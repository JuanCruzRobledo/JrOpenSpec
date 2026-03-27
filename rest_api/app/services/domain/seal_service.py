"""Seal service — CRUD with system protection and tenant scoping.

Pure business logic — no FastAPI imports.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import ForbiddenError, NotFoundError
from shared.infrastructure.db import safe_commit
from shared.models.marketing.seal import Seal

logger = logging.getLogger(__name__)


def _to_dict(s: Seal) -> dict:
    return {
        "id": s.id,
        "codigo": s.code,
        "nombre": s.name,
        "color": s.color,
        "icono": s.icon,
        "descripcion": s.description,
        "es_sistema": s.is_system,
        "created_at": s.created_at.isoformat() if s.created_at else "",
        "updated_at": s.updated_at.isoformat() if s.updated_at else "",
    }


class SealService:
    """Business logic for seal management."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_query(self, tenant_id: int):
        return select(Seal).where(
            or_(Seal.tenant_id.is_(None), Seal.tenant_id == tenant_id),
            Seal.deleted_at.is_(None),
        )

    async def list(
        self, tenant_id: int, page: int = 1, limit: int = 20, search: str | None = None,
    ) -> tuple[list[dict], int]:
        base = self._base_query(tenant_id)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(Seal.name.ilike(pattern), Seal.code.ilike(pattern))
            )

        total = (await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar() or 0

        offset = (page - 1) * limit
        result = await self._db.execute(
            base.order_by(Seal.is_system.desc(), Seal.name)
            .offset(offset).limit(limit)
        )
        return [_to_dict(s) for s in result.scalars().all()], total

    async def get_by_id(self, seal_id: int, tenant_id: int) -> dict:
        s = await self._fetch(seal_id, tenant_id)
        return _to_dict(s)

    async def create(self, tenant_id: int, data: dict) -> dict:
        s = Seal(
            code=data["codigo"],
            name=data["nombre"],
            color=data["color"],
            icon=data.get("icono"),
            description=data.get("descripcion"),
            is_system=False,
            tenant_id=tenant_id,
        )
        self._db.add(s)
        await safe_commit(self._db)
        await self._db.refresh(s)
        return _to_dict(s)

    async def update(self, seal_id: int, tenant_id: int, data: dict) -> dict:
        s = await self._fetch(seal_id, tenant_id)
        self._check_not_system(s)

        if "nombre" in data and data["nombre"] is not None:
            s.name = data["nombre"]
        if "color" in data and data["color"] is not None:
            s.color = data["color"]
        if "icono" in data:
            s.icon = data["icono"]
        if "descripcion" in data:
            s.description = data["descripcion"]

        await safe_commit(self._db)
        await self._db.refresh(s)
        return _to_dict(s)

    async def delete(self, seal_id: int, tenant_id: int, user_id: int) -> dict:
        s = await self._fetch(seal_id, tenant_id)
        self._check_not_system(s)
        s.soft_delete(user_id)
        await safe_commit(self._db)
        return {"message": "Sello eliminado"}

    async def _fetch(self, seal_id: int, tenant_id: int) -> Seal:
        result = await self._db.execute(
            self._base_query(tenant_id).where(Seal.id == seal_id)
        )
        s = result.scalar_one_or_none()
        if s is None:
            raise NotFoundError(message="Sello no encontrado")
        return s

    @staticmethod
    def _check_not_system(s: Seal) -> None:
        if s.is_system:
            raise ForbiddenError(message="No se puede modificar un sello del sistema")
