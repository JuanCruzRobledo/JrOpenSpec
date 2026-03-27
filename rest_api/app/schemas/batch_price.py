"""Batch price update schemas."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator
from typing import Annotated

from shared.enums import BatchPriceOperation


class BatchPriceRequest(BaseModel):
    """POST body for batch price preview/apply."""

    product_ids: Annotated[list[int], Field(min_length=1, max_length=500)]
    operation: BatchPriceOperation
    amount: Annotated[Decimal, Field(ge=0)]
    branch_id: int | None = None

    @field_validator("product_ids")
    @classmethod
    def unique_product_ids(cls, v: list[int]) -> list[int]:
        """Ensure no duplicate product IDs."""
        if len(v) != len(set(v)):
            msg = "product_ids must be unique"
            raise ValueError(msg)
        return v


class BatchPriceChangeItem(BaseModel):
    """A single price change in the preview."""

    product_id: int
    nombre_producto: str
    branch_id: int
    nombre_sucursal: str
    precio_anterior_centavos: int
    precio_nuevo_centavos: int


class BatchPricePreviewResponse(BaseModel):
    """Response for batch price preview."""

    cambios: list[BatchPriceChangeItem]
    total_productos: int
    total_sucursales: int
    total_cambios: int


class BatchPriceApplyRequest(BaseModel):
    """POST body for applying batch price changes."""

    product_ids: Annotated[list[int], Field(min_length=1, max_length=500)]
    operation: BatchPriceOperation
    amount: Annotated[Decimal, Field(ge=0)]
    branch_id: int | None = None
    confirmed: bool

    @field_validator("confirmed")
    @classmethod
    def must_be_confirmed(cls, v: bool) -> bool:
        """Apply requires explicit confirmation."""
        if not v:
            msg = "confirmed must be true to apply"
            raise ValueError(msg)
        return v


class BatchPriceApplyResponse(BaseModel):
    """Response for batch price apply."""

    applied: int
    audit_log_ids: list[int]
