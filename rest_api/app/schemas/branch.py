"""Branch schemas — Spanish API field names mapped from English DB columns."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class BranchRead(BaseModel):
    """Branch response shape matching spec section 3.3."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    imagen_url: str | None = None
    horario_apertura: str = "09:00"
    horario_cierre: str = "23:00"
    estado: str  # "activo" | "inactivo"
    orden: int = 0
    created_at: str
    updated_at: str


class BranchCreate(BaseModel):
    """POST /api/v1/branches request body."""

    nombre: Annotated[str, Field(min_length=2, max_length=100)]
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    imagen_url: str | None = None
    horario_apertura: str = "09:00"
    horario_cierre: str = "23:00"
    estado: str = "activo"
    orden: int | None = None


class BranchUpdate(BaseModel):
    """PUT /api/v1/branches/{id} request body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=2, max_length=100)] = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    imagen_url: str | None = None
    horario_apertura: str | None = None
    horario_cierre: str | None = None
    estado: str | None = None
    orden: int | None = None


class DeleteCascadeResponse(BaseModel):
    """Response for branch deletion with cascade counts."""

    message: str
    cascade: dict[str, int]
