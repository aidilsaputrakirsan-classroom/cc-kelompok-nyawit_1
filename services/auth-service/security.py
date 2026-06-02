"""
Security utilities — password hashing (bcrypt) dan JWT token management.

Dipindahkan dari monolith (backend/app/core/security.py) dengan
penyesuaian: config dibaca dari environment variable langsung,
bukan dari Pydantic Settings (supaya service ini ringan & mandiri).
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext

# ── Configuration dari environment ────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "dev-refresh-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ── Password hashing ──────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash password dengan bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifikasi password terhadap hash-nya."""
    return pwd_context.verify(plain, hashed)


# ── JWT Access Token ──────────────────────────────────────────────
def create_access_token(subject: int, role: str) -> str:
    """
    Buat JWT access token.
    
    Payload:
        sub  – user id
        role – "admin" atau "requester"
        type – "access"
        exp  – waktu kedaluwarsa
        iat  – waktu dibuat
        jti  – unique ID token (untuk blacklist saat logout)
        iss  – issuer
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "iss": "sicure-auth-service",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decode dan validasi access token.
    Return payload dict jika valid, None jika tidak.
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
        if payload.get("type") != "access":
            return None
        return payload
    except PyJWTError:
        return None


# ── JWT Refresh Token ─────────────────────────────────────────────
def create_refresh_token(subject: int) -> str:
    """
    Buat JWT refresh token (berlaku lebih lama, untuk minta access token baru).
    Pakai secret key BERBEDA dari access token — lebih aman.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(subject),
        "type": "refresh",
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "iss": "sicure-auth-service",
    }
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def decode_refresh_token(token: str) -> dict | None:
    """Decode dan validasi refresh token."""
    try:
        payload = jwt.decode(
            token,
            REFRESH_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except PyJWTError:
        return None
