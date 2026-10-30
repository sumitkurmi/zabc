# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Public complaint registration with email-OTP verification and rate-limiting.

import re
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, status
from backend.app.config import settings
from backend.app.db import get_database
from backend.app.complaint_management.schemas import (
    OTPRequestPayload,
    OTPRequestResponse,
    OTPVerifyPayload,
    OTPVerifyResponse,
    OTPResendPayload
)
from backend.app.routers.public_complaints import generate_reference_number
from backend.app.complaint_management.services.ticket_service import generate_ticket_id
from backend.app.complaint_management.services.status_service import StatusService
from backend.app.complaint_management.models import ComplaintStatus
from backend.app.notifications.service import notify
from backend.app import events

router = APIRouter(prefix="/complaints/otp", tags=["complaints-otp"])


def hash_otp(otp: str) -> str:
    """Computes HMAC-SHA256 hash of OTP code using configured OTP_SECRET."""
    secret = getattr(settings, "OTP_SECRET", "mnnit-otp-secret-key-32bytes-min").encode("utf-8")
    return hmac.new(secret, otp.encode("utf-8"), hashlib.sha256).hexdigest()


def validate_email_domain(email: str) -> str:
    """Validates student email against allowed college domain.

    Rules:
    - Lowercase and trim.
    - Matches ^[a-z0-9][a-z0-9._-]{0,63}@<ALLOWED_EMAIL_DOMAIN>$
    - Exactly one @, no subdomains.
    """
    clean_email = email.strip().lower()
    allowed_domain = (getattr(settings, "ALLOWED_EMAIL_DOMAIN", None) or "mnnit.ac.in").strip().lower()

    pattern = rf"^[a-z0-9][a-z0-9._-]{{0,63}}@{re.escape(allowed_domain)}$"
    if not re.match(pattern, clean_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email must be a valid '@{allowed_domain}' address without subdomains."
        )
    return clean_email


@router.post("/request", response_model=OTPRequestResponse)
async def request_otp(data: OTPRequestPayload, request: Request):
    """Submits complaint details and dispatches a 6-digit OTP to the student's college email."""
    if data.honeypot:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Spam submission detected")

    clean_email = validate_email_domain(data.email)
    db = get_database()

    # Per-email rate limit: max OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR (5) requests per hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    max_hourly_reqs = getattr(settings, "OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR", 5)
    req_count = await db.otp_request_log.count_documents({"email": clean_email, "at": {"$gte": one_hour_ago}})

    if req_count >= max_hourly_reqs:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests for this email address. Please try again in an hour."
        )

    # Log request
    await db.otp_request_log.insert_one({"email": clean_email, "at": datetime.utcnow()})

    # Generate 6-digit numeric OTP
    otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    otp_hashed = hash_otp(otp_code)

    otp_expire_mins = getattr(settings, "OTP_EXPIRE_MINUTES", 10)
    cooldown_secs = getattr(settings, "OTP_RESEND_SECONDS", 60)
    now_dt = datetime.utcnow()
    expires_dt = now_dt + timedelta(minutes=otp_expire_mins)

    pending_doc = {
        "name": data.name,
        "email": clean_email,
        "mobile": data.mobile,
        "location": data.location,
        "address_room": data.address_room,
        "preferred_from": data.preferred_from,
        "preferred_to": data.preferred_to,
        "problem_type": data.problem_type,
        "additional_comment": data.additional_comment or "",
        "chat_id": data.chat_id,
        "filled_by_ai": data.filled_by_ai,
        "otp_hash": otp_hashed,
        "otp_expires_at": expires_dt,
        "otp_attempts": 0,
        "resend_count": 0,
        "last_sent_at": now_dt,
        "ip": request.client.host if request.client else "unknown",
        "created_at": now_dt,
        "expires_at": expires_dt
    }

    res = await db.pending_complaints.insert_one(pending_doc)
    pending_id = str(res.inserted_id)

    # Dispatch OTP email directly
    context = {
        "name": data.name,
        "otp_code": otp_code,
        "to_role": "STUDENT"
    }

    email_backend = getattr(settings, "EMAIL_BACKEND", "console").lower()
    app_env = getattr(settings, "APP_ENV", "development").lower()

    if email_backend == "console" and app_env == "development":
        print(f"\n[DEVELOPMENT OTP CONSOLE] Student Email: {clean_email} | OTP Code: {otp_code}\n")

    await notify("otp_request", "PENDING", [clean_email], context)

    return OTPRequestResponse(
        pending_id=pending_id,
        message=f"OTP sent to {clean_email}. Please verify.",
        expires_in_seconds=otp_expire_mins * 60,
        resend_cooldown_seconds=cooldown_secs
    )


