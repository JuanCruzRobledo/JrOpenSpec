"""Staff repository — tenant-scoped data access for users (staff members)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import String, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
from shared.repositories.tenant import TenantRepository

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StaffRepository(TenantRepository[User]):
    """Repository for staff (users), scoped to a tenant."""

    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        super().__init__(session, tenant_id)

    # ── Read helpers ────────────────────────────────────────────────────

    async def search(
        self,
        q: str | None = None,
        role: str | None = None,
        is_active: bool = True,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """Search staff with optional text filter, role filter, and pagination.

        Returns (users, total_count).
        """
        include_deleted = not is_active
        stmt = self._base_query(include_deleted=include_deleted)

        # Eager-load branch_roles for the dict conversion
        stmt = stmt.options(selectinload(User.branch_roles))

        # Text search on full name and email
        if q:
            pattern = f"%{q}%"
            full_name = func.concat(User.first_name, " ", User.last_name)
            stmt = stmt.where(
                or_(
                    full_name.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )

        # Role filter via JOIN on UserBranchRole
        if role:
            stmt = stmt.join(User.branch_roles).where(
                UserBranchRole.role == role
            )

        # Count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Order and paginate
        offset = (page - 1) * limit
        stmt = stmt.order_by(User.last_name, User.first_name).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        users = list(result.scalars().unique().all())

        return users, total

    async def get_by_email(self, email: str) -> User | None:
        """Exact email match within the tenant."""
        stmt = self._base_query().where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_waiters(self, is_active: bool = True) -> list[User]:
        """Get users who have at least one WAITER role in any branch."""
        include_deleted = not is_active
        stmt = (
            self._base_query(include_deleted=include_deleted)
            .join(User.branch_roles)
            .where(UserBranchRole.role == "WAITER")
            .options(selectinload(User.branch_roles))
            .order_by(User.last_name, User.first_name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())
