"""
Authentication router — register & login endpoints.

POST /api/v1/auth/register  → admin-only, create new user
POST /api/v1/auth/login     → return JWT access token
GET  /api/v1/auth/me        → return current authenticated user
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.user import UserCreate

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── POST /register ────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register user baru (admin only)",
)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["admin"])),
):
    """
    Hanya user dengan role **admin** yang dapat membuat akun baru.
    Email harus unik.
    """
    # Check duplicate email
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


# ── POST /login ───────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login dan dapatkan access token",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Autentikasi dengan email & password.
    Mengembalikan JWT access token (berlaku 8 jam).
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract role value safely (handles both Enum and string)
    role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
    token = create_access_token(subject=user.id, role=role_value)
    return TokenResponse(access_token=token)


# ── GET /me ───────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Profil user yang sedang login",
)
async def me(current_user: User = Depends(get_current_user)):
    """Mengembalikan data user berdasarkan token yang dikirim."""
    return current_user
