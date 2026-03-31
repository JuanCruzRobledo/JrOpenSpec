"""Assignment repository — data access for waiter-sector assignments."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.infrastructure.db import safe_commit
from shared.models.services.waiter_sector_assignment import WaiterSectorAssignment
from shared.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AssignmentRepository(BaseRepository[WaiterSectorAssignment]):
    """Repository for waiter-sector assignments."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # ── Read helpers ────────────────────────────────────────────────────

    async def get_by_date(
        self, branch_id: int, date_: date
    ) -> list[WaiterSectorAssignment]:
        """Get all assignments for a branch on a given date, eagerly loading user and sector."""
        stmt = (
            self._base_query()
            .where(
                WaiterSectorAssignment.branch_id == branch_id,
                WaiterSectorAssignment.date == date_,
                WaiterSectorAssignment.deleted_at.is_(None),
            )
            .options(
                selectinload(WaiterSectorAssignment.user),
                selectinload(WaiterSectorAssignment.sector),
            )
            .order_by(WaiterSectorAssignment.shift, WaiterSectorAssignment.sector_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_waiter_date(
        self, waiter_id: int, date_: date
    ) -> list[WaiterSectorAssignment]:
        """Get assignments for a specific waiter on a date."""
        stmt = (
            self._base_query()
            .where(
                WaiterSectorAssignment.user_id == waiter_id,
                WaiterSectorAssignment.date == date_,
                WaiterSectorAssignment.deleted_at.is_(None),
            )
            .options(
                selectinload(WaiterSectorAssignment.user),
                selectinload(WaiterSectorAssignment.sector),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def has_active_assignments(self, waiter_id: int, date_: date) -> bool:
        """Check if a waiter has any active assignments for the given date."""
        stmt = select(
            exists().where(
                WaiterSectorAssignment.user_id == waiter_id,
                WaiterSectorAssignment.date == date_,
                WaiterSectorAssignment.is_active.is_(True),
                WaiterSectorAssignment.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or False

    # ── Write helpers ───────────────────────────────────────────────────

    async def delete_by_date_shift(
        self, branch_id: int, date_: date, shift: str
    ) -> int:
        """Hard-delete all assignments for a date+shift in a branch.

        Uses actual DELETE (not soft-delete) because bulk_save
        replaces the entire set for the date+shift.
        """
        stmt = (
            delete(WaiterSectorAssignment)
            .where(
                WaiterSectorAssignment.branch_id == branch_id,
                WaiterSectorAssignment.date == date_,
                WaiterSectorAssignment.shift == shift,
            )
            .returning(func.count())
        )
        # Use a simple count approach
        count_stmt = select(func.count(WaiterSectorAssignment.id)).where(
            WaiterSectorAssignment.branch_id == branch_id,
            WaiterSectorAssignment.date == date_,
            WaiterSectorAssignment.shift == shift,
        )
        count_result = await self.session.execute(count_stmt)
        count = count_result.scalar() or 0

        delete_stmt = delete(WaiterSectorAssignment).where(
            WaiterSectorAssignment.branch_id == branch_id,
            WaiterSectorAssignment.date == date_,
            WaiterSectorAssignment.shift == shift,
        )
        await self.session.execute(delete_stmt)
        await safe_commit(self.session)

        logger.info(
            "Deleted %d assignments: branch=%d date=%s shift=%s",
            count, branch_id, date_, shift,
        )
        return count

    async def bulk_create(
        self, assignments: list[WaiterSectorAssignment]
    ) -> list[WaiterSectorAssignment]:
        """Add multiple assignments and commit."""
        self.session.add_all(assignments)
        await safe_commit(self.session)
        for a in assignments:
            await self.session.refresh(a)
        return assignments
