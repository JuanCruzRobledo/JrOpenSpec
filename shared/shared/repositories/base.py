"""Base repository with generic CRUD operations and soft-delete support."""

from __future__ import annotations

import logging
import types
from typing import get_args

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.infrastructure.db import safe_commit

logger = logging.getLogger(__name__)


class BaseRepository[T]:
    """Generic repository providing standard CRUD with soft-delete.

    Usage::

        class ProductRepository(BaseRepository[Product]):
            pass

        repo = ProductRepository(session)
        product = await repo.get_by_id(1)
    """

    model: type[T]

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Automatically resolve the model type from the generic parameter."""
        super().__init_subclass__(**kwargs)
        for base in types.get_original_bases(cls):
            args = get_args(base)
            if args and isinstance(args[0], type):
                cls.model = args[0]
                break

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Query building ──────────────────────────────────────────────────

    def _base_query(self, include_deleted: bool = False):
        """Return a base SELECT statement, filtering inactive by default."""
        stmt = select(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.is_active.is_(True))  # type: ignore[attr-defined]
        return stmt

    # ── Read ────────────────────────────────────────────────────────────

    async def get_by_id(self, id: int, include_deleted: bool = False) -> T | None:
        """Fetch a single entity by primary key."""
        stmt = self._base_query(include_deleted).where(self.model.id == id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[T]:
        """Fetch a paginated list of entities."""
        stmt = self._base_query(include_deleted).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Write ───────────────────────────────────────────────────────────

    async def create(self, entity: T) -> T:
        """Add a new entity and commit."""
        self.session.add(entity)
        await safe_commit(self.session)
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        """Commit pending changes on an already-tracked entity."""
        await safe_commit(self.session)
        await self.session.refresh(entity)
        return entity

    async def soft_delete(self, id: int, user_id: int | None = None) -> T:
        """Mark an entity as deleted (soft delete)."""
        entity = await self.get_by_id(id)
        if entity is None:
            from shared.exceptions import NotFoundError

            raise NotFoundError(f"{self.model.__name__} with id={id} not found")
        entity.soft_delete(user_id)  # type: ignore[attr-defined]
        await safe_commit(self.session)
        await self.session.refresh(entity)
        return entity

    async def restore(self, id: int) -> T:
        """Restore a soft-deleted entity."""
        entity = await self.get_by_id(id, include_deleted=True)
        if entity is None:
            from shared.exceptions import NotFoundError

            raise NotFoundError(f"{self.model.__name__} with id={id} not found")
        entity.restore()  # type: ignore[attr-defined]
        await safe_commit(self.session)
        await self.session.refresh(entity)
        return entity
