"""Product router — CRUD nested under /api/v1/branches/{branch_id}/products.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.envelope import ListResponse, SingleResponse
from rest_api.app.schemas.product import (
    ProductCreate,
    ProductDeleteResponse,
    ProductRead,
    ProductUpdate,
)
from rest_api.app.services.domain.product_service import ProductService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/branches/{branch_id}/products",
    tags=["products"],
)


def _get_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(db)


@router.get("/", response_model=ListResponse[ProductRead])
async def list_products(
    branch_id: int,
    page: int = 1,
    limit: int = 10,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductService = Depends(_get_service),
) -> dict:
    """GET /api/v1/branches/{branch_id}/products?page=1&limit=10."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    items, total = await service.list(
        tenant_id=ctx.tenant_id,
        branch_id=branch_id,
        page=page,
        limit=limit,
    )
    return {
        "data": items,
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.post("/", response_model=SingleResponse[ProductRead], status_code=status.HTTP_201_CREATED)
async def create_product(
    branch_id: int,
    body: ProductCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductService = Depends(_get_service),
) -> dict:
    """POST /api/v1/branches/{branch_id}/products."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.create(
        tenant_id=ctx.tenant_id,
        branch_id=branch_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.put("/{product_id}", response_model=SingleResponse[ProductRead])
async def update_product(
    branch_id: int,
    product_id: int,
    body: ProductUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductService = Depends(_get_service),
) -> dict:
    """PUT /api/v1/branches/{branch_id}/products/{id}."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.update(
        product_id=product_id,
        tenant_id=ctx.tenant_id,
        branch_id=branch_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.delete("/{product_id}", response_model=SingleResponse[ProductDeleteResponse])
async def delete_product(
    branch_id: int,
    product_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductService = Depends(_get_service),
) -> dict:
    """DELETE /api/v1/branches/{branch_id}/products/{id}."""
    ctx = PermissionContext(user)
    ctx.require_admin()
    ctx.require_branch_access(branch_id)

    data = await service.delete(
        product_id=product_id,
        tenant_id=ctx.tenant_id,
        branch_id=branch_id,
        user_id=int(ctx.user_id),
    )
    return {"data": data}
