# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Authentication dependencies and JWT token verification module supporting staff roles and Part 1 compatibility.

from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from bson import ObjectId
from backend.app.config import settings
from backend.app.db import get_database

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates signed JWT token containing admin claims and expiration time."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> str:
    """Decodes and validates JWT token string, returning sub claim if valid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """FastAPI dependency to validate JWT bearer token or cookie on protected admin endpoints.

    Reloads staff user from DB to verify active status and ADMIN role.
    """
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("admin_token") or request.cookies.get("staff_token")

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
        role: str = payload.get("role", "ADMIN")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # If staff_id is present, verify in staff_users DB
    if staff_id:
        db = get_database()
        user_doc = await db.staff_users.find_one({"_id": staff_id})
        if not user_doc:
            try:
                user_doc = await db.staff_users.find_one({"_id": ObjectId(staff_id)})
            except Exception:
                pass

        if user_doc:
            if not user_doc.get("is_active", True):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff account is deactivated")
            if user_doc.get("role") != "ADMIN":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
            return user_doc["username"]

    return verify_token(token)
