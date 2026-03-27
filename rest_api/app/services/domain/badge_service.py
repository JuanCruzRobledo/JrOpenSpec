"""Badge service — CRUD with system protection and tenant scoping.

Pure business logic — no FastAPI imports.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import ForbiddenError, NotFoundError
from shared.infrastructure.db import safe_commit
from shared.models.marketing.badge import Badge

logger = logging.getLogger(__name__)


def _to_dict(b: Badge) -> dict:
    return {
        "id": b.id,
        "codigo": b.code,
        "nombre": b.name,
        "color": b.color,
        "icono": b.icon,
        "es_sistema": b.is_system,
        "created_at": b.created_at.isoformat() if b.created_at else "",
        "updated_at": b.updated_at.isoformat() if b.updated_at else "",
    }


class BadgeService:
    """Business logic for badge management."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_query(self, tenant_id: int):
        return select(Badge).where(
            or_(Badge.tenant_id.is_(None), Badge.tenant_id == tenant_id),
            Badge.deleted_at.is_(None),
        )

    async def list(
        self, tenant_id: int, page: int = 1, limit: int = 20, search: str | None = None,
    ) -> tuple[list[dict], int]:
        base = self._base_query(tenant_id)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(Badge.name.ilike(pattern), Badge.code.ilike(pattern))
            )

        total = (await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar() or 0

        offset = (page - 1) * limit
        result = await self._db.execute(
            base.order_by(Badge.is_system.desc(), Badge.name)
            .offset(offset).limit(limit)
        )
        return [_to_dict(b) for b in result.scalars().all()], total

    async def get_by_id(self, badge_id: int, tenant_id: int) -> dict:
        b = await self._fetch(badge_id, tenant_id)
        return _to_dict(b)

    async def create(self, tenant_id: int, data: dict) -> dict:
        b = Badge(
            code=data["codigo"],
            name=data["nombre"],
            color=data["color"],
            icon=data.get("icono"),
            is_system=False,
            tenant_id=tenant_id,
        )
        self._db.add(b)
        await safe_commit(self._db)
        await self._db.refresh(b)
        return _to_dict(b)

    async def update(self, badge_id: int, tenant_id: int, data: dict) -> dict:
        b = await self._fetch(badge_id, tenant_id)
        self._check_not_system(b)

        if "nombre" in data and data["nombre"] is not None:
            b.name = data["nombre"]
        if "color" in data and data["color"] is not None:
            b.color = data["color"]
        if "icono" in data:
            b.icon = data["icono"]

        await safe_commit(self._db)
        await self._db.refresh(b)
        return _to_dict(b)

    async def delete(self, badge_id: int, tenant_id: int, user_id: int) -> dict:
        b = await self._fetch(badge_id, tenant_id)
        self._check_not_system(b)
        b.soft_delete(user_id)
        await safe_commit(self._db)
        return {"message": "Insignia eliminada"}

    async def _fetch(self, badge_id: int, tenant_id: int) -> Badge:
        result = await self._db.execute(
            self._base_query(tenant_id).where(Badge.id == badge_id)
        )
        b = result.scalar_one_or_none()
        if b is None:
            raise NotFoundError(message="Insignia no encontrada")
        return b

    @staticmethod
    def _check_not_system(b: Badge) -> None:
        if b.is_system:
            raise ForbiddenError(message="No se puede modificar una insignia del sistema")
