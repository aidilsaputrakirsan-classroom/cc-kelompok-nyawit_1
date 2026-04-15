"""
Goods Received Note (GRN) Document model — proof-of-receipt uploaded by requester.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GRNDocument(Base):
    __tablename__ = "grn_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    po_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    receipt_url: Mapped[str] = mapped_column(String(500), nullable=False)
    commercial_invoice_url: Mapped[str] = mapped_column(String(500), nullable=False)
    goods_photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── relationships ──────────────────────────────────────────────
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="grn_document",
    )
    requester: Mapped["User"] = relationship(
        "User",
        back_populates="grn_submissions",
        foreign_keys=[requester_id],
    )

    def __repr__(self) -> str:
        return f"<GRN id={self.id} po_id={self.po_id}>"
