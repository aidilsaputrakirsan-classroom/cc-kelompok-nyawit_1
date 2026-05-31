"""
Auth Service — Microservice untuk Authentication & User Management.

Tanggung jawab:
- Register user (admin-only & self-register)
- Login (generate JWT access + refresh token)
- Refresh token
- Logout (blacklist token)
- GET /me (profil user)
- GET /verify ← BARU! Dipanggil oleh service lain untuk verifikasi token

Endpoint /verify adalah "jembatan" antar service. Procurement Service
tidak punya akses ke auth_db, jadi ia memanggil endpoint ini via HTTP
untuk memastikan token user valid.
"""

import os
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, get_db, Base
from models import User, TokenBlacklist, UserRole
from schemas import (
    LoginRequest,
    RegisterRequest,
    RegisterRequesterRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    TokenVerifyResponse,
)
from security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)

# ── Create tables on startup ──────────────────────────────────────
app = FastAPI(
    title="SiCure Auth Service",
    description="Authentication microservice — register, login, verify tokens",
    version="2.0.0",
)


@app.on_event("startup")
async def startup():
    """Buat tabel jika belum ada (untuk development)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── CORS ──────────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bearer token scheme
_bearer = HTTPBearer()


# ══════════════════════════════════════════════════════════════════
# HELPER: Get current user (internal, untuk endpoint /me dan /logout)
# ══════════════════════════════════════════════════════════════════
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validasi token dan return User object."""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kedaluwarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Cek apakah token sudah di-blacklist (logout)
    jti = payload.get("jti")
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

    # Ambil user dari database
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(roles: list[str]):
    """Dependency factory: cek apakah user punya role yang diizinkan."""
    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Role yang diizinkan: {', '.join(roles)}",
            )
        return current_user
    return _checker


# ══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check — dipakai Docker untuk memastikan service hidup."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "2.0.0",
    }


# ── POST /register (admin only) ──────────────────────────────────
@app.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["admin"])),
):
    """Register user baru — hanya admin yang bisa."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")

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


# ── POST /register-requester (public) ────────────────────────────
@app.post("/register-requester", response_model=UserResponse, status_code=201)
async def register_requester(
    body: RegisterRequesterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Self-register sebagai requester — endpoint publik."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole.REQUESTER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ── POST /login ───────────────────────────────────────────────────
@app.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login — return access token + refresh token."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
        )

    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    access = create_access_token(subject=user.id, role=role_value)
    refresh = create_refresh_token(subject=user.id)

    return TokenResponse(access_token=access, refresh_token=refresh)


# ── POST /refresh ─────────────────────────────────────────────────
@app.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Tukar refresh token dengan access + refresh token baru."""
    payload = decode_refresh_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token tidak valid atau sudah kedaluwarsa",
        )

    # Cek apakah refresh token sudah di-revoke
    jti = payload.get("jti")
    if jti:
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token sudah di-revoke, silakan login kembali",
            )

    # Pastikan user masih ada
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")

    # Blacklist refresh token lama (token rotation)
    if jti:
        exp = payload.get("exp")
        blacklisted = TokenBlacklist(
            jti=jti,
            user_id=int(user_id),
            expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
        )
        db.add(blacklisted)
        await db.commit()

    # Buat token pair baru
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    new_access = create_access_token(subject=user.id, role=role_value)
    new_refresh = create_refresh_token(subject=user.id)

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


# ── POST /logout ──────────────────────────────────────────────────
@app.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Logout — blacklist access token supaya tidak bisa dipakai lagi."""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token tidak valid")

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

    return {"message": "Logout berhasil, token telah di-revoke"}


# ── GET /me ───────────────────────────────────────────────────────
@app.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return profil user yang sedang login."""
    return current_user


# ══════════════════════════════════════════════════════════════════
# GET /verify — ENDPOINT BARU UNTUK INTER-SERVICE COMMUNICATION
# ══════════════════════════════════════════════════════════════════
@app.get("/verify", response_model=TokenVerifyResponse)
async def verify_token(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Verifikasi JWT token — DIPANGGIL OLEH SERVICE LAIN (bukan frontend).

    Alur:
    1. Procurement Service terima request dari user dengan token
    2. Procurement Service panggil GET /verify ke Auth Service
    3. Auth Service cek token valid? sudah di-blacklist?
    4. Jika valid, return data user (id, email, name, role)
    5. Procurement Service lanjutkan proses dengan data user tersebut

    Ini adalah INTI dari inter-service communication di microservices.
    """
    # Extract token dari header "Bearer xxx"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Format header: Bearer <token>")

    token = authorization.split("Bearer ")[1]
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Token tidak valid atau expired")

    # Cek blacklist
    jti = payload.get("jti")
    if jti:
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=401, detail="Token sudah di-revoke")

    # Pastikan user masih ada di database
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")

    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)

    return TokenVerifyResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=role_value,
    )
