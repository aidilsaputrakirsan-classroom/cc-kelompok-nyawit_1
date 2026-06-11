from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import PRStatus


# ── Request ────────────────────────────────────────────────────────
class GRNSubmitSchema(BaseModel):
    """Payload to submit proof-of-receipt documents for a PO."""

    po_id: int = Field(..., description="ID of the Purchase Order")
    receipt_url: str = Field(..., max_length=500, description="URL to uploaded receipt document")
    commercial_invoice_url: str = Field(..., max_length=500, description="URL to uploaded commercial invoice")
    goods_photo_url: str = Field(..., max_length=500, description="URL to uploaded goods photo")


class GRNVerify(BaseModel):
    """Payload for admin to verify/close a GRN submission."""

    status: PRStatus = Field(
        ...,
        description="Target status: VERIFIED or CLOSED",
    )
    verification_note: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Catatan verifikasi wajib diisi",
    )

    @model_validator(mode="after")
    def validate_status(self):
        """Only VERIFIED or CLOSED are valid target statuses."""
        if self.status not in (PRStatus.VERIFIED, PRStatus.CLOSED):
            raise ValueError("Status hanya boleh VERIFIED atau CLOSED")
        return self


# ── Response ───────────────────────────────────────────────────────
class GRNOut(BaseModel):
    id: int
    po_id: int
    requester_id: int
    receipt_url: str
    commercial_invoice_url: str
    goods_photo_url: str
    submitted_at: datetime
    verification_note: str | None

    model_config = {"from_attributes": True}
