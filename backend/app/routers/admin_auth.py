"""Admin authentication API router.

Specification Section 9.1 & Section 10.
Handles admin login using username and bcrypt password hash verification,
returning short-lived JWT access tokens and setting HTTP-only cookie.
"""

from datetime import timedelta
import bcrypt
from fastapi import APIRouter, HTTPException, Request, Response, status
from backend.app.config import settings
from backend.app.deps import create_access_token
from backend.app.schemas import AdminLoginRequest, AdminLoginResponse

router = APIRouter(prefix="/admin", tags=["admin-auth"])


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(data: AdminLoginRequest, request: Request, response: Response):
    """Authenticates admin credentials, returns JWT token, and sets admin_token cookie."""
    # Verify username
    if data.username != settings.ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Verify bcrypt password hash
    plain_pw_bytes = data.password.encode("utf-8")
    hash_pw_bytes = settings.ADMIN_PASSWORD_HASH.encode("utf-8")

    if not bcrypt.checkpw(plain_pw_bytes, hash_pw_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Generate JWT access token
    expires_delta = timedelta(hours=settings.JWT_EXPIRE_HOURS)
    token = create_access_token(data={"sub": settings.ADMIN_USERNAME}, expires_delta=expires_delta)
    expires_at_str = str(expires_delta.total_seconds())

    # Set HTTP cookie for server-side page redirect checks
    response.set_cookie(
        key="admin_token",
        value=token,
        max_age=int(expires_delta.total_seconds()),
        httponly=True,
        samesite="lax",
        path="/"
    )

    return AdminLoginResponse(
        token=token,
        expires_at=expires_at_str
    )


@router.post("/logout")
async def admin_logout(response: Response):
    """Clears admin authentication token cookie."""
    response.delete_cookie(key="admin_token", path="/")
    return {"message": "Logged out successfully"}
