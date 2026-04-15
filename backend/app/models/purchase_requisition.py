"""
Purchase Requisition (PR) model — the core procurement request document.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PRStatus


class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pr_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="Auto-generated PR number, e.g. PR-20260415-0001",
    )
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PRStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PRStatus.DRAFT,
        index=True,
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    approval_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── relationships ──────────────────────────────────────────────
    requester: Mapped["User"] = relationship(
        "User",
        back_populates="purchase_requisitions",
        foreign_keys=[requester_id],
    )
    line_items: Mapped[list["PRLineItem"]] = relationship(
        "PRLineItem",
        back_populates="purchase_requisition",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        back_populates="purchase_requisition",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<PR id={self.id} number={self.pr_number!r} status={self.status}>"
