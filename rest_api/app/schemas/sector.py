"""Sector schemas — Spanish API field names."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class SectorRead(BaseModel):
    """Sector response shape."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sucursal_id: int
    nombre: str
    tipo: str
    prefijo: str
    capacidad: int | None = None
    orden: int = 0
    estado: str  # "activo" | "inactivo"
    created_at: str
    updated_at: str


class SectorCreate(BaseModel):
    """POST /api/v1/branches/{branch_id}/sectors request body."""

    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    tipo: str = "interior"  # SectorType value
    capacidad: int | None = Field(default=None, gt=0)
    orden: int | None = None


class SectorUpdate(BaseModel):
    """PUT request body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    tipo: str | None = None
    capacidad: int | None = Field(default=None, gt=0)
    orden: int | None = None
    estado: str | None = None


class SectorDeleteResponse(BaseModel):
    """Response for sector deletion with cascade counts."""

    message: str
    cascade: dict[str, int]
