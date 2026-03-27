"""Badge dashboard router — CRUD.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.badge import BadgeCreate, BadgeRead, BadgeUpdate
from rest_api.app.schemas.envelope import ListResponse, SingleResponse
from rest_api.app.services.domain.badge_service import BadgeService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/badges", tags=["badges"])


def _get_service(db: AsyncSession = Depends(get_db)) -> BadgeService:
    return BadgeService(db)


@router.get("/", response_model=ListResponse[BadgeRead])
async def list_badges(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    user: dict[str, Any] = Depends(get_current_user),
    service: BadgeService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    items, total = await service.list(ctx.tenant_id, page, limit, search)
    return {"data": items, "meta": {"page": page, "limit": limit, "total": total}}


@router.get("/{badge_id}", response_model=SingleResponse[BadgeRead])
async def get_badge(
    badge_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: BadgeService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    return {"data": await service.get_by_id(badge_id, ctx.tenant_id)}


@router.post("/", response_model=SingleResponse[BadgeRead], status_code=status.HTTP_201_CREATED)
async def create_badge(
    body: BadgeCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: BadgeService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    data = await service.create(ctx.tenant_id, body.model_dump(exclude_unset=True))
    return {"data": data}


@router.put("/{badge_id}", response_model=SingleResponse[BadgeRead])
async def update_badge(
    badge_id: int,
    body: BadgeUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: BadgeService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    data = await service.update(badge_id, ctx.tenant_id, body.model_dump(exclude_unset=True))
    return {"data": data}


@router.delete("/{badge_id}")
async def delete_badge(
    badge_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: BadgeService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_admin()
    return await service.delete(badge_id, ctx.tenant_id, int(ctx.user_id))
