"""TableSession repository — data access for table session history."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.room.table_session import TableSession
from shared.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class TableSessionRepository(BaseRepository[TableSession]):
    """Repository for table sessions (historical records of table occupancy)."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # ── Read helpers ────────────────────────────────────────────────────

    async def get_by_table(self, table_id: int, limit: int = 50) -> list[TableSession]:
        """Return sessions for a table, most recent first."""
        stmt = (
            self._base_query()
            .where(TableSession.table_id == table_id)
            .order_by(TableSession.closed_at.desc().nulls_last())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
