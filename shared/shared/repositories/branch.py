"""Branch-scoped repository — queries filtered by tenant_id AND branch_id."""

from __future__ import annotations

import logging
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from shared.repositories.tenant import TenantRepository

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BranchRepository(TenantRepository[T]):
    """Repository that scopes queries to a specific branch within a tenant.

    Usage::

        class BranchProductRepository(BranchRepository[BranchProduct]):
            pass

        repo = BranchProductRepository(session, tenant_id=1, branch_id=3)
        products = await repo.get_all()  # only branch 3 products
    """

    def __init__(self, session: AsyncSession, tenant_id: int, branch_id: int) -> None:
        if branch_id is None:
            raise ValueError("branch_id must not be None — BranchRepository requires a valid branch_id")
        super().__init__(session, tenant_id)
        self.branch_id = branch_id

    def _base_query(self, include_deleted: bool = False):
        """Add branch_id filter on top of tenant query."""
        stmt = super()._base_query(include_deleted)
        stmt = stmt.where(self.model.branch_id == self.branch_id)  # type: ignore[attr-defined]
        return stmt
