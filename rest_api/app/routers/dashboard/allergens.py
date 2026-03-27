"""Allergen dashboard router — CRUD + cross-reactions.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.allergen import (
    AllergenCreate,
    AllergenRead,
    AllergenUpdate,
    CrossReactionCreate,
    CrossReactionRead,
)
from rest_api.app.schemas.envelope import ListResponse, SingleResponse
from rest_api.app.services.domain.allergen_service import AllergenService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/allergens", tags=["allergens"])


def _get_service(db: AsyncSession = Depends(get_db)) -> AllergenService:
    return AllergenService(db)


@router.get("/", response_model=ListResponse[AllergenRead])
async def list_allergens(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    user: dict[str, Any] = Depends(get_current_user),
    service: AllergenService = Depends(_get_service),
) -> dict:
    """GET /api/dashboard/allergens."""
    ctx = PermissionContext(user)
    ctx.require_management()

    items, total = await service.list(
        tenant_id=ctx.tenant_id, page=page, limit=limit, search=search,
    )
    return {"data": items, "meta": {"page": page, "limit": limit, "total": total}}


@router.get("/{allergen_id}", response_model=SingleResponse[AllergenRead])
async def get_allergen(
    allergen_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: AllergenService = Depends(_get_service),
) -> dict:
    """GET /api/dashboard/allergens/{id}."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.get_by_id(allergen_id, tenant_id=ctx.tenant_id)
    return {"data": data}


@router.post("/", response_model=SingleResponse[AllergenRead], status_code=status.HTTP_201_CREATED)
async def create_allergen(
    body: AllergenCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: AllergenService = Depends(_get_service),
) -> dict:
    """POST /api/dashboard/allergens."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.create(
        tenant_id=ctx.tenant_id,
        data=body.model_dump(exclude_unset=True),
    )
    return {"data": data}


@router.put("/{allergen_id}", response_model=SingleResponse[AllergenRead])
async def update_allergen(
    allergen_id: int,
    body: AllergenUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: AllergenService = Depends(_get_service),
) -> dict:
    """PUT /api/dashboard/allergens/{id}."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.update(
        allergen_id=allergen_id,
        tenant_id=ctx.tenant_id,
        data=body.model_dump(exclude_unset=True),
    )
    return {"data": data}


@router.delete("/{allergen_id}")
async def delete_allergen(
    allergen_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: AllergenService = Depends(_get_service),
) -> dict:
    """DELETE /api/dashboard/allergens/{id}."""
    ctx = PermissionContext(user)
    ctx.require_admin()

    return await service.delete(
        allergen_id=allergen_id,
        tenant_id=ctx.tenant_id,
        user_id=int(ctx.user_id),
    )


# ── Cross-reactions ──


@router.get("/{allergen_id}/cross-reactions", response_model=SingleResponse[list[CrossReactionRead]])
async def list_cross_reactions(
    allergen_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: AllergenService = Depends(_get_service),
) -> dict:
    """GET /api/dashboard/allergens/{id}/cross-reactions."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.list_cross_reactions(allergen_id, tenant_id=ctx.tenant_id)
    return {"data": data}


@router.post(
    "/{allergen_id}/cross-reactions",
    response_model=SingleResponse[CrossReactionRead],
    status_code=status.HTTP_201_CREATED,
)
async def add_cross_reaction(
    allergen_id: int,
    body: CrossReactionCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: AllergenService = Depends(_get_service),
) -> dict:
    """POST /api/dashboard/allergens/{id}/cross-reactions."""
    ctx = PermissionContext(user)
    ctx.require_management()

    data = await service.add_cross_reaction(
        allergen_id=allergen_id,
        tenant_id=ctx.tenant_id,
        data=body.model_dump(),
    )
    return {"data": data}


@router.delete("/cross-reactions/{cross_reaction_id}")
async def remove_cross_reaction(
    cross_reaction_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: AllergenService = Depends(_get_service),
) -> dict:
    """DELETE /api/dashboard/allergens/cross-reactions/{id}."""
    ctx = PermissionContext(user)
    ctx.require_admin()

    return await service.remove_cross_reaction(cross_reaction_id)
