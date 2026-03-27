"""Seal dashboard router — CRUD.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.envelope import ListResponse, SingleResponse
from rest_api.app.schemas.seal import SealCreate, SealRead, SealUpdate
from rest_api.app.services.domain.seal_service import SealService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/seals", tags=["seals"])


def _get_service(db: AsyncSession = Depends(get_db)) -> SealService:
    return SealService(db)


@router.get("/", response_model=ListResponse[SealRead])
async def list_seals(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    user: dict[str, Any] = Depends(get_current_user),
    service: SealService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    items, total = await service.list(ctx.tenant_id, page, limit, search)
    return {"data": items, "meta": {"page": page, "limit": limit, "total": total}}


@router.get("/{seal_id}", response_model=SingleResponse[SealRead])
async def get_seal(
    seal_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: SealService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    return {"data": await service.get_by_id(seal_id, ctx.tenant_id)}


@router.post("/", response_model=SingleResponse[SealRead], status_code=status.HTTP_201_CREATED)
async def create_seal(
    body: SealCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: SealService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    data = await service.create(ctx.tenant_id, body.model_dump(exclude_unset=True))
    return {"data": data}


@router.put("/{seal_id}", response_model=SingleResponse[SealRead])
async def update_seal(
    seal_id: int,
    body: SealUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: SealService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    data = await service.update(seal_id, ctx.tenant_id, body.model_dump(exclude_unset=True))
    return {"data": data}


@router.delete("/{seal_id}")
async def delete_seal(
    seal_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: SealService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_admin()
    return await service.delete(seal_id, ctx.tenant_id, int(ctx.user_id))
