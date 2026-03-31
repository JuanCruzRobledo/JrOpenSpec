"""Sector router — CRUD endpoints nested under /api/v1/branches/{branch_id}/sectors.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.envelope import ListResponse, SingleResponse
from rest_api.app.schemas.sector import (
    SectorCreate,
    SectorDeleteResponse,
    SectorRead,
    SectorUpdate,
)
from rest_api.app.services.domain.sector_service import SectorService
from rest_api.app.services.permissions.context import PermissionContext
from rest_api.app.services.permissions.strategies import Action
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/branches/{branch_id}/sectors",
    tags=["sectors"],
)


def _get_service(db: AsyncSession = Depends(get_db)) -> SectorService:
    return SectorService(db)


@router.get("/", response_model=ListResponse[SectorRead])
async def list_sectors(
    branch_id: int,
    include_inactive: bool = Query(False),
    user: dict[str, Any] = Depends(get_current_user),
    service: SectorService = Depends(_get_service),
) -> dict:
    """GET /api/v1/branches/{branch_id}/sectors."""
    ctx = PermissionContext(user)
    ctx.require_can(Action.READ, "Sector")
    ctx.require_branch_access(branch_id)

    items = await service.list_sectors(
        branch_id=branch_id,
        include_inactive=include_inactive,
    )
    return {
        "data": items,
        "meta": {"page": 1, "limit": len(items), "total": len(items)},
    }


@router.post("/", response_model=SingleResponse[SectorRead], status_code=status.HTTP_201_CREATED)
async def create_sector(
    branch_id: int,
    body: SectorCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: SectorService = Depends(_get_service),
) -> dict:
    """POST /api/v1/branches/{branch_id}/sectors."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.create_sector(
        branch_id=branch_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.put("/{sector_id}", response_model=SingleResponse[SectorRead])
async def update_sector(
    branch_id: int,
    sector_id: int,
    body: SectorUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: SectorService = Depends(_get_service),
) -> dict:
    """PUT /api/v1/branches/{branch_id}/sectors/{sector_id}."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.update_sector(
        sector_id=sector_id,
        branch_id=branch_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.delete("/{sector_id}", response_model=SingleResponse[SectorDeleteResponse])
async def delete_sector(
    branch_id: int,
    sector_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: SectorService = Depends(_get_service),
) -> dict:
    """DELETE /api/v1/branches/{branch_id}/sectors/{sector_id}."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.delete_sector(
        sector_id=sector_id,
        branch_id=branch_id,
        user_id=int(ctx.user_id),
    )
    return {"data": data}
