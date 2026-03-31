"""Roles service — RBAC permission matrix."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

ROLES_MATRIX: list[dict] = [
    {
        "rol": "ADMIN",
        "etiqueta": "Administrador",
        "permisos": ["*"],
    },
    {
        "rol": "MANAGER",
        "etiqueta": "Gerente",
        "permisos": [
            "sectors:*", "tables:*", "staff:*", "assignments:*",
            "menu:*", "orders:*", "kitchen:read", "reports:read",
        ],
    },
    {
        "rol": "WAITER",
        "etiqueta": "Mozo",
        "permisos": [
            "sectors:read", "tables:read", "tables:write",
            "assignments:read", "menu:read",
            "orders:read", "orders:write",
        ],
    },
    {
        "rol": "KITCHEN",
        "etiqueta": "Cocina",
        "permisos": [
            "kitchen:read", "kitchen:write",
            "menu:read", "orders:read",
        ],
    },
    {
        "rol": "READONLY",
        "etiqueta": "Solo Lectura",
        "permisos": [
            "sectors:read", "tables:read", "staff:read",
            "assignments:read", "menu:read", "orders:read",
            "kitchen:read", "reports:read",
        ],
    },
]


class RolesService:
    """Provides the RBAC permission matrix."""

    def get_permissions_matrix(self) -> list[dict]:
        """Return the full RBAC permission matrix."""
        return ROLES_MATRIX

    def get_role_permissions(self, role: str) -> dict | None:
        """Return permissions for a specific role, or None if not found."""
        for entry in ROLES_MATRIX:
            if entry["rol"] == role:
                return entry
        return None

    def get_available_roles(self) -> list[str]:
        """Return list of all valid role names."""
        return [entry["rol"] for entry in ROLES_MATRIX]
