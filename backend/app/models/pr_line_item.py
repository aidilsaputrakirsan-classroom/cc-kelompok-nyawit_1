"""
PR Line Item model — individual items within a Purchase Requisition.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PRLineItem(Base):
    __tablename__ = "pr_line_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requisitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="e.g. pcs, kg, liter, box, unit",
    )
    estimated_unit_price: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    subtotal: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        comment="quantity * estimated_unit_price",
    )

    # ── relationships ──────────────────────────────────────────────
    purchase_requisition: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition",
        back_populates="line_items",
    )

    def __repr__(self) -> str:
        return f"<PRLineItem id={self.id} item={self.item_name!r} qty={self.quantity}>"
