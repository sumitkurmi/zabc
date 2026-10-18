"""Authentication dependency and JWT token verification module.

Provides FastAPI dependency functions to protect admin endpoints using Bearer JWT tokens.

Token lifecycle:
- Token generated upon POST /api/admin/login with expiration (default 8h)
- Token passed via HTTP Header: `Authorization: Bearer <token>`
- Decoded using PyJWT with constant JWT_SECRET configured in settings
"""

from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from backend.app.config import settings

# HTTP Bearer authentication scheme wrapper
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a signed JWT token containing admin claims and expiration time.

    Args:
        data: Dict containing claims (e.g. {'sub': 'admin'}).
        expires_delta: Optional custom token duration.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """FastAPI dependency to validate JWT bearer token on protected admin endpoints.

    Args:
        credentials: Bearer token supplied in Authorization header.

    Returns:
        Subject username string extracted from decoded token.

    Raises:
        HTTPException 401 if token is missing, invalid, or expired.
    """
    token = credentials.credentials
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
