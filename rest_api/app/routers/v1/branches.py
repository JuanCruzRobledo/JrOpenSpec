"""Branch router — CRUD endpoints under /api/v1/branches.

Thin handlers: Depends + PermissionContext + service call.
RBAC: ADMIN = full CRUD, MANAGER = list + update (their branches).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.branch import (
    BranchCreate,
    BranchRead,
    BranchUpdate,
    DeleteCascadeResponse,
)
from rest_api.app.schemas.envelope import ListResponse, PaginationMeta, SingleResponse
from rest_api.app.services.domain.branch_service import BranchService
from rest_api.app.services.permissions.context import PermissionContext
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/branches", tags=["branches"])


def _get_service(db: AsyncSession = Depends(get_db)) -> BranchService:
    return BranchService(db)


@router.get("/", response_model=ListResponse[BranchRead])
async def list_branches(
    page: int = 1,
    limit: int = 10,
    user: dict[str, Any] = Depends(get_current_user),
    service: BranchService = Depends(_get_service),
) -> dict:
    """GET /api/v1/branches?page=1&limit=10."""
    ctx = PermissionContext(user)
    ctx.require_management()

    # MANAGER sees only their assigned branches; ADMIN sees all
    branch_ids = None if ctx.is_superadmin or "ADMIN" in ctx.roles else ctx.branch_ids

    items, total = await service.list(
        tenant_id=ctx.tenant_id,
        page=page,
        limit=limit,
        branch_ids=branch_ids,
    )
    return {
        "data": items,
        "meta": {"page": page, "limit": limit, "total": total},
    }


@router.post("/", response_model=SingleResponse[BranchRead], status_code=status.HTTP_201_CREATED)
async def create_branch(
    body: BranchCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: BranchService = Depends(_get_service),
) -> dict:
    """POST /api/v1/branches — create branch + auto-create General category."""
    ctx = PermissionContext(user)
    ctx.require_admin()

    data = await service.create(
        tenant_id=ctx.tenant_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.put("/{branch_id}", response_model=SingleResponse[BranchRead])
async def update_branch(
    branch_id: int,
    body: BranchUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: BranchService = Depends(_get_service),
) -> dict:
    """PUT /api/v1/branches/{id}."""
    ctx = PermissionContext(user)
    ctx.require_management()

    # MANAGER can only update their assigned branches
    if "ADMIN" not in ctx.roles and not ctx.is_superadmin:
        ctx.require_branch_access(branch_id)

    data = await service.update(
        branch_id=branch_id,
        tenant_id=ctx.tenant_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.delete("/{branch_id}", response_model=SingleResponse[DeleteCascadeResponse])
async def delete_branch(
    branch_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: BranchService = Depends(_get_service),
) -> dict:
    """DELETE /api/v1/branches/{id} — soft delete with cascade counts."""
    ctx = PermissionContext(user)
    ctx.require_admin()

    data = await service.delete(
        branch_id=branch_id,
        tenant_id=ctx.tenant_id,
        user_id=int(ctx.user_id),
    )
    return {"data": data}
