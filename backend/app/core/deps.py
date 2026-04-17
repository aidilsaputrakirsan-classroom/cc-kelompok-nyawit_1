"""
FastAPI dependencies for authentication and role-based access control.

Authentication flow:
    1. HTTPBearer extracts the token from the Authorization header
    2. decode_access_token verifies signature, expiration, and token type
    3. Token jti is checked against the blacklist (revoked tokens)
    4. User is fetched from the database to confirm they still exist
    5. Role is checked from the DB object (not from the JWT payload)
"""

from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User

# Bearer token scheme — expects "Authorization: Bearer <token>"
_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the JWT access token from the Authorization header and
    return the corresponding User ORM object.

    Raises 401 if the token is missing, invalid, expired, revoked,
    or the user no longer exists in the database.
    """
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kedaluwarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Check token blacklist (revocation) ────────────────────────
    jti: str | None = payload.get("jti")
    if jti:
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sudah di-revoke, silakan login kembali",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ── Fetch user from database ──────────────────────────────────
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(roles: List[str]):
    """
    Factory that returns a dependency which checks whether the
    authenticated user has one of the allowed roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(["admin"]))])
        async def admin_endpoint(...): ...

    Or inject the user directly:
        async def endpoint(user: User = Depends(require_role(["admin"]))): ...
    """

    async def _role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        # Extract role value safely (handles both Enum and string)
        user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Role yang diizinkan: {', '.join(roles)}",
            )
        return current_user

    return _role_checker
