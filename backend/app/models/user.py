"""
User model — represents system users (admin / requester).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole


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

    # ── relationships ──────────────────────────────────────────────
    purchase_requisitions: Mapped[list["PurchaseRequisition"]] = relationship(
        "PurchaseRequisition",
        back_populates="requester",
        foreign_keys="PurchaseRequisition.requester_id",
    )
    issued_purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="issuer",
        foreign_keys="PurchaseOrder.issued_by",
    )
    grn_submissions: Mapped[list["GRNDocument"]] = relationship(
        "GRNDocument",
        back_populates="requester",
        foreign_keys="GRNDocument.requester_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
