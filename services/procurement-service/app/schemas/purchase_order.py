from datetime import datetime

from pydantic import BaseModel, Field


# ── Request ────────────────────────────────────────────────────────
class POCreate(BaseModel):
    """Payload to issue a Purchase Order against an approved PR."""

    pr_id: int = Field(..., description="ID of the approved Purchase Requisition")
    allocated_budget: float = Field(..., gt=0, description="Budget allocated for this PO")


# ── Response ───────────────────────────────────────────────────────
class POOut(BaseModel):
    id: int
    po_number: str
    pr_id: int
    issued_by: int
    issued_at: datetime
    allocated_budget: float

    model_config = {"from_attributes": True}
