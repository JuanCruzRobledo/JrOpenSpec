"""Public allergens router — no auth required.

GET /api/public/allergens?tenant={slug}
"""

from __future__ import annotations

import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from rest_api.app.middleware.rate_limit import limiter
from rest_api.app.services.cache_service import CacheService
from rest_api.app.services.domain.public_menu_service import PublicMenuService
from shared.infrastructure.db import get_db
from shared.infrastructure.redis import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/allergens", tags=["public-allergens"])

CACHE_CONTROL = "public, max-age=300"


def _get_service(
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
) -> PublicMenuService:
    cache = CacheService(redis_client)
    return PublicMenuService(db, cache)


@router.get("/")
@limiter.limit("60/minute")
async def get_allergens(
    request: Request,
    tenant: str = Query(..., description="Tenant slug"),
    service: PublicMenuService = Depends(_get_service),
) -> JSONResponse:
    """GET /api/public/allergens?tenant={slug} — allergen catalog with cross-reactions."""
    data = await service.get_allergens(tenant)
    return JSONResponse(content=data, headers={"Cache-Control": CACHE_CONTROL})
