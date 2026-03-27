"""Restaurant (Tenant) schemas — Spanish API field names."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class RestaurantRead(BaseModel):
    """GET /api/v1/restaurants/me response shape."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    slug: str
    descripcion: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None


class RestaurantUpdate(BaseModel):
    """PUT /api/v1/restaurants/{id} request body."""

    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    slug: Annotated[str, Field(min_length=1, max_length=100)]
    descripcion: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
