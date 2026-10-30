# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Admin staff user management router with bcrypt hashing, deactivation guards, and audit logging.

import bcrypt
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.db import get_database
from backend.app.auth.jwt_auth import require_roles
from backend.app.complaint_management.models import StaffRole, ComplaintStatus, TechnicianAvailability
from backend.app.complaint_management.schemas import (
    StaffCreatePayload,
    StaffUpdatePayload,
    PasswordResetPayload,
    StaffUserResponse
)

router = APIRouter(prefix="/admin", tags=["admin-staff"])


async def log_admin_audit(action: str, actor_id: str, details: dict):
    """Appends an administrative action log to admin_audit_log collection."""
    db = get_database()
    audit_doc = {
        "action": action,
        "actor_id": actor_id,
        "details": details,
        "at": datetime.utcnow()
    }
    await db.admin_audit_log.insert_one(audit_doc)


@router.get("/staff", response_model=List[StaffUserResponse])
async def list_staff_users(admin_user: dict = Depends(require_roles("ADMIN"))):
    """Lists all staff users (active and soft-deactivated)."""
    db = get_database()
    cursor = db.staff_users.find({}).sort("created_at", -1)

    staff_list = []
    async for s in cursor:
        staff_list.append(
            StaffUserResponse(
                _id=str(s["_id"]),
                username=s["username"],
                full_name=s["full_name"],
                role=s["role"],
                email=s["email"],
                mobile=s["mobile"],
                is_active=s.get("is_active", True),
                notify_on_new_complaint=s.get("notify_on_new_complaint", False),
                technician_profile=s.get("technician_profile"),
                created_at=s.get("created_at", datetime.utcnow())
            )
        )

    return staff_list


@router.post("/staff", response_model=StaffUserResponse, status_code=status.HTTP_201_CREATED)
async def create_staff_user(payload: StaffCreatePayload, admin_user: dict = Depends(require_roles("ADMIN"))):
    """Creates a new MANAGER or TECHNICIAN staff account. Admins cannot create other admins."""
    if payload.role == StaffRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot create other Admin accounts."
        )

    db = get_database()
    clean_username = payload.username.strip().lower()

    existing = await db.staff_users.find_one({"username": clean_username})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{clean_username}' already exists."
        )

    # Hash password with bcrypt
    hashed_pwd = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    now_dt = datetime.utcnow()
    admin_id = str(admin_user["_id"])

    doc = {
        "username": clean_username,
        "password_hash": hashed_pwd,
        "full_name": payload.full_name.strip(),
        "role": payload.role.value,
        "email": payload.email.strip().lower(),
        "mobile": payload.mobile.strip(),
        "is_active": True,
        "failed_login_count": 0,
        "locked_until": None,
        "notify_on_new_complaint": False,
        "created_by": admin_id,
        "created_at": now_dt,
        "deactivated_at": None,
        "technician_profile": None
    }

    if payload.role == StaffRole.TECHNICIAN:
        doc["technician_profile"] = {
            "availability": TechnicianAvailability.UNAVAILABLE.value,
            "zones": payload.zones or [],
            "categories": payload.categories or ["LAN_PROBLEM", "IP_ADDRESS_ISSUE", "PROXY_ISSUE", "LAN_PORT_BROKEN", "WIFI_PROBLEM"],
            "max_open_complaints": payload.max_open_complaints
        }

    res = await db.staff_users.insert_one(doc)
    doc_id = str(res.inserted_id)

    await log_admin_audit("CREATE_STAFF", admin_id, {"staff_id": doc_id, "username": clean_username, "role": payload.role.value})

    return StaffUserResponse(
        _id=doc_id,
        username=clean_username,
        full_name=doc["full_name"],
        role=doc["role"],
        email=doc["email"],
        mobile=doc["mobile"],
        is_active=True,
        notify_on_new_complaint=False,
        technician_profile=doc["technician_profile"],
        created_at=now_dt
    )


@router.put("/staff/{id}", response_model=StaffUserResponse)
async def update_staff_user(id: str, payload: StaffUpdatePayload, admin_user: dict = Depends(require_roles("ADMIN"))):
    """Updates staff user profile details and technician zones."""
    db = get_database()
    staff_doc = await db.staff_users.find_one({"_id": id})
    if not staff_doc:
        try:
            staff_doc = await db.staff_users.find_one({"_id": ObjectId(id)})
        except Exception:
            pass

    if not staff_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")

    update_fields = {}
    if payload.full_name is not None:
        update_fields["full_name"] = payload.full_name.strip()
    if payload.email is not None:
        update_fields["email"] = payload.email.strip().lower()
    if payload.mobile is not None:
        update_fields["mobile"] = payload.mobile.strip()

    if staff_doc.get("role") == StaffRole.TECHNICIAN.value:
        if payload.zones is not None:
            update_fields["technician_profile.zones"] = payload.zones
        if payload.categories is not None:
            update_fields["technician_profile.categories"] = payload.categories
        if payload.max_open_complaints is not None:
            update_fields["technician_profile.max_open_complaints"] = payload.max_open_complaints

    if update_fields:
        await db.staff_users.update_one({"_id": staff_doc["_id"]}, {"$set": update_fields})

    updated = await db.staff_users.find_one({"_id": staff_doc["_id"]})
    admin_id = str(admin_user["_id"])
    await log_admin_audit("UPDATE_STAFF", admin_id, {"staff_id": str(staff_doc["_id"]), "updates": update_fields})

    return StaffUserResponse(
        _id=str(updated["_id"]),
        username=updated["username"],
        full_name=updated["full_name"],
        role=updated["role"],
        email=updated["email"],
        mobile=updated["mobile"],
        is_active=updated.get("is_active", True),
        notify_on_new_complaint=updated.get("notify_on_new_complaint", False),
        technician_profile=updated.get("technician_profile"),
        created_at=updated.get("created_at", datetime.utcnow())
    )


