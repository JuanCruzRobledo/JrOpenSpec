"""Product schemas — Spanish API field names."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class ProductRead(BaseModel):
    """Product response shape matching spec section 3.6."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None = None
    categoria_id: int
    categoria_nombre: str
    subcategoria_id: int | None = None
    subcategoria_nombre: str | None = None
    precio: int  # cents
    imagen_url: str | None = None
    destacado: bool = False
    popular: bool = False
    estado: str  # "activo" | "inactivo"
    created_at: str
    updated_at: str


class ProductCreate(BaseModel):
    """POST /api/v1/branches/{branch_id}/products request body."""

    nombre: Annotated[str, Field(min_length=2, max_length=100)]
    descripcion: Annotated[str | None, Field(max_length=500)] = None
    categoria_id: int
    subcategoria_id: int | None = None
    precio: int = Field(ge=0)  # cents
    imagen_url: str | None = None
    destacado: bool = False
    popular: bool = False
    estado: str = "activo"


class ProductUpdate(BaseModel):
    """PUT request body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=2, max_length=100)] = None
    descripcion: Annotated[str | None, Field(max_length=500)] = None
    categoria_id: int | None = None
    subcategoria_id: int | None = None
    precio: int | None = Field(default=None, ge=0)
    imagen_url: str | None = None
    destacado: bool | None = None
    popular: bool | None = None
    estado: str | None = None


class ProductDeleteResponse(BaseModel):
    """Response for product deletion."""

    message: str
