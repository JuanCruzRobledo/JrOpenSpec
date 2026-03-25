"""Tenant-scoped repository — all queries filtered by tenant_id."""

from __future__ import annotations

import logging
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from shared.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TenantRepository(BaseRepository[T]):
    """Repository that automatically scopes all queries to a single tenant.

    Usage::

        class CategoryRepository(TenantRepository[Category]):
            pass

        repo = CategoryRepository(session, tenant_id=1)
        categories = await repo.get_all()  # only tenant 1 categories
    """

    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id must not be None — TenantRepository requires a valid tenant_id")
        super().__init__(session)
        self.tenant_id = tenant_id

    def _base_query(self, include_deleted: bool = False):
        """Add tenant_id filter on top of base query."""
        stmt = super()._base_query(include_deleted)
        stmt = stmt.where(self.model.tenant_id == self.tenant_id)  # type: ignore[attr-defined]
        return stmt
