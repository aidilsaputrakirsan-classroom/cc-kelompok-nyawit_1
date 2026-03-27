from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict
import re


# Email regex: standard format
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# Password regex: min 8, uppercase, number, special char
PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"


# ============================================================
# AUTH SCHEMAS
# ============================================================

class UserCreate(BaseModel):
    """Schema untuk registrasi user baru."""
    email: str = Field(..., examples=["user@student.itk.ac.id"])
    name: str = Field(..., min_length=2, max_length=100, examples=["Aidil Saputra"])
    password: str = Field(..., min_length=8, examples=["Passw0rd!"])

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(EMAIL_REGEX, v):
            raise ValueError('Email format tidak valid (contoh: user@example.com)')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError('Password harus minimal 8 karakter, mengandung huruf besar, angka, dan karakter khusus (@$!%*?&)')
        return v


class UserResponse(BaseModel):
    """Schema untuk response user (tanpa password)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    """Schema untuk login request."""
    email: str = Field(..., examples=["user@student.itk.ac.id"])
    password: str = Field(..., examples=["Passw0rd!"])

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(EMAIL_REGEX, v):
            raise ValueError('Email format tidak valid')
        return v


class TokenResponse(BaseModel):
    """Schema untuk response setelah login berhasil."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============================================================
# ITEM SCHEMAS
# ============================================================

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)


class ItemCreate(ItemBase):
    """Schema untuk create item."""
    pass


class ItemUpdate(BaseModel):
    """Schema untuk update item (partial)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)


class ItemResponse(ItemBase):
    """Schema untuk response satu item."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ItemListResponse(BaseModel):
    """Schema untuk list items dengan pagination."""
    items: list[ItemResponse]
    total: int
    skip: int
    limit: int


# ============================================================
# STATS SCHEMA (NEW)
# ============================================================

class ItemStats(BaseModel):
    """Schema untuk statistik items."""
    total_items: int
    total_value: float
    avg_price: float
    avg_quantity: float
    low_stock: int = Field(..., description="Items dengan quantity < 10")

