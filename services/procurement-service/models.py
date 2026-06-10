"""
Models untuk Procurement Service.

Berisi: PurchaseRequisition, PRLineItem, PurchaseOrder, GRNDocument.

PERHATIKAN:
- TIDAK ADA model User di sini!
- Field seperti requester_id dan issued_by adalah INTEGER biasa (bukan ForeignKey ke users)
- Karena tabel users ada di database lain (auth_db), kita tidak bisa buat FK cross-database
- Konsistensi dijaga di level aplikasi (via Auth Service), bukan di level database
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ── Enums ─────────────────────────────────────────────────────────
class PRStatus(str, enum.Enum):
    """Purchase Requisition lifecycle status."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PO_ISSUED = "PO_ISSUED"
    DOC_SUBMITTED = "DOC_SUBMITTED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"


# ── Purchase Requisition ──────────────────────────────────────────
class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pr_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True,
    )
    # requester_id: reference ke user di auth_db (BUKAN foreign key!)
    requester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PRStatus] = mapped_column(
        String(20), nullable=False, default=PRStatus.DRAFT, index=True,
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False, default=0,
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now(),
    )
    approval_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships (hanya dalam procurement_db)
    line_items: Mapped[list["PRLineItem"]] = relationship(
        "PRLineItem", back_populates="purchase_requisition",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder", back_populates="purchase_requisition", uselist=False,
    )


# ── PR Line Item ─────────────────────────────────────────────────
class PRLineItem(Base):
    __tablename__ = "pr_line_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pr_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requisitions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_unit_price: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False,
    )
    subtotal: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False,
    )

    purchase_requisition: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition", back_populates="line_items",
    )


# ── Purchase Order ────────────────────────────────────────────────
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    po_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True,
    )
    pr_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requisitions.id", ondelete="RESTRICT"),
        nullable=False, unique=True, index=True,
    )
    # issued_by: reference ke admin user di auth_db (BUKAN foreign key!)
    issued_by: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    allocated_budget: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False,
    )

    purchase_requisition: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition", back_populates="purchase_order",
    )
    grn_document: Mapped["GRNDocument | None"] = relationship(
        "GRNDocument", back_populates="purchase_order", uselist=False,
    )


# ── GRN Document ─────────────────────────────────────────────────
class GRNDocument(Base):
    __tablename__ = "grn_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    po_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="RESTRICT"),
        nullable=False, unique=True, index=True,
    )
    # requester_id: reference ke user di auth_db (BUKAN foreign key!)
    requester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    receipt_url: Mapped[str] = mapped_column(String(500), nullable=False)
    commercial_invoice_url: Mapped[str] = mapped_column(String(500), nullable=False)
    goods_photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="grn_document",
    )
