"""BranchProduct dashboard router — per-branch pricing and availability.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.branch_product import (
    BranchProductBulkUpdate,
    BranchProductRead,
    PriceUpdateResponse,
    ToggleAvailabilityResponse,
)
from rest_api.app.schemas.envelope import SingleResponse
from rest_api.app.services.domain.branch_product_service import BranchProductService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["branch-products"])


def _get_service(db: AsyncSession = Depends(get_db)) -> BranchProductService:
    return BranchProductService(db)


@router.get("/{product_id}/branches", response_model=SingleResponse[list[BranchProductRead]])
async def get_product_branches(
    product_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: BranchProductService = Depends(_get_service),
) -> dict:
    """GET /api/dashboard/products/{id}/branches — branch pricing grid."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.get_by_product(product_id, ctx.tenant_id)
    return {"data": data}


@router.put("/{product_id}/branches", response_model=SingleResponse[list[BranchProductRead]])
async def bulk_update_product_branches(
    product_id: int,
    body: BranchProductBulkUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: BranchProductService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/products/{id}/branches — bulk update."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.bulk_upsert(
        product_id=product_id,
        tenant_id=ctx.tenant_id,
        items=[item.model_dump() for item in body.sucursales],
    )
    return {"data": data}


@router.patch(
    "/{product_id}/branches/{branch_id}/toggle",
    response_model=SingleResponse[ToggleAvailabilityResponse],
)
async def toggle_availability(
    product_id: int,
    branch_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: BranchProductService = Depends(_get_service),
) -> dict:
    """PATCH /api/dashboard/products/{id}/branches/{branch_id}/toggle."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.toggle_availability(product_id, branch_id, ctx.tenant_id)
    return {"data": data}


@router.patch(
    "/{product_id}/branches/{branch_id}/price",
    response_model=SingleResponse[PriceUpdateResponse],
)
async def update_price(
    product_id: int,
    branch_id: int,
    body: dict,
    user: dict[str, Any] = Depends(get_current_user),
    service: BranchProductService = Depends(_get_service),
) -> dict:
    """PATCH /api/dashboard/products/{id}/branches/{branch_id}/price."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.update_price(
        product_id=product_id,
        branch_id=branch_id,
        tenant_id=ctx.tenant_id,
        price_cents=body.get("precio_centavos"),
    )
    return {"data": data}
