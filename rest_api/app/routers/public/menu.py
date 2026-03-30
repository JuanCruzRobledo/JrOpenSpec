"""Public menu router — no auth required.

GET /api/public/menu/{slug} — full menu for a branch
GET /api/public/menu/{slug}/product/{id} — product detail
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

router = APIRouter(prefix="/menu", tags=["public-menu"])

CACHE_CONTROL = "public, max-age=300"


def _get_service(
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
) -> PublicMenuService:
    cache = CacheService(redis_client)
    return PublicMenuService(db, cache)


@router.get("/{slug}")
@limiter.limit("60/minute")
async def get_menu(
    request: Request,
    slug: str,
    dietary: str | None = Query(None, description="Comma-separated dietary profile codes"),
    allergen_free: str | None = Query(None, description="Comma-separated allergen codes to exclude"),
    service: PublicMenuService = Depends(_get_service),
) -> JSONResponse:
    """GET /api/public/menu/{slug} — full menu for a branch."""
    dietary_list = [d.strip() for d in dietary.split(",") if d.strip()] if dietary else None
    allergen_free_list = [a.strip() for a in allergen_free.split(",") if a.strip()] if allergen_free else None

    data = await service.get_menu(slug, dietary_list, allergen_free_list)
    return JSONResponse(content=data, headers={"Cache-Control": CACHE_CONTROL})


@router.get("/{slug}/product/{product_id}")
@limiter.limit("60/minute")
async def get_product_detail(
    request: Request,
    slug: str,
    product_id: int,
    service: PublicMenuService = Depends(_get_service),
) -> JSONResponse:
    """GET /api/public/menu/{slug}/product/{id} — full product detail."""
    data = await service.get_product(slug, product_id)
    return JSONResponse(content=data, headers={"Cache-Control": CACHE_CONTROL})
