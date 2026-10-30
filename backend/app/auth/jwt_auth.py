# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Staff user authentication dependency, JWT token creation, and database-reloaded role guards.

from datetime import datetime, timedelta
from typing import List, Optional, Callable
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from bson import ObjectId
from backend.app.config import settings
from backend.app.db import get_database

security = HTTPBearer(auto_error=False)


def create_staff_token(staff_id: str, username: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generates signed JWT token string containing staff claims and expiration."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)

    payload = {
        "sub": username,
        "staff_id": staff_id,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def require_roles(*allowed_roles: str):
    """FastAPI dependency factory enforcing staff role permissions and checking DB activity status.

    Reloads staff user record from MongoDB on every request to instantly block deactivated staff.

    Args:
        *allowed_roles: Allowed StaffRole enum strings (e.g., 'ADMIN', 'MANAGER', 'TECHNICIAN').
    """
    async def _role_guard(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        token = None
        if credentials:
            token = credentials.credentials
        else:
            token = request.cookies.get("staff_token") or request.cookies.get("admin_token")

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            staff_id: str = payload.get("staff_id")
            username: str = payload.get("sub")
            if not staff_id or not username:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.PyJWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

        # Reload user from DB on every request to verify activity status
        db = get_database()
        user_doc = await db.staff_users.find_one({"_id": staff_id})
        if not user_doc:
            try:
                user_doc = await db.staff_users.find_one({"_id": ObjectId(staff_id)})
            except Exception:
                pass

        if not user_doc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff account no longer exists")

        if not user_doc.get("is_active", True):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff account is deactivated")

        user_role = user_doc.get("role")
        if allowed_roles and user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: required role in {allowed_roles}, got '{user_role}'"
            )

        return user_doc

    return _role_guard
