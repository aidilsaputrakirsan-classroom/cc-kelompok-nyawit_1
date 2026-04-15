"""
Procurement status enums for the SiCure system.
"""

import enum


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


class UserRole(str, enum.Enum):
    """User role within the procurement system."""

    ADMIN = "admin"
    REQUESTER = "requester"
