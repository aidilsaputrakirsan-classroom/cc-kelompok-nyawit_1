from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequesterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.user import UserCreate
from app.schemas.common import APIResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── POST /register ────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=APIResponse,
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

    user_response = UserResponse.model_validate(user)
    return APIResponse(
        success=True,
        data=user_response.model_dump(),
        message="User berhasil dibuat"
    )


# ── POST /register-requester ─────────────────────────────────────
@router.post(
    "/register-requester",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register mandiri sebagai requester (public)",
)
async def register_requester(
    body: RegisterRequesterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint publik untuk registrasi mandiri.
    Role otomatis di-set sebagai **requester**.
    """
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
        role=UserRole.REQUESTER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    user_response = UserResponse.model_validate(user)
    return APIResponse(
        success=True,
        data=user_response.model_dump(),
        message="Registrasi berhasil! Silakan login.",
    )


# ── POST /login ───────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=APIResponse,
    summary="Login dan dapatkan access + refresh token",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Autentikasi dengan email & password.
    Mengembalikan JWT access token (berlaku 30 menit) dan
    refresh token (berlaku 7 hari).
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
    access = create_access_token(subject=user.id, role=role_value)
    refresh = create_refresh_token(subject=user.id)

    token_response = TokenResponse(access_token=access, refresh_token=refresh)
    return APIResponse(
        success=True,
        data=token_response.model_dump(),
        message="Login berhasil"
    )


# ── POST /refresh ─────────────────────────────────────────────────
@router.post(
    "/refresh",
    response_model=APIResponse,
    summary="Refresh access token menggunakan refresh token",
)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Tukar refresh token yang masih valid dengan pasangan
    access token + refresh token baru (token rotation).
    """
    payload = decode_refresh_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token tidak valid atau sudah kedaluwarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti: str | None = payload.get("jti")
    if jti:
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token sudah di-revoke, silakan login kembali",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if jti:
        exp = payload.get("exp")
        blacklisted = TokenBlacklist(
            jti=jti,
            user_id=int(user_id),
            expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
        )
        db.add(blacklisted)
        await db.commit()

    role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
    new_access = create_access_token(subject=user.id, role=role_value)
    new_refresh = create_refresh_token(subject=user.id)

    token_response = TokenResponse(access_token=new_access, refresh_token=new_refresh)
    return APIResponse(
        success=True,
        data=token_response.model_dump(),
        message="Token berhasil diperbarui",
    )


# ── POST /logout ──────────────────────────────────────────────────
@router.post(
    "/logout",
    response_model=APIResponse,
    summary="Logout dan revoke access token",
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke (blacklist) the current access token.
    """
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kedaluwarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    exp = payload.get("exp")

    if jti and exp:
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        )
        if result.scalar_one_or_none() is None:
            blacklisted = TokenBlacklist(
                jti=jti,
                user_id=int(payload.get("sub")),
                expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
            )
            db.add(blacklisted)
            await db.commit()

    return APIResponse(
        success=True,
        data=None,
        message="Logout berhasil, token telah di-revoke",
    )


# ── GET /me ───────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=APIResponse,
    summary="Profil user yang sedang login",
)
async def me(current_user: User = Depends(get_current_user)):
    user_response = UserResponse.model_validate(current_user)
    return APIResponse(
        success=True,
        data=user_response.model_dump(),
        message="OK"
    )


# ── GET /verify ──────────────────────────────────────────────────
@router.get(
    "/verify",
    response_model=APIResponse,
    summary="Verifikasi token JWT (internal call)",
)
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verifikasi token JWT untuk service lain.
    Menerima header Authorization: Bearer <token>.
    """
    role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    return APIResponse(
        success=True,
        data={
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": role_value,
        },
        message="Token verified",
    )
