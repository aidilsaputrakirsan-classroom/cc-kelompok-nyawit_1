"""
Pydantic schemas untuk Procurement Service.
Gabungan dari semua schemas procurement di monolith.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from models import PRStatus


# ══════════════════════════════════════════════════════════════════
# COMMON — Standard API Response
# ══════════════════════════════════════════════════════════════════

class APIResponse(BaseModel):
    """Standard JSON envelope untuk setiap API response."""
    success: bool = True
    data: Any = None
    message: str = "OK"


class PaginationMeta(BaseModel):
    """Metadata pagination."""
    page: int
    per_page: int
    total_items: int
    total_pages: int


class PaginatedResponse(BaseModel):
    """Standard paginated list response."""
    success: bool = True
    data: list[Any] = []
    message: str = "OK"
    pagination: PaginationMeta


# ══════════════════════════════════════════════════════════════════
# PR LINE ITEM
# ══════════════════════════════════════════════════════════════════

class ItemSchema(BaseModel):
    """Schema untuk membuat line item."""
    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0)
    unit_of_measure: str = Field(..., min_length=1, max_length=50)
    estimated_unit_price: float = Field(..., gt=0)


class ItemOut(ItemSchema):
    """Line item response (termasuk id, pr_id, subtotal)."""
    id: int
    pr_id: int
    subtotal: float

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════
# PURCHASE REQUISITION
# ══════════════════════════════════════════════════════════════════

class PRCreate(BaseModel):
    """Payload untuk membuat PR baru."""
    title: str = Field(..., min_length=1, max_length=255)
    justification: str | None = Field(None, max_length=2000)
    items: list[ItemSchema] = Field(..., min_length=1)


class PRUpdate(BaseModel):
    """Payload untuk edit PR yang masih SUBMITTED."""
    title: str = Field(..., min_length=1, max_length=255)
    justification: str | None = Field(None, max_length=2000)
    items: list[ItemSchema] = Field(..., min_length=1)


class PRStatusUpdate(BaseModel):
    """Payload admin untuk approve/reject PR."""
    status: PRStatus
    approval_note: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_approval_note(self):
        if self.status in (PRStatus.APPROVED, PRStatus.REJECTED):
            if not self.approval_note or not self.approval_note.strip():
                raise ValueError("approval_note wajib diisi saat APPROVED atau REJECTED")
        return self


class PROut(BaseModel):
    """PR response."""
    id: int
    pr_number: str
    requester_id: int
    title: str
    justification: str | None
    status: PRStatus
    total_amount: float
    created_at: datetime
    updated_at: datetime
    approval_note: str | None
    line_items: list[ItemOut] = []

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════
# PURCHASE ORDER
# ══════════════════════════════════════════════════════════════════

class POOut(BaseModel):
    """PO response."""
    id: int
    po_number: str
    pr_id: int
    issued_by: int
    issued_at: datetime
    allocated_budget: float

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════
# GRN DOCUMENT
# ══════════════════════════════════════════════════════════════════

class GRNVerify(BaseModel):
    """Payload admin untuk verify/close GRN."""
    status: PRStatus
    verification_note: str = Field(..., min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_status(self):
        if self.status not in (PRStatus.VERIFIED, PRStatus.CLOSED):
            raise ValueError("Status hanya boleh VERIFIED atau CLOSED")
        return self


class GRNOut(BaseModel):
    """GRN response."""
    id: int
    po_id: int
    requester_id: int
    receipt_url: str
    commercial_invoice_url: str
    goods_photo_url: str
    submitted_at: datetime
    verification_note: str | None

    model_config = {"from_attributes": True}
