"""Generic response envelope following the spec contract.

All API responses use:
  Success single: { "data": T }
  Success list:   { "data": [T], "meta": { "page", "limit", "total" } }
  Error:          { "detail": str, "code": str }
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    page: int
    limit: int
    total: int


class SingleResponse(BaseModel, Generic[T]):
    """Envelope for a single-item response: { data: T }."""

    data: T


class ListResponse(BaseModel, Generic[T]):
    """Envelope for a paginated list response: { data: [T], meta: {...} }."""

    data: list[T]
    meta: PaginationMeta


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    code: str