@router.post("/verify", response_model=OTPVerifyResponse)
async def verify_otp(data: OTPVerifyPayload):
    """Verifies 6-digit OTP code using constant-time comparison and creates complaint ticket on success."""
    db = get_database()
    pending_doc = await db.pending_complaints.find_one({"_id": data.pending_id})

    if not pending_doc:
        try:
            from bson import ObjectId
            pending_doc = await db.pending_complaints.find_one({"_id": ObjectId(data.pending_id)})
        except Exception:
            pass

    if not pending_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pending request expired or invalid. Please request a new OTP."
        )

    # Check expiration
    if datetime.utcnow() > pending_doc["otp_expires_at"]:
        await db.pending_complaints.delete_one({"_id": pending_doc["_id"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code has expired. Please request a new OTP."
        )

    # Check wrong attempts limit
    max_attempts = getattr(settings, "OTP_MAX_ATTEMPTS", 5)
    attempts = pending_doc.get("otp_attempts", 0) + 1

    if attempts > max_attempts:
        await db.pending_complaints.delete_one({"_id": pending_doc["_id"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP verification attempts exceeded. Please start again."
        )

    # Constant-time comparison
    expected_hash = pending_doc["otp_hash"]
    submitted_hash = hash_otp(data.otp.strip())

    if not hmac.compare_digest(expected_hash, submitted_hash):
        await db.pending_complaints.update_one(
            {"_id": pending_doc["_id"]},
            {"$set": {"otp_attempts": attempts}}
        )
        remaining = max(0, max_attempts - attempts)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP code. {remaining} attempt(s) remaining."
        )

    # Success: Generate 12-digit ticket_id and Part 1 ref_no
    ticket_id = await generate_ticket_id()
    ref_no = await generate_reference_number()
    now_dt = datetime.utcnow()

    complaint_doc = {
        "ticket_id": ticket_id,
        "ref_no": ref_no,
        "name": pending_doc["name"],
        "email": pending_doc["email"],
        "mobile": pending_doc["mobile"],
        "location": pending_doc["location"],
        "address_room": pending_doc["address_room"],
        "preferred_from": pending_doc["preferred_from"],
        "preferred_to": pending_doc["preferred_to"],
        "problem_type": pending_doc["problem_type"],
        "additional_comment": pending_doc["additional_comment"],
        "chat_id": pending_doc.get("chat_id"),
        "filled_by_ai": pending_doc.get("filled_by_ai", False),
        "status": ComplaintStatus.SUBMITTED.value,
        "assigned_technician_id": None,
        "assigned_at": None,
        "assignment_count": 0,
        "diagnosis": None,
        "solution": None,
        "resolved_at": None,
        "items_used": [],
        "asset_actions": [],
        "previous_attempts": [],
        "reopen_count": 0,
        "confirmation_requested_at": None,
        "closed_at": None,
        "closed_by": None,
        "created_at": now_dt,
        "updated_at": now_dt
    }

    # Delete pending request and insert complaint as SUBMITTED
    await db.pending_complaints.delete_one({"_id": pending_doc["_id"]})
    await db.complaints.insert_one(complaint_doc)

    actor = {"type": "SYSTEM", "id": "system_registration", "role": "SYSTEM", "name": "Registration Engine"}

    # Emit complaint_registered event
    await events.emit("complaint_registered", {
        "ticket_id": ticket_id,
        "complaint": complaint_doc,
        "actor": actor
    })

    # Delegate classification & advancement to classification_service
    from backend.app.complaint_management.services.classification_service import classify_and_advance
    await classify_and_advance(ticket_id)

    return OTPVerifyResponse(
        ticket_id=ticket_id,
        message="Complaint registered and verified successfully."
    )


@router.post("/resend", response_model=OTPRequestResponse)
async def resend_otp(data: OTPResendPayload):
    """Resends a fresh OTP after 60-second cooldown."""
    db = get_database()
    pending_doc = await db.pending_complaints.find_one({"_id": data.pending_id})

    if not pending_doc:
        try:
            from bson import ObjectId
            pending_doc = await db.pending_complaints.find_one({"_id": ObjectId(data.pending_id)})
        except Exception:
            pass

    if not pending_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pending request not found or expired. Please start again."
        )

    now_dt = datetime.utcnow()
    last_sent = pending_doc.get("last_sent_at", now_dt)
    cooldown_secs = getattr(settings, "OTP_RESEND_SECONDS", 60)

    if (now_dt - last_sent).total_seconds() < cooldown_secs:
        remaining_secs = int(cooldown_secs - (now_dt - last_sent).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining_secs} seconds before requesting a new OTP."
        )

    max_resends = getattr(settings, "OTP_MAX_RESENDS", 3)
    resend_cnt = pending_doc.get("resend_count", 0) + 1

    if resend_cnt > max_resends:
        await db.pending_complaints.delete_one({"_id": pending_doc["_id"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP resend limit reached. Please start again."
        )

    # Generate new OTP
    otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    otp_hashed = hash_otp(otp_code)
    otp_expire_mins = getattr(settings, "OTP_EXPIRE_MINUTES", 10)
    expires_dt = now_dt + timedelta(minutes=otp_expire_mins)

    await db.pending_complaints.update_one(
        {"_id": pending_doc["_id"]},
        {
            "$set": {
                "otp_hash": otp_hashed,
                "otp_expires_at": expires_dt,
                "otp_attempts": 0,
                "resend_count": resend_cnt,
                "last_sent_at": now_dt,
                "expires_at": expires_dt
            }
        }
    )

    clean_email = pending_doc["email"]
    email_backend = getattr(settings, "EMAIL_BACKEND", "console").lower()
    app_env = getattr(settings, "APP_ENV", "development").lower()

    if email_backend == "console" and app_env == "development":
        print(f"\n[DEVELOPMENT OTP RESEND CONSOLE] Student Email: {clean_email} | OTP Code: {otp_code}\n")

    context = {
        "name": pending_doc["name"],
        "otp_code": otp_code,
        "to_role": "STUDENT"
    }
    await notify("otp_request", "PENDING", [clean_email], context)

    return OTPRequestResponse(
        pending_id=str(pending_doc["_id"]),
        message=f"Fresh OTP sent to {clean_email}.",
        expires_in_seconds=otp_expire_mins * 60,
        resend_cooldown_seconds=cooldown_secs
    )
