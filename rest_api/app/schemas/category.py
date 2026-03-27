"""Category schemas — Spanish API field names."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class CategoryRead(BaseModel):
    """Category response shape matching spec section 3.4."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    icono: str | None = None
    imagen_url: str | None = None
    orden: int = 0
    estado: str  # "activo" | "inactivo"
    es_home: bool = False
    created_at: str
    updated_at: str


class CategoryCreate(BaseModel):
    """POST /api/v1/branches/{branch_id}/categories request body."""

    nombre: Annotated[str, Field(min_length=2, max_length=100)]
    icono: str | None = None
    imagen_url: str | None = None
    orden: int | None = None
    estado: str = "activo"


class CategoryUpdate(BaseModel):
    """PUT request body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=2, max_length=100)] = None
    icono: str | None = None
    imagen_url: str | None = None
    orden: int | None = None
    estado: str | None = None


class CategoryDeleteResponse(BaseModel):
    """Response for category deletion with cascade counts."""

    message: str
    cascade: dict[str, int]
