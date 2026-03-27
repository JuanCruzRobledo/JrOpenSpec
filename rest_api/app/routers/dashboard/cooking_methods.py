"""Cooking method dashboard router — CRUD.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.cooking_method import (
    CookingMethodCreate,
    CookingMethodRead,
    CookingMethodUpdate,
)
from rest_api.app.schemas.envelope import ListResponse, SingleResponse
from rest_api.app.services.domain.cooking_method_service import CookingMethodService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cooking-methods", tags=["cooking-methods"])


def _get_service(db: AsyncSession = Depends(get_db)) -> CookingMethodService:
    return CookingMethodService(db)


@router.get("/", response_model=ListResponse[CookingMethodRead])
async def list_cooking_methods(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    user: dict[str, Any] = Depends(get_current_user),
    service: CookingMethodService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    items, total = await service.list(ctx.tenant_id, page, limit, search)
    return {"data": items, "meta": {"page": page, "limit": limit, "total": total}}


@router.get("/{method_id}", response_model=SingleResponse[CookingMethodRead])
async def get_cooking_method(
    method_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: CookingMethodService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    return {"data": await service.get_by_id(method_id, ctx.tenant_id)}


@router.post("/", response_model=SingleResponse[CookingMethodRead], status_code=status.HTTP_201_CREATED)
async def create_cooking_method(
    body: CookingMethodCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: CookingMethodService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    data = await service.create(ctx.tenant_id, body.model_dump(exclude_unset=True))
    return {"data": data}


@router.put("/{method_id}", response_model=SingleResponse[CookingMethodRead])
async def update_cooking_method(
    method_id: int,
    body: CookingMethodUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: CookingMethodService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_management()
    data = await service.update(method_id, ctx.tenant_id, body.model_dump(exclude_unset=True))
    return {"data": data}


@router.delete("/{method_id}")
async def delete_cooking_method(
    method_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: CookingMethodService = Depends(_get_service),
) -> dict:
    ctx = PermissionContext(user)
    ctx.require_admin()
    return await service.delete(method_id, ctx.tenant_id, int(ctx.user_id))
