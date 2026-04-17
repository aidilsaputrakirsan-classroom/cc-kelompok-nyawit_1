"""
Security utilities — password hashing (bcrypt) and JWT token management.

Tokens:
    - Access token  : short-lived (30 min), carries sub + role + type
    - Refresh token : long-lived  (7 days), carries sub + type only

Standard JWT claims included: sub, exp, iat, jti, iss.
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ──────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return bcrypt hash of the given plain-text password."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return pwd_context.verify(plain, hashed)


# ── JWT access token ──────────────────────────────────────────────
def create_access_token(subject: int, role: str) -> str:
    """
    Create a signed JWT access token.

    Payload claims:
        sub  – user id (as string, per JWT spec)
        role – user role ("admin" | "requester")
        type – "access"
        exp  – expiration timestamp
        iat  – issued-at timestamp
        jti  – unique token identifier (UUID4)
        iss  – issuer identifier
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "iss": "sicure-backend",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate a JWT access token.

    Returns the payload dict on success, or None if the token is
    invalid / expired / wrong type.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
        if payload.get("type") != "access":
            return None
        return payload
    except PyJWTError:
        return None


# ── JWT refresh token ─────────────────────────────────────────────
def create_refresh_token(subject: int) -> str:
    """
    Create a signed JWT refresh token.

    Refresh tokens use a **separate secret** so that even if the
    access-token secret is compromised, refresh tokens remain safe.

    Payload claims:
        sub  – user id
        type – "refresh"
        exp  – expiration timestamp
        iat  – issued-at timestamp
        jti  – unique token identifier (UUID4)
        iss  – issuer identifier
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(subject),
        "type": "refresh",
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "iss": "sicure-backend",
    }
    return jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_refresh_token(token: str) -> dict | None:
    """
    Decode and validate a JWT refresh token.

    Returns the payload dict on success, or None if the token is
    invalid / expired / wrong type.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_REFRESH_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except PyJWTError:
        return None
