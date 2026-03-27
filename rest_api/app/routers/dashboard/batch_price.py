"""Batch price dashboard router — preview + apply.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.batch_price import (
    BatchPriceApplyRequest,
    BatchPriceApplyResponse,
    BatchPricePreviewResponse,
    BatchPriceRequest,
)
from rest_api.app.schemas.envelope import SingleResponse
from rest_api.app.services.domain.batch_price_service import BatchPriceService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products/batch-price", tags=["batch-price"])


def _get_service(db: AsyncSession = Depends(get_db)) -> BatchPriceService:
    return BatchPriceService(db)


@router.post("/preview", response_model=SingleResponse[BatchPricePreviewResponse])
async def preview_batch_price(
    body: BatchPriceRequest,
    user: dict[str, Any] = Depends(get_current_user),
    service: BatchPriceService = Depends(_get_service),
) -> dict:
    """POST /api/dashboard/products/batch-price/preview — preview without side effects."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.preview(
        product_ids=body.product_ids,
        operation=body.operation,
        amount=body.amount,
        branch_id=body.branch_id,
        tenant_id=ctx.tenant_id,
    )
    return {"data": data}


@router.post("/apply", response_model=SingleResponse[BatchPriceApplyResponse])
async def apply_batch_price(
    body: BatchPriceApplyRequest,
    user: dict[str, Any] = Depends(get_current_user),
    service: BatchPriceService = Depends(_get_service),
) -> dict:
    """POST /api/dashboard/products/batch-price/apply — apply with confirmation."""
    ctx = PermissionContext(user)
    ctx.require_admin()

    data = await service.apply(
        product_ids=body.product_ids,
        operation=body.operation,
        amount=body.amount,
        branch_id=body.branch_id,
        tenant_id=ctx.tenant_id,
        user_id=int(ctx.user_id),
    )
    return {"data": data}
