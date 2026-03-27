"""Badge schemas — Dashboard API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class BadgeCreate(BaseModel):
    """POST body for creating a custom badge."""

    codigo: Annotated[str, Field(min_length=1, max_length=50)]
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    color: Annotated[str, Field(min_length=4, max_length=7, pattern=r"^#[0-9A-Fa-f]{3,6}$")]
    icono: str | None = None


class BadgeUpdate(BaseModel):
    """PUT body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    color: Annotated[str | None, Field(min_length=4, max_length=7, pattern=r"^#[0-9A-Fa-f]{3,6}$")] = None
    icono: str | None = None


class BadgeRead(BaseModel):
    """Badge response shape."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    color: str
    icono: str | None = None
    es_sistema: bool = False
    created_at: str
    updated_at: str
