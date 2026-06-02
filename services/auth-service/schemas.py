"""
Pydantic schemas untuk Auth Service.

Mendefinisikan format request dan response untuk setiap endpoint.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from models import UserRole


# ── Request Schemas ────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Body untuk POST /login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """Body untuk POST /register (admin-only)."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimal 8 karakter")
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.REQUESTER


class RegisterRequesterRequest(BaseModel):
    """Body untuk POST /register-requester (public, self-register)."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimal 8 karakter")
    full_name: str = Field(..., min_length=1, max_length=255)


class RefreshRequest(BaseModel):
    """Body untuk POST /refresh."""
    refresh_token: str


# ── Response Schemas ───────────────────────────────────────────────

class TokenResponse(BaseModel):
    """Response setelah login/refresh berhasil."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Data user yang aman untuk ditampilkan (tanpa password)."""
    id: int
    email: str
    full_name: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenVerifyResponse(BaseModel):
    """
    Response dari GET /verify — dipanggil oleh service lain.
    
    Ini endpoint BARU yang tidak ada di monolith.
    Procurement Service akan memanggil endpoint ini untuk memverifikasi
    apakah token user valid, tanpa perlu akses ke auth_db.
    """
    user_id: int
    email: str
    full_name: str
    role: str
