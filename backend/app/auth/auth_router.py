# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Authentication router handling staff user login with bcrypt and account lockout protection.

import bcrypt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from backend.app.config import settings
from backend.app.db import get_database
from backend.app.complaint_management.schemas import StaffLoginPayload, StaffLoginResponse, StaffUserResponse
from backend.app.auth.jwt_auth import create_staff_token, require_roles

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=StaffLoginResponse)
async def staff_login(data: StaffLoginPayload):
    """Authenticates staff user with bcrypt password comparison and account lockout.

    Lockout Policy:
    - Locks account for LOGIN_LOCK_MINUTES (15m) after LOGIN_MAX_FAILURES (5) failed attempts.
    - Generic error message used for timing safety.
    """
    db = get_database()
    username_clean = data.username.strip().lower()

    user_doc = await db.staff_users.find_one({"username": username_clean})
    generic_error = "Invalid username or password"

    if not user_doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=generic_error)

    if not user_doc.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff account is deactivated")

    # Check lock status
    now_dt = datetime.utcnow()
    locked_until = user_doc.get("locked_until")
    if locked_until and locked_until > now_dt:
        lock_mins = getattr(settings, "LOGIN_LOCK_MINUTES", 15)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account is temporarily locked due to multiple failed login attempts. Try again later."
        )

    # Verify password with bcrypt
    password_bytes = data.password.encode("utf-8")
    hash_bytes = user_doc.get("password_hash", "").encode("utf-8")

    password_ok = False
    try:
        password_ok = bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        password_ok = False

    if not password_ok:
        # Increment failed login count
        max_failures = getattr(settings, "LOGIN_MAX_FAILURES", 5)
        failed_cnt = user_doc.get("failed_login_count", 0) + 1
        update_doc = {"failed_login_count": failed_cnt}

        if failed_cnt >= max_failures:
            lock_mins = getattr(settings, "LOGIN_LOCK_MINUTES", 15)
            update_doc["locked_until"] = now_dt + timedelta(minutes=lock_mins)

        await db.staff_users.update_one({"_id": user_doc["_id"]}, {"$set": update_doc})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=generic_error)

    # Success: reset failed attempts
    await db.staff_users.update_one(
        {"_id": user_doc["_id"]},
        {"$set": {"failed_login_count": 0, "locked_until": None}}
    )

    staff_id = str(user_doc["_id"])
    role = user_doc["role"]
    token = create_staff_token(staff_id=staff_id, username=user_doc["username"], role=role)
    expires_at = now_dt + timedelta(hours=settings.JWT_EXPIRE_HOURS)

    return StaffLoginResponse(
        token=token,
        role=role,
        full_name=user_doc.get("full_name", username_clean),
        expires_at=expires_at
    )


@router.get("/me", response_model=StaffUserResponse)
async def get_current_staff(user_doc: dict = Depends(require_roles("ADMIN", "MANAGER", "TECHNICIAN"))):
    """Returns currently authenticated staff user profile."""
    return StaffUserResponse(
        _id=str(user_doc["_id"]),
        username=user_doc["username"],
        full_name=user_doc["full_name"],
        role=user_doc["role"],
        email=user_doc["email"],
        mobile=user_doc["mobile"],
        is_active=user_doc.get("is_active", True),
        notify_on_new_complaint=user_doc.get("notify_on_new_complaint", False),
        technician_profile=user_doc.get("technician_profile"),
        created_at=user_doc.get("created_at", datetime.utcnow())
    )
