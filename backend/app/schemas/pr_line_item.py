"""
Pydantic schemas for PR Line Items.
"""

from pydantic import BaseModel, Field


class ItemSchema(BaseModel):
    """Used both for creating and reading line items."""

    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0)
    unit_of_measure: str = Field(..., min_length=1, max_length=50, examples=["pcs", "kg", "liter", "box", "unit"])
    estimated_unit_price: float = Field(..., gt=0)

    @property
    def computed_subtotal(self) -> float:
        return round(self.quantity * self.estimated_unit_price, 2)


class ItemOut(ItemSchema):
    """Line item as returned from the API (includes id, pr_id, subtotal)."""

    id: int
    pr_id: int
    subtotal: float

    model_config = {"from_attributes": True}
