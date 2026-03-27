"""Dietary profile dashboard router — CRUD.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.dietary_profile import (
    DietaryProfileCreate,
    DietaryProfileRead,
    DietaryProfileUpdate,
)
from rest_api.app.schemas.envelope import ListResponse, SingleResponse
from rest_api.app.services.domain.dietary_profile_service import DietaryProfileService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dietary-profiles", tags=["dietary-profiles"])


def _get_service(db: AsyncSession = Depends(get_db)) -> DietaryProfileService:
    return DietaryProfileService(db)


@router.get("/", response_model=ListResponse[DietaryProfileRead])
async def list_dietary_profiles(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    user: dict[str, Any] = Depends(get_current_user),
    service: DietaryProfileService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    items, total = await service.list(ctx.tenant_id, page, limit, search)
    return {"data": items, "meta": {"page": page, "limit": limit, "total": total}}


@router.get("/{profile_id}", response_model=SingleResponse[DietaryProfileRead])
async def get_dietary_profile(
    profile_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: DietaryProfileService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    return {"data": await service.get_by_id(profile_id, ctx.tenant_id)}


@router.post("/", response_model=SingleResponse[DietaryProfileRead], status_code=status.HTTP_201_CREATED)
async def create_dietary_profile(
    body: DietaryProfileCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: DietaryProfileService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    data = await service.create(ctx.tenant_id, body.model_dump(exclude_unset=True))
    return {"data": data}


@router.put("/{profile_id}", response_model=SingleResponse[DietaryProfileRead])
async def update_dietary_profile(
    profile_id: int,
    body: DietaryProfileUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: DietaryProfileService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    data = await service.update(profile_id, ctx.tenant_id, body.model_dump(exclude_unset=True))
    return {"data": data}


@router.delete("/{profile_id}")
async def delete_dietary_profile(
    profile_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: DietaryProfileService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_admin()
    return await service.delete(profile_id, ctx.tenant_id, int(ctx.user_id))
