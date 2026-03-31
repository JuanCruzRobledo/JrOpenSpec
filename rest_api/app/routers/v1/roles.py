"""Roles router — RBAC permission matrix endpoint.

Thin handler: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.role import RolesMatrixResponse
from rest_api.app.services.domain.roles_service import RolesService
from rest_api.app.services.permissions.context import PermissionContext
from rest_api.app.services.permissions.strategies import Action

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
)


@router.get("/permissions", response_model=RolesMatrixResponse)
async def get_permissions_matrix(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """GET /api/v1/roles/permissions."""
    ctx = PermissionContext(user)
    ctx.require_can(Action.READ, "Staff")

    service = RolesService()
    matrix = service.get_permissions_matrix()
    return {"roles": matrix}
