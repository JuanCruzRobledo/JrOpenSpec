"""Table router — CRUD + FSM endpoints nested under /api/v1/branches/{branch_id}/tables.

Thin handlers: Depends + PermissionContext + service call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.dependencies import get_current_user
from rest_api.app.schemas.envelope import ListResponse, SingleResponse
from rest_api.app.schemas.table import (
    TableBatchCreate,
    TableBatchCreateResponse,
    TableCreate,
    TableDeleteResponse,
    TableRead,
    TableStatusUpdate,
    TableUpdate,
)
from rest_api.app.services.domain.table_service import TableService
from rest_api.app.services.permissions.context import PermissionContext
from rest_api.app.services.permissions.strategies import Action
from shared.infrastructure.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/branches/{branch_id}/tables",
    tags=["tables"],
)


def _get_service(db: AsyncSession = Depends(get_db)) -> TableService:
    return TableService(db)


@router.get("/", response_model=ListResponse[TableRead])
async def list_tables(
    branch_id: int,
    sector_id: int | None = Query(None),
    estado: str | None = Query(None, alias="status"),
    user: dict[str, Any] = Depends(get_current_user),
    service: TableService = Depends(_get_service),
) -> dict:
    """GET /api/v1/branches/{branch_id}/tables?sector_id=&status=."""
    ctx = PermissionContext(user)
    ctx.require_can(Action.READ, "Table")
    ctx.require_branch_access(branch_id)

    items = await service.list_tables(
        branch_id=branch_id,
        sector_id=sector_id,
        status=estado,
    )
    return {
        "data": items,
        "meta": {"page": 1, "limit": len(items), "total": len(items)},
    }


@router.post("/", response_model=SingleResponse[TableRead], status_code=status.HTTP_201_CREATED)
async def create_table(
    branch_id: int,
    body: TableCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: TableService = Depends(_get_service),
) -> dict:
    """POST /api/v1/branches/{branch_id}/tables."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.create_table(
        branch_id=branch_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.post("/batch", response_model=SingleResponse[TableBatchCreateResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_tables(
    branch_id: int,
    body: TableBatchCreate,
    user: dict[str, Any] = Depends(get_current_user),
    service: TableService = Depends(_get_service),
) -> dict:
    """POST /api/v1/branches/{branch_id}/tables/batch."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.batch_create(
        branch_id=branch_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.put("/{table_id}", response_model=SingleResponse[TableRead])
async def update_table(
    branch_id: int,
    table_id: int,
    body: TableUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: TableService = Depends(_get_service),
) -> dict:
    """PUT /api/v1/branches/{branch_id}/tables/{table_id}."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.update_table(
        table_id=table_id,
        branch_id=branch_id,
        data=body.model_dump(exclude_unset=True),
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.delete("/{table_id}", response_model=SingleResponse[TableDeleteResponse])
async def delete_table(
    branch_id: int,
    table_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    service: TableService = Depends(_get_service),
) -> dict:
    """DELETE /api/v1/branches/{branch_id}/tables/{table_id}."""
    ctx = PermissionContext(user)
    ctx.require_management()
    ctx.require_branch_access(branch_id)

    data = await service.delete_table(
        table_id=table_id,
        branch_id=branch_id,
        user_id=int(ctx.user_id),
    )
    return {"data": data}


@router.patch("/{table_id}/status", response_model=SingleResponse[TableRead])
async def transition_table_status(
    branch_id: int,
    table_id: int,
    body: TableStatusUpdate,
    user: dict[str, Any] = Depends(get_current_user),
    service: TableService = Depends(_get_service),
) -> dict:
    """PATCH /api/v1/branches/{branch_id}/tables/{table_id}/status."""
    ctx = PermissionContext(user)
    ctx.require_can(Action.EDIT, "Table")
    ctx.require_branch_access(branch_id)

    data = await service.transition_status(
        table_id=table_id,
        branch_id=branch_id,
        new_status=body.estado,
        version=body.version,
        user_id=int(ctx.user_id),
    )
    return {"data": data}
