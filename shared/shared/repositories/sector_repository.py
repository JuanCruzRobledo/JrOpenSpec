"""Sector repository — branch-scoped data access for sectors."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.room.sector import Sector
from shared.models.room.table import Table
from shared.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class SectorRepository(BaseRepository[Sector]):
    """Repository for sectors, manually scoped to a branch.

    Sector has ``branch_id`` but no ``tenant_id``, so it cannot use
    ``BranchRepository`` which expects both columns on the model.
    """

    def __init__(self, session: AsyncSession, branch_id: int) -> None:
        if branch_id is None:
            raise ValueError("branch_id is required for SectorRepository")
        super().__init__(session)
        self.branch_id = branch_id

    def _base_query(self, include_deleted: bool = False):
        """Base query scoped to branch_id."""
        stmt = super()._base_query(include_deleted)
        stmt = stmt.where(Sector.branch_id == self.branch_id)
        return stmt

    # ── Read helpers ────────────────────────────────────────────────────

    async def get_by_branch(self, include_inactive: bool = False) -> list[Sector]:
        """Return all sectors for the branch, ordered by type then name."""
        stmt = self._base_query(include_deleted=include_inactive).order_by(
            Sector.type, Sector.name
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Sector | None:
        """Case-insensitive name lookup within the branch."""
        stmt = self._base_query().where(func.lower(Sector.name) == name.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_prefix(self, prefix: str) -> Sector | None:
        """Exact prefix lookup within the branch (active only)."""
        stmt = self._base_query().where(Sector.prefix == prefix)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_active_tables(self, sector_id: int) -> int:
        """Count active, non-deleted tables belonging to a sector."""
        stmt = (
            select(func.count(Table.id))
            .where(
                Table.sector_id == sector_id,
                Table.is_active.is_(True),
                Table.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
