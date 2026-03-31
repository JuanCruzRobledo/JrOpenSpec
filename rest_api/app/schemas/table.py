"""Table schemas — Spanish API field names."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class TableRead(BaseModel):
    """Table response shape."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sector_id: int
    numero: int
    capacidad: int
    estado: str  # TableStatus value
    codigo: str | None = None
    pos_x: int | None = None
    pos_y: int | None = None
    version: int
    status_changed_at: str | None = None
    occupied_at: str | None = None
    order_requested_at: str | None = None
    order_fulfilled_at: str | None = None
    check_requested_at: str | None = None
    session_count: int = 0
    estado_activo: str = "activo"
    created_at: str
    updated_at: str


class TableCreate(BaseModel):
    """POST /api/v1/branches/{branch_id}/tables request body."""

    numero: int | None = Field(default=None, gt=0)
    capacidad: int = Field(default=4, ge=1, le=20)
    sector_id: int


class TableBatchCreate(BaseModel):
    """POST /api/v1/branches/{branch_id}/tables/batch request body."""

    sector_id: int
    cantidad: Annotated[int, Field(ge=1, le=50)]
    capacidad: int = Field(default=4, ge=1, le=20)
    numero_inicio: int | None = Field(default=None, gt=0)


class TableUpdate(BaseModel):
    """PUT request body — all fields optional."""

    capacidad: int | None = Field(default=None, ge=1, le=20)
    sector_id: int | None = None
    pos_x: int | None = None
    pos_y: int | None = None


class TableStatusUpdate(BaseModel):
    """PATCH /{table_id}/status request body."""

    estado: str  # TableStatus value
    version: int


class TableDeleteResponse(BaseModel):
    """Response for table deletion."""

    message: str


class TableBatchCreateResponse(BaseModel):
    """Response for batch table creation."""

    cantidad_creadas: int
    mesas: list[TableRead]
