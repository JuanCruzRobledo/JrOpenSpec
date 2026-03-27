"""Seal schemas — Dashboard API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class SealCreate(BaseModel):
    """POST body for creating a custom seal."""

    codigo: Annotated[str, Field(min_length=1, max_length=50)]
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    color: Annotated[str, Field(min_length=4, max_length=7, pattern=r"^#[0-9A-Fa-f]{3,6}$")]
    icono: str | None = None
    descripcion: str | None = None


class SealUpdate(BaseModel):
    """PUT body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    color: Annotated[str | None, Field(min_length=4, max_length=7, pattern=r"^#[0-9A-Fa-f]{3,6}$")] = None
    icono: str | None = None
    descripcion: str | None = None


class SealRead(BaseModel):
    """Seal response shape."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    color: str
    icono: str | None = None
    descripcion: str | None = None
    es_sistema: bool = False
    created_at: str
    updated_at: str
