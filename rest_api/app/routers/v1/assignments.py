"""Assignment router — waiter-sector assignments under /api/v1/branches/{branch_id}/assignments.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.assignment import (
    AssignmentBulkCreate,
    AssignmentBulkResponse,
    AssignmentDeleteResponse,
)
from rest_api.app.schemas.envelope import SingleResponse
from rest_api.app.services.domain.assignment_service import AssignmentService
from rest_api.app.services.permissions.context import PermissionContext
from rest_api.app.services.permissions.strategies import Action
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/branches/{branch_id}/assignments",
    tags=["assignments"],
)


def _get_service(db: AsyncSession = Depends(get_db)) -> AssignmentService:
    return AssignmentService(db)


@router.get("/")
async def list_assignments(
    branch_id: int,
    fecha: date = Query(default_factory=date.today),
    user: dict[str, Any] = Depends(get_current_user),
    service: AssignmentService = Depends(_get_service),
) -> dict:
    """GET /api/v1/branches/{branch_id}/assignments?fecha=YYYY-MM-DD.

    Returns assignments grouped by shift: { morning: [...], afternoon: [...], night: [...] }.
    """
    ctx = PermissionContext(user)
    ctx.require_can(Action.READ, "WaiterSectorAssignment")
    ctx.require_branch_access(branch_id)

    grouped = await service.list_assignments(
        branch_id=branch_id,
        date_=fecha,
    )
    return {"data": grouped}


@router.post("/bulk", response_model=SingleResponse[AssignmentBulkResponse], status_code=status.HTTP_201_CREATED)
async def bulk_save_assignments(
    branch_id: int,
    body: AssignmentBulkCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: AssignmentService = Depends(_get_service),
) -> dict:
    """POST /api/v1/branches/{branch_id}/assignments/bulk."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    # Convert bulk items to list of dicts for service
    assignments_data = [
        {"mozo_id": item.mozo_id, "sector_id": item.sector_id}
        for item in body.asignaciones
    ]

    data = await service.bulk_save(
        branch_id=branch_id,
        date_=date.fromisoformat(body.fecha),
        shift=body.turno,
        assignments=assignments_data,
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.delete("/{assignment_id}", response_model=SingleResponse[AssignmentDeleteResponse])
async def delete_assignment(
    branch_id: int,
    assignment_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: AssignmentService = Depends(_get_service),
) -> dict:
    """DELETE /api/v1/branches/{branch_id}/assignments/{assignment_id}."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.delete_assignment(
        assignment_id=assignment_id,
    )
    return {"data": data}
