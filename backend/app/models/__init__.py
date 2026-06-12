"""
Central model registry — importing this module ensures all models are
registered with the SQLAlchemy metadata so Alembic autogenerate works.
"""

from app.models.enums import PRStatus, UserRole  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.purchase_requisition import PurchaseRequisition  # noqa: F401
from app.models.pr_line_item import PRLineItem  # noqa: F401
from app.models.vendor_quote import VendorQuote  # noqa: F401
from app.models.purchase_order import PurchaseOrder  # noqa: F401
from app.models.grn_document import GRNDocument  # noqa: F401
from app.models.token_blacklist import TokenBlacklist  # noqa: F401

__all__ = [
    "PRStatus",
    "UserRole",
    "User",
    "PurchaseRequisition",
    "PRLineItem",
    "VendorQuote",
    "PurchaseOrder",
    "GRNDocument",
    "TokenBlacklist",
]
