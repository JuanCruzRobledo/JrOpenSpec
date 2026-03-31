"""Assignment schemas — Spanish API field names."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class AssignmentWaiterInfo(BaseModel):
    """Inline waiter info for assignment responses."""

    id: int
    nombre_completo: str


class AssignmentSectorInfo(BaseModel):
    """Inline sector info for assignment responses."""

    id: int
    nombre: str


class AssignmentRead(BaseModel):
    """Assignment response shape."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    mozo: AssignmentWaiterInfo
    sector: AssignmentSectorInfo
    turno: str
    fecha: str


class AssignmentBulkItem(BaseModel):
    """Single assignment entry within a bulk create request."""

    mozo_id: int
    sector_id: int


class AssignmentBulkCreate(BaseModel):
    """POST /api/v1/branches/{branch_id}/assignments/bulk request body."""

    fecha: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]  # ISO date YYYY-MM-DD
    turno: str  # ShiftType value: morning, afternoon, night
    asignaciones: list[AssignmentBulkItem]


class AssignmentBulkResponse(BaseModel):
    """Response for bulk assignment save."""

    turno: str
    fecha: str
    eliminadas: int
    creadas: int


class AssignmentDeleteResponse(BaseModel):
    """Response for assignment deletion."""

    message: str
    id: int
