# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Public token-based student actions for confirming resolution status and rating technician service quality.

import secrets
import hashlib
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from backend.app.config import settings
from backend.app.db import get_database
from backend.app.complaint_management.schemas import (
    StudentConfirmPayload,
    StudentRatePayload,
    StudentTokenInfoResponse
)
from backend.app.complaint_management.models import ComplaintStatus, ClosedBy, ActionTokenPurpose
from backend.app.complaint_management.services.status_service import StatusService
from backend.app import events

router = APIRouter(prefix="/student-actions", tags=["student-actions"])


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hash string of a raw token."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


async def create_action_token(ticket_id: str, purpose: ActionTokenPurpose) -> str:
    """Generates a random 32-byte URL-safe token, stores SHA-256 hash in MongoDB, and returns raw token string."""
    db = get_database()
    raw_token = secrets.token_urlsafe(32)
    token_hashed = hash_token(raw_token)

    expiry_days = getattr(settings, "ACTION_TOKEN_EXPIRY_DAYS", 14)
    expires_dt = datetime.utcnow() + timedelta(days=expiry_days)

    token_doc = {
        "token_hash": token_hashed,
        "ticket_id": ticket_id,
        "purpose": purpose.value,
        "expires_at": expires_dt,
        "used_at": None,
        "created_at": datetime.utcnow()
    }
    await db.action_tokens.insert_one(token_doc)
    return raw_token


@router.get("/{token}", response_model=StudentTokenInfoResponse)
async def get_token_info(token: str):
    """Fetches action token status and complaint solution preview for public confirmation/rating pages."""
    db = get_database()
    token_hashed = hash_token(token)

    token_doc = await db.action_tokens.find_one({"token_hash": token_hashed})
    if not token_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid action link")

    ticket_id = token_doc["ticket_id"]
    complaint = await db.complaints.find_one({"ticket_id": ticket_id})
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated complaint not found")

    tech_name = None
    tech_id = complaint.get("assigned_technician_id")
    if tech_id:
        tech = await db.staff_users.find_one({"_id": tech_id})
        if tech:
            tech_name = tech.get("full_name")

    now_dt = datetime.utcnow()
    is_expired = now_dt > token_doc["expires_at"]
    is_used = token_doc.get("used_at") is not None
    is_valid = not is_expired and not is_used

    return StudentTokenInfoResponse(
        ticket_id=ticket_id,
        purpose=ActionTokenPurpose(token_doc["purpose"]),
        solution=complaint.get("solution"),
        technician_name=tech_name,
        status=complaint.get("status"),
        is_valid=is_valid,
        is_expired=is_expired,
        is_used=is_used
    )


