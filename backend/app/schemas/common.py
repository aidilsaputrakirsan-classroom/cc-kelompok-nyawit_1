"""
Common / shared Pydantic schemas — standard API response wrapper & pagination.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel):
    """Standard JSON envelope for every API response."""

    success: bool = True
    data: Any = None
    message: str = "OK"


class PaginationMeta(BaseModel):
    """Pagination metadata returned alongside list responses."""

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
