"""Role schemas — RBAC permission matrix."""

from __future__ import annotations

from pydantic import BaseModel


class RolePermissions(BaseModel):
    """Single role with its permissions."""

    rol: str
    etiqueta: str
    permisos: list[str]


class RolesMatrixResponse(BaseModel):
    """GET /api/v1/roles/permissions response."""

    roles: list[RolePermissions]