@router.post("/{token}/confirm")
async def confirm_resolution(token: str, payload: StudentConfirmPayload):
    """Processes student confirmation response (solved vs not solved/reopened)."""
    db = get_database()
    token_hashed = hash_token(token)

    token_doc = await db.action_tokens.find_one({"token_hash": token_hashed, "purpose": ActionTokenPurpose.CONFIRM.value})
    if not token_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid confirmation token")

    if token_doc.get("used_at"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This confirmation link has already been used.")

    if datetime.utcnow() > token_doc["expires_at"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This confirmation link has expired.")

    ticket_id = token_doc["ticket_id"]
    complaint = await db.complaints.find_one({"ticket_id": ticket_id})

    if not complaint or complaint.get("status") != ComplaintStatus.STUDENT_CONFIRMATION.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint is not currently awaiting student confirmation."
        )

    # Mark token used
    now_dt = datetime.utcnow()
    await db.action_tokens.update_one({"_id": token_doc["_id"]}, {"$set": {"used_at": now_dt}})

    student_actor = {
        "type": "STUDENT",
        "id": complaint.get("email"),
        "role": "STUDENT",
        "name": complaint.get("name", "Student")
    }

    if payload.solved:
        # Mark closed by STUDENT
        await db.complaints.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"closed_by": ClosedBy.STUDENT.value, "closed_at": now_dt}}
        )

        updated_complaint = await StatusService.change_status(
            ticket_id=ticket_id,
            to_status=ComplaintStatus.CLOSED.value,
            actor=student_actor,
            note="Student confirmed resolution"
        )

        # Generate RATE token for rating email
        rate_token = await create_action_token(ticket_id, ActionTokenPurpose.RATE)

        # Dispatch closed & rate email
        await events.emit("complaint_closed", {
            "ticket_id": ticket_id,
            "complaint": updated_complaint,
            "rate_token": rate_token,
            "actor": student_actor
        })

        return {"message": "Thank you for confirming. Your ticket has been closed.", "ticket_id": ticket_id}

    else:
        # Student clicked 'Not solved' -> Reopen
        prev_attempt = {
            "diagnosis": complaint.get("diagnosis", ""),
            "solution": complaint.get("solution", ""),
            "items_used": complaint.get("items_used", []),
            "asset_actions": complaint.get("asset_actions", []),
            "resolved_at": complaint.get("resolved_at", now_dt),
            "reopened_at": now_dt
        }

        reopen_cnt = complaint.get("reopen_count", 0) + 1

        # Check if assigned technician is still active
        tech_id = complaint.get("assigned_technician_id")
        target_status = ComplaintStatus.ASSIGNED.value

        if tech_id:
            tech = await db.staff_users.find_one({"_id": tech_id, "is_active": True})
            if not tech:
                # Tech is no longer active -> reset to CLASSIFIED unassigned
                await db.complaints.update_one(
                    {"ticket_id": ticket_id},
                    {"$set": {"assigned_technician_id": None, "assigned_at": None}}
                )
                target_status = ComplaintStatus.CLASSIFIED.value

        await db.complaints.update_one(
            {"ticket_id": ticket_id},
            {
                "$push": {"previous_attempts": prev_attempt},
                "$set": {
                    "reopen_count": reopen_cnt,
                    "diagnosis": None,
                    "solution": None,
                    "items_used": [],
                    "asset_actions": []
                }
            }
        )

        updated_complaint = await StatusService.change_status(
            ticket_id=ticket_id,
            to_status=target_status,
            actor=student_actor,
            note=f"Student marked issue not solved: {payload.comment or 'Reopened'}"
        )

        await events.emit("complaint_reopened", {
            "ticket_id": ticket_id,
            "complaint": updated_complaint,
            "comment": payload.comment,
            "actor": student_actor
        })

        return {"message": "Your complaint has been reopened and returned to IT support.", "ticket_id": ticket_id}


@router.post("/{token}/rate")
async def rate_service(token: str, payload: StudentRatePayload):
    """Submits student 1-5 star service rating and optional feedback."""
    db = get_database()
    token_hashed = hash_token(token)

    token_doc = await db.action_tokens.find_one({"token_hash": token_hashed, "purpose": ActionTokenPurpose.RATE.value})
    if not token_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid rating token")

    if token_doc.get("used_at"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This rating link has already been used.")

    if datetime.utcnow() > token_doc["expires_at"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This rating link has expired.")

    ticket_id = token_doc["ticket_id"]
    complaint = await db.complaints.find_one({"ticket_id": ticket_id})

    if not complaint or complaint.get("status") != ComplaintStatus.CLOSED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ratings can only be submitted for closed complaints.")

    tech_id = complaint.get("assigned_technician_id")
    if not tech_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No technician was assigned when closing this complaint.")

    # Check unique rating constraint
    existing_rating = await db.ratings.find_one({"ticket_id": ticket_id})
    if existing_rating:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A rating has already been submitted for this complaint.")

    now_dt = datetime.utcnow()
    rating_doc = {
        "ticket_id": ticket_id,
        "technician_id": tech_id,
        "rating": payload.rating,
        "feedback": payload.feedback or "",
        "created_at": now_dt
    }

    await db.ratings.insert_one(rating_doc)
    await db.action_tokens.update_one({"_id": token_doc["_id"]}, {"$set": {"used_at": now_dt}})

    await events.emit("rating_received", {
        "ticket_id": ticket_id,
        "technician_id": tech_id,
        "rating": payload.rating,
        "feedback": payload.feedback
    })

    return {"message": "Thank you for rating our service quality!", "ticket_id": ticket_id}
