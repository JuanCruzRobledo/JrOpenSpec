"""Allergen schemas — Dashboard API (Spanish field names)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class AllergenCreate(BaseModel):
    """POST body for creating a custom allergen."""

    codigo: Annotated[str, Field(min_length=1, max_length=50, alias="codigo")]
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    descripcion: str | None = None
    icono: str | None = None


class AllergenUpdate(BaseModel):
    """PUT body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    descripcion: str | None = None
    icono: str | None = None


class CrossReactionRead(BaseModel):
    """Cross-reaction in a response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    allergen_id: int
    related_allergen_id: int
    related_code: str
    related_name: str
    descripcion: str
    severidad: str


class AllergenRead(BaseModel):
    """Allergen response shape."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    icono: str | None = None
    es_sistema: bool = False
    reacciones_cruzadas: list[CrossReactionRead] = []
    created_at: str
    updated_at: str


class CrossReactionCreate(BaseModel):
    """POST body for adding a cross-reaction."""

    related_allergen_id: int
    descripcion: Annotated[str, Field(min_length=1)]
    severidad: Annotated[str, Field(pattern=r"^(low|moderate|severe|life_threatening)$")]
