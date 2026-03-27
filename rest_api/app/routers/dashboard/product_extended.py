"""Product extended dashboard router — sub-resource endpoints for product enrichment.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.envelope import SingleResponse
from rest_api.app.schemas.product_extended import (
    ProductAllergenInput,
    ProductAllergenRead,
    ProductBadgeSet,
    ProductCookingMethodSet,
    ProductDietarySet,
    ProductFlavorProfileSet,
    ProductIngredientRead,
    ProductIngredientSet,
    ProductSealSet,
    ProductTextureProfileSet,
)
from rest_api.app.services.domain.product_extended_service import ProductExtendedService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["product-extended"])


def _get_service(db: AsyncSession = Depends(get_db)) -> ProductExtendedService:
    return ProductExtendedService(db)


@router.put("/{product_id}/allergens", response_model=SingleResponse[list[ProductAllergenRead]])
async def set_product_allergens(
    product_id: int,
    body: list[ProductAllergenInput],
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductExtendedService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/products/{id}/allergens — replace all allergen associations."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.set_allergens(
        product_id=product_id,
        tenant_id=ctx.tenant_id,
        allergen_data=[item.model_dump() for item in body],
    )
    return {"data": data}


@router.put("/{product_id}/dietary-profiles")
async def set_product_dietary_profiles(
    product_id: int,
    body: ProductDietarySet,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductExtendedService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/products/{id}/dietary-profiles."""
    ctx = PermissionContext(user)
    ctx.require_management()

    ids = await service.set_dietary_profiles(product_id, ctx.tenant_id, body.profile_ids)
    return {"data": {"profile_ids": ids}}


@router.put("/{product_id}/cooking-methods")
async def set_product_cooking_methods(
    product_id: int,
    body: ProductCookingMethodSet,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductExtendedService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/products/{id}/cooking-methods."""
    ctx = PermissionContext(user)
    ctx.require_management()

    ids = await service.set_cooking_methods(product_id, ctx.tenant_id, body.method_ids)
    return {"data": {"method_ids": ids}}


@router.put("/{product_id}/flavor-profiles")
async def set_product_flavor_profiles(
    product_id: int,
    body: ProductFlavorProfileSet,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductExtendedService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/products/{id}/flavor-profiles."""
    ctx = PermissionContext(user)
    ctx.require_management()

    profiles = await service.set_flavor_profiles(
        product_id, ctx.tenant_id, [p.value for p in body.profiles],
    )
    return {"data": {"profiles": profiles}}


@router.put("/{product_id}/texture-profiles")
async def set_product_texture_profiles(
    product_id: int,
    body: ProductTextureProfileSet,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductExtendedService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/products/{id}/texture-profiles."""
    ctx = PermissionContext(user)
    ctx.require_management()

    profiles = await service.set_texture_profiles(
        product_id, ctx.tenant_id, [p.value for p in body.profiles],
    )
    return {"data": {"profiles": profiles}}


@router.put("/{product_id}/ingredients", response_model=SingleResponse[list[ProductIngredientRead]])
async def set_product_ingredients(
    product_id: int,
    body: ProductIngredientSet,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductExtendedService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/products/{id}/ingredients — replace all ingredients."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.set_ingredients(
        product_id=product_id,
        tenant_id=ctx.tenant_id,
        ingredients_data=[item.model_dump() for item in body.ingredientes],
    )
    return {"data": data}


@router.put("/{product_id}/badges")
async def set_product_badges(
    product_id: int,
    body: ProductBadgeSet,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductExtendedService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/products/{id}/badges — replace all badge associations."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.set_badges(
        product_id=product_id,
        tenant_id=ctx.tenant_id,
        badge_data=[item.model_dump() for item in body.badges],
    )
    return {"data": data}


@router.put("/{product_id}/seals")
async def set_product_seals(
    product_id: int,
    body: ProductSealSet,
    user: dict[str, Any] = Depends(get_current_user),
    service: ProductExtendedService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/products/{id}/seals — replace all seal associations."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.set_seals(
        product_id=product_id,
        tenant_id=ctx.tenant_id,
        seal_data=[item.model_dump() for item in body.seals],
    )
    return {"data": data}
