"""Subcategory schemas — Spanish API field names."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class SubcategoryRead(BaseModel):
    """Subcategory response shape matching spec section 3.5."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    imagen_url: str | None = None
    categoria_id: int
    categoria_nombre: str
    orden: int = 0
    estado: str  # "activo" | "inactivo"
    productos_count: int = 0
    created_at: str
    updated_at: str


class SubcategoryCreate(BaseModel):
    """POST /api/v1/branches/{branch_id}/subcategories request body."""

    nombre: Annotated[str, Field(min_length=2, max_length=100)]
    categoria_id: int
    imagen_url: str | None = None
    orden: int | None = None
    estado: str = "activo"


class SubcategoryUpdate(BaseModel):
    """PUT request body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=2, max_length=100)] = None
    categoria_id: int | None = None
    imagen_url: str | None = None
    orden: int | None = None
    estado: str | None = None


class SubcategoryDeleteResponse(BaseModel):
    """Response for subcategory deletion with cascade counts."""

    message: str
    cascade: dict[str, int]
