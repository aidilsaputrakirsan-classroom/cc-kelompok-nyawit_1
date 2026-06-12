"""
Pydantic schemas for Vendor Quote operations.

The survey-evidence file is uploaded separately (multipart); these schemas
cover only the structured metadata of each vendor quote.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class VendorQuoteIn(BaseModel):
    """One element of the `vendor_quotes_json` payload (no file)."""

    vendor_name: str = Field(..., min_length=1, max_length=255)       # Req 2.1
    vendor_contact: str = Field(..., min_length=1, max_length=255)     # Req 2.2
    quoted_price: Decimal = Field(..., gt=0)                           # Req 2.3
    survey_date: date                                                 # Req 2.4
    is_recommended: bool = False                                      # Req 4


class VendorQuoteOut(BaseModel):
    id: int
    pr_id: int
    vendor_name: str
    vendor_contact: str
    quoted_price: float
    survey_date: date
    survey_evidence_url: str
    is_recommended: bool

    model_config = {"from_attributes": True}
