"""
Purchase Order (PO) model — issued after a PR is approved.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    po_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="Auto-generated PO number, e.g. PO-20260415-0001",
    )
    pr_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requisitions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    issued_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    issued_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    allocated_budget: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    selected_vendor_quote_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendor_quotes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── relationships ──────────────────────────────────────────────
    purchase_requisition: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition",
        back_populates="purchase_order",
    )
    selected_vendor_quote: Mapped["VendorQuote | None"] = relationship(
        "VendorQuote",
    )
    issuer: Mapped["User"] = relationship(
        "User",
        back_populates="issued_purchase_orders",
        foreign_keys=[issued_by],
    )
    grn_document: Mapped["GRNDocument | None"] = relationship(
        "GRNDocument",
        back_populates="purchase_order",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<PO id={self.id} number={self.po_number!r}>"
