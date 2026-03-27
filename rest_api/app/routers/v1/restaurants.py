"""Restaurant router — GET /me, PUT /{id}.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.envelope import SingleResponse
from rest_api.app.schemas.restaurant import RestaurantRead, RestaurantUpdate
from rest_api.app.services.domain.restaurant_service import RestaurantService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


def _get_service(db: AsyncSession = Depends(get_db)) -> RestaurantService:
    return RestaurantService(db)


@router.get("/me", response_model=SingleResponse[RestaurantRead])
async def get_my_restaurant(
    user: dict[str, Any] = Depends(get_current_user),
    service: RestaurantService = Depends(_get_service),
) -> dict:
    """GET /api/v1/restaurants/me — retrieve current tenant info."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.get_by_tenant_id(ctx.tenant_id)
    return {"data": data}


@router.put("/{restaurant_id}", response_model=SingleResponse[RestaurantRead])
async def update_restaurant(
    restaurant_id: int,
    body: RestaurantUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: RestaurantService = Depends(_get_service),
) -> dict:
    """PUT /api/v1/restaurants/{id} — update tenant info."""
    ctx = PermissionContext(user)
    ctx.require_admin()

    data = await service.update(
        tenant_id=restaurant_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}
