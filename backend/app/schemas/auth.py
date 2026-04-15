"""
Pydantic schemas for authentication responses.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


# ── Request ────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


# ── Response ───────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    """Returned after successful login."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user representation (no sensitive fields)."""

    id: int
    email: str
    full_name: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}
