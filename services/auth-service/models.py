"""
Models untuk Auth Service.

Hanya berisi User dan TokenBlacklist.
TIDAK ada model procurement di sini — itu tanggung jawab Procurement Service.

Perhatikan: User model di sini TIDAK punya relationship ke PurchaseRequisition,
PurchaseOrder, dll. Karena model-model itu ada di database lain (procurement_db).
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


# ── Enum ──────────────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    """Role user dalam sistem."""
    ADMIN = "admin"
    REQUESTER = "requester"


# ── User Model ────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, create_constraint=False),
        nullable=False,
        default=UserRole.REQUESTER,
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"


# ── Token Blacklist Model ─────────────────────────────────────────
class TokenBlacklist(Base):
    """
    Menyimpan token yang sudah di-revoke (logout).
    Saat user logout, jti token disimpan di sini supaya tidak bisa dipakai lagi.
    """
    __tablename__ = "token_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    blacklisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
