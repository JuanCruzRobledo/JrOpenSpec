"""Staff schemas — Spanish API field names. Password NEVER included in reads."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Annotated


class StaffRead(BaseModel):
    """Staff response shape. Password is NEVER included."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_completo: str
    email: str
    telefono: str | None = None
    rol: str | None = None
    dni: str | None = None
    fecha_contratacion: str | None = None
    estado: str  # "activo" | "inactivo"
    created_at: str


class StaffCreate(BaseModel):
    """POST /api/v1/staff request body."""

    nombre: Annotated[str, Field(min_length=2, max_length=100)]
    apellido: Annotated[str, Field(min_length=2, max_length=100)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]
    rol: str = "READONLY"
    telefono: str | None = None
    dni: str | None = Field(default=None, max_length=20)
    fecha_contratacion: str | None = None  # ISO date
    sucursal_id: int | None = None


class StaffUpdate(BaseModel):
    """PUT request body — all fields optional."""

    nombre: Annotated[str | None, Field(min_length=2, max_length=100)] = None
    apellido: Annotated[str | None, Field(min_length=2, max_length=100)] = None
    email: EmailStr | None = None
    password: str | None = None
    rol: str | None = None
    telefono: str | None = None
    dni: str | None = Field(default=None, max_length=20)
    fecha_contratacion: str | None = None
    sucursal_id: int | None = None


class StaffDeleteResponse(BaseModel):
    """Response for staff deletion."""

    message: str
    id: int