@router.post("/staff/{id}/reset-password")
async def reset_staff_password(id: str, payload: PasswordResetPayload, admin_user: dict = Depends(require_roles("ADMIN"))):
    """Resets staff user password."""
    db = get_database()
    staff_doc = await db.staff_users.find_one({"_id": id})
    if not staff_doc:
        try:
            staff_doc = await db.staff_users.find_one({"_id": ObjectId(id)})
        except Exception:
            pass

    if not staff_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")

    hashed_pwd = bcrypt.hashpw(payload.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    await db.staff_users.update_one(
        {"_id": staff_doc["_id"]},
        {"$set": {"password_hash": hashed_pwd, "failed_login_count": 0, "locked_until": None}}
    )

    admin_id = str(admin_user["_id"])
    await log_admin_audit("RESET_STAFF_PASSWORD", admin_id, {"staff_id": str(staff_doc["_id"])})

    return {"message": f"Password reset successfully for '{staff_doc['username']}'."}


@router.post("/staff/{id}/deactivate")
async def deactivate_staff_user(id: str, admin_user: dict = Depends(require_roles("ADMIN"))):
    """Soft-deactivates staff user. Blocks deactivation if technician has open assigned complaints."""
    db = get_database()
    staff_doc = await db.staff_users.find_one({"_id": id})
    if not staff_doc:
        try:
            staff_doc = await db.staff_users.find_one({"_id": ObjectId(id)})
        except Exception:
            pass

    if not staff_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")

    staff_id = str(staff_doc["_id"])
    admin_id = str(admin_user["_id"])

    if staff_id == admin_id or staff_doc.get("role") == StaffRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot deactivate Admin accounts.")

    if staff_doc.get("role") == StaffRole.TECHNICIAN.value:
        open_cursor = db.complaints.find({
            "assigned_technician_id": staff_id,
            "status": {"$in": [ComplaintStatus.ASSIGNED.value, ComplaintStatus.DIAGNOSED.value]}
        })
        open_tickets = [c["ticket_id"] async for c in open_cursor]

        if open_tickets:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot deactivate technician with active assigned complaints. Reassign these tickets first: {open_tickets}"
            )

    now_dt = datetime.utcnow()
    await db.staff_users.update_one(
        {"_id": staff_doc["_id"]},
        {
            "$set": {
                "is_active": False,
                "deactivated_at": now_dt,
                "technician_profile.availability": TechnicianAvailability.UNAVAILABLE.value
            }
        }
    )

    await log_admin_audit("DEACTIVATE_STAFF", admin_id, {"staff_id": staff_id, "username": staff_doc["username"]})
    return {"message": f"Staff user '{staff_doc['username']}' deactivated successfully."}


@router.post("/staff/{id}/reactivate")
async def reactivate_staff_user(id: str, admin_user: dict = Depends(require_roles("ADMIN"))):
    """Reactivates a soft-deactivated staff account."""
    db = get_database()
    staff_doc = await db.staff_users.find_one({"_id": id})
    if not staff_doc:
        try:
            staff_doc = await db.staff_users.find_one({"_id": ObjectId(id)})
        except Exception:
            pass

    if not staff_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")

    staff_id = str(staff_doc["_id"])
    admin_id = str(admin_user["_id"])

    await db.staff_users.update_one(
        {"_id": staff_doc["_id"]},
        {"$set": {"is_active": True, "deactivated_at": None}}
    )

    await log_admin_audit("REACTIVATE_STAFF", admin_id, {"staff_id": staff_id, "username": staff_doc["username"]})
    return {"message": f"Staff user '{staff_doc['username']}' reactivated successfully."}


# Admin settings: toggle notify_on_new_complaint
@router.get("/me/settings")
async def get_admin_settings(admin_user: dict = Depends(require_roles("ADMIN"))):
    """Returns admin personal settings."""
    return {"notify_on_new_complaint": admin_user.get("notify_on_new_complaint", False)}


@router.put("/me/settings")
async def update_admin_settings(payload: dict, admin_user: dict = Depends(require_roles("ADMIN"))):
    """Updates admin notify_on_new_complaint setting."""
    db = get_database()
    notify_flag = bool(payload.get("notify_on_new_complaint", False))

    await db.staff_users.update_one(
        {"_id": admin_user["_id"]},
        {"$set": {"notify_on_new_complaint": notify_flag}}
    )

    return {"message": "Admin settings updated successfully", "notify_on_new_complaint": notify_flag}


@router.get("/agent/status")
async def get_admin_agent_status(admin_user: dict = Depends(require_roles("ADMIN", "MANAGER"))):
    """Returns agent configuration status, pending/failed job counts, and last successful run timestamp."""
    db = get_database()
    from backend.app.config import settings

    pending_jobs = await db.agent_jobs.count_documents({"status": "PENDING"})
    failed_jobs = await db.agent_jobs.count_documents({"status": "FAILED"})

    last_run = await db.agent_runs.find_one({"success": True}, sort=[("started_at", -1)])
    last_run_at = last_run.get("started_at") if last_run else None

    return {
        "enabled": getattr(settings, "AGENT_ENABLED", True),
        "mode": getattr(settings, "AGENT_ASSIGNMENT_MODE", "auto"),
        "pending_jobs": pending_jobs,
        "failed_jobs": failed_jobs,
        "last_successful_run": last_run_at
    }
