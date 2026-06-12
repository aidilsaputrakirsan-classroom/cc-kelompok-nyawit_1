"""
Vendor Quote model — a vendor's price offer attached to a Purchase Requisition.

Implements the "3 quotation" comparison: a requester attaches one or more
vendor quotes (with survey evidence) when creating a PR.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VendorQuote(Base):
    __tablename__ = "vendor_quotes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requisitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_contact: Mapped[str] = mapped_column(String(255), nullable=False)
    quoted_price: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    survey_date: Mapped[date] = mapped_column(Date, nullable=False)
    survey_evidence_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_recommended: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ── relationships ──────────────────────────────────────────────
    purchase_requisition: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition",
        back_populates="vendor_quotes",
    )

    def __repr__(self) -> str:
        return (
            f"<VendorQuote id={self.id} pr_id={self.pr_id} "
            f"vendor={self.vendor_name!r} recommended={self.is_recommended}>"
        )
