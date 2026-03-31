"""Table repository — branch-scoped data access for tables via sector join."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.room.sector import Sector
from shared.models.room.table import Table
from shared.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class TableRepository(BaseRepository[Table]):
    """Repository for tables, scoped to a branch through the sector relationship.

    Table has ``sector_id`` but no ``branch_id`` directly. We join through
    Sector to enforce branch-level isolation on every query.
    """

    def __init__(self, session: AsyncSession, branch_id: int) -> None:
        if branch_id is None:
            raise ValueError("branch_id is required for TableRepository")
        super().__init__(session)
        self.branch_id = branch_id

    def _base_query(self, include_deleted: bool = False):
        """Base query scoped to branch via sector join."""
        stmt = super()._base_query(include_deleted)
        stmt = stmt.join(Sector, Table.sector_id == Sector.id).where(
            Sector.branch_id == self.branch_id
        )
        return stmt

    # ── Read helpers ────────────────────────────────────────────────────

    async def get_by_branch(
        self,
        sector_id: int | None = None,
        status: str | None = None,
    ) -> list[Table]:
        """Return tables for the branch with optional sector/status filters."""
        stmt = self._base_query()
        if sector_id is not None:
            stmt = stmt.where(Table.sector_id == sector_id)
        if status is not None:
            stmt = stmt.where(Table.status == status)
        stmt = stmt.order_by(Table.sector_id, Table.number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_update(self, table_id: int) -> Table | None:
        """Fetch a single table with row-level lock for status transitions."""
        stmt = (
            self._base_query()
            .where(Table.id == table_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_max_number(self, sector_id: int) -> int | None:
        """Return the highest table number in a sector (active only)."""
        stmt = (
            select(func.max(Table.number))
            .where(
                Table.sector_id == sector_id,
                Table.is_active.is_(True),
                Table.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_existing_numbers(self, sector_id: int, numbers: list[int]) -> list[int]:
        """Return which of the given numbers already exist in the sector."""
        if not numbers:
            return []
        stmt = (
            select(Table.number)
            .where(
                Table.sector_id == sector_id,
                Table.number.in_(numbers),
                Table.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(self, tables: list[Table]) -> list[Table]:
        """Add multiple tables in a single flush + commit."""
        self.session.add_all(tables)
        from shared.infrastructure.db import safe_commit

        await safe_commit(self.session)
        for table in tables:
            await self.session.refresh(table)
        return tables

    async def get_by_sector_and_number(self, sector_id: int, number: int) -> Table | None:
        """Look up a specific table by sector and number (active only)."""
        stmt = (
            self._base_query()
            .where(Table.sector_id == sector_id, Table.number == number)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
