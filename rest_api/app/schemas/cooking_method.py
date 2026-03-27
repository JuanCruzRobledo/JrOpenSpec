"""CookingMethod schemas — Dashboard API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class CookingMethodCreate(BaseModel):
    """POST body for creating a custom cooking method."""

    codigo: Annotated[str, Field(min_length=1, max_length=50)]
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    icono: str | None = None


class CookingMethodUpdate(BaseModel):
    """PUT body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    icono: str | None = None


class CookingMethodRead(BaseModel):
    """Cooking method response shape."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    icono: str | None = None
    es_sistema: bool = False
    created_at: str
    updated_at: str
