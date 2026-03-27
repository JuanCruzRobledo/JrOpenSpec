"""BranchProduct schemas — per-branch pricing and availability."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class BranchProductRead(BaseModel):
    """Branch-product pricing and availability response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    nombre_sucursal: str
    product_id: int
    nombre_producto: str
    esta_activo: bool
    precio_centavos: int | None = None
    precio_efectivo_centavos: int
    orden: int = 0


class BranchProductUpdate(BaseModel):
    """Input for updating a single branch-product."""

    esta_activo: bool | None = None
    precio_centavos: Annotated[int | None, Field(ge=0)] = None
    orden: int | None = None


class BranchProductBulkItem(BaseModel):
    """Single item in bulk update."""

    branch_id: int
    esta_activo: bool = True
    precio_centavos: Annotated[int | None, Field(ge=0)] = None


class BranchProductBulkUpdate(BaseModel):
    """Input for bulk update of branch-product records for a product."""

    sucursales: list[BranchProductBulkItem]


class ToggleAvailabilityResponse(BaseModel):
    """Response after toggling availability."""

    branch_id: int
    product_id: int
    esta_activo: bool


class PriceUpdateResponse(BaseModel):
    """Response after updating price."""

    branch_id: int
    product_id: int
    precio_centavos: int | None
    precio_efectivo_centavos: int
