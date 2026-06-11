from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import PRStatus
from app.schemas.pr_line_item import ItemSchema, ItemOut


# ── Request ────────────────────────────────────────────────────────
class PRCreate(BaseModel):
    """Payload to create a new Purchase Requisition with line items."""

    title: str = Field(..., min_length=1, max_length=255)
    justification: str | None = Field(None, max_length=2000)
    items: list[ItemSchema] = Field(..., min_length=1, description="At least one line item required")


class PRUpdate(BaseModel):
    """Payload to update an existing Purchase Requisition (only when SUBMITTED)."""

    title: str = Field(..., min_length=1, max_length=255)
    justification: str | None = Field(None, max_length=2000)
    items: list[ItemSchema] = Field(..., min_length=1, description="At least one line item required")


class PRStatusUpdate(BaseModel):
    """Payload for admin to transition PR status (approve / reject)."""

    status: PRStatus
    approval_note: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_approval_note(self):
        """approval_note wajib diisi saat APPROVED atau REJECTED."""
        if self.status in (PRStatus.APPROVED, PRStatus.REJECTED):
            if not self.approval_note or not self.approval_note.strip():
                raise ValueError(
                    "approval_note wajib diisi saat status APPROVED atau REJECTED"
                )
        return self


# ── Response ───────────────────────────────────────────────────────
class PROut(BaseModel):
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
