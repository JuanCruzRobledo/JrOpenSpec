"""Centralized cache invalidation hooks — called from service layer after writes.

No FastAPI imports. Pure Python + CacheService dependency.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.core.branch import Branch
from rest_api.app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class CacheInvalidator:
    """Invalidates public API cache entries when data changes."""

    def __init__(self, cache: CacheService, db: AsyncSession) -> None:
        self._cache = cache
        self._db = db

    async def _get_branch_slugs_for_tenant(self, tenant_id: int) -> list[str]:
        """Fetch all branch slugs for a tenant."""
        result = await self._db.execute(
            select(Branch.slug).where(
                Branch.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def _get_tenant_slug(self, tenant_id: int) -> str | None:
        """Fetch tenant slug from a branch belonging to that tenant."""
        from shared.models.core.tenant import Tenant

        result = await self._db.execute(
            select(Tenant.slug).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def on_product_change(self, product_id: int, tenant_id: int) -> None:
        """Invalidate menu and product caches when a product changes."""
        slugs = await self._get_branch_slugs_for_tenant(tenant_id)
        for slug in slugs:
            await self._cache.invalidate_pattern(f"cache:public:menu:{slug}*")
            await self._cache.invalidate_keys(f"cache:public:product:{slug}:{product_id}")

    async def on_branch_change(self, branch_slug: str, tenant_id: int) -> None:
        """Invalidate branch and menu caches when a branch changes."""
        tenant_slug = await self._get_tenant_slug(tenant_id)
        await self._cache.invalidate_pattern(f"cache:public:menu:{branch_slug}*")
        if tenant_slug:
            await self._cache.invalidate_keys(f"cache:public:branches:{tenant_slug}")

    async def on_allergen_change(self, tenant_id: int) -> None:
        """Invalidate allergen catalog and menu caches."""
        tenant_slug = await self._get_tenant_slug(tenant_id)
        if tenant_slug:
            await self._cache.invalidate_keys(f"cache:public:allergens:{tenant_slug}")
        slugs = await self._get_branch_slugs_for_tenant(tenant_id)
        for slug in slugs:
            await self._cache.invalidate_pattern(f"cache:public:menu:{slug}*")

    async def on_branch_product_change(self, branch_slug: str) -> None:
        """Invalidate menu and product caches for a branch."""
        await self._cache.invalidate_pattern(f"cache:public:menu:{branch_slug}*")
        await self._cache.invalidate_pattern(f"cache:public:product:{branch_slug}:*")

    async def on_badge_or_seal_change(self, tenant_id: int) -> None:
        """Invalidate menu caches for all branches of tenant."""
        slugs = await self._get_branch_slugs_for_tenant(tenant_id)
        for slug in slugs:
            await self._cache.invalidate_pattern(f"cache:public:menu:{slug}*")
