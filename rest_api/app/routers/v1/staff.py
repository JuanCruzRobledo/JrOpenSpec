"""Staff router — CRUD endpoints under /api/v1/staff.

Tenant-scoped. Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.envelope import ListResponse, SingleResponse
from rest_api.app.schemas.staff import (
    StaffCreate,
    StaffDeleteResponse,
    StaffRead,
    StaffUpdate,
)
from rest_api.app.services.domain.staff_service import StaffService
from rest_api.app.services.permissions.context import PermissionContext
from rest_api.app.services.permissions.strategies import Action
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/staff",
    tags=["staff"],
)


def _get_service(db: AsyncSession = Depends(get_db)) -> StaffService:
    return StaffService(db)


@router.get("/", response_model=ListResponse[StaffRead])
async def list_staff(
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: str | None = Query(None),
    is_active: bool = Query(True),
    user: dict[str, Any] = Depends(get_current_user),
    service: StaffService = Depends(_get_service),
) -> dict:
    """GET /api/v1/staff?q=&page=&limit=&role=&is_active=."""
    ctx = PermissionContext(user)
    ctx.require_can(Action.READ, "Staff")

    items, total = await service.list_staff(
        tenant_id=ctx.tenant_id,
        q=q,
        role=role,
        is_active=is_active,
        page=page,
        limit=limit,
    )
    return {
        "data": items,
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.post("/", response_model=SingleResponse[StaffRead], status_code=status.HTTP_201_CREATED)
async def create_staff(
    body: StaffCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: StaffService = Depends(_get_service),
) -> dict:
    """POST /api/v1/staff."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.create_staff(
        tenant_id=ctx.tenant_id,
        data=body.model_dump(exclude_unset=True),
        current_user=user,
    )
    return {"data": data}


@router.put("/{user_id}", response_model=SingleResponse[StaffRead])
async def update_staff(
    user_id: int,
    body: StaffUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: StaffService = Depends(_get_service),
) -> dict:
    """PUT /api/v1/staff/{user_id}."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.update_staff(
        user_id=user_id,
        tenant_id=ctx.tenant_id,
        data=body.model_dump(exclude_unset=True),
        current_user=user,
    )
    return {"data": data}


@router.delete("/{user_id}", response_model=SingleResponse[StaffDeleteResponse])
async def delete_staff(
    user_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: StaffService = Depends(_get_service),
) -> dict:
    """DELETE /api/v1/staff/{user_id}."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.delete_staff(
        user_id=user_id,
        tenant_id=ctx.tenant_id,
    )
    return {"data": data}
