from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


# ── Request ────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Plain-text password (will be hashed)")
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.REQUESTER


# ── Response ───────────────────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}
