"""CookingMethod service — CRUD with system protection and tenant scoping.

Pure business logic — no FastAPI imports.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import ForbiddenError, NotFoundError
from shared.infrastructure.db import safe_commit
from shared.models.profiles.cooking_method import CookingMethod

logger = logging.getLogger(__name__)


def _to_dict(cm: CookingMethod) -> dict:
    return {
        "id": cm.id,
        "codigo": cm.code,
        "nombre": cm.name,
        "icono": cm.icon,
        "es_sistema": cm.is_system,
        "created_at": cm.created_at.isoformat() if cm.created_at else "",
        "updated_at": cm.updated_at.isoformat() if cm.updated_at else "",
    }


class CookingMethodService:
    """Business logic for cooking method management."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_query(self, tenant_id: int):
        return select(CookingMethod).where(
            or_(CookingMethod.tenant_id.is_(None), CookingMethod.tenant_id == tenant_id),
            CookingMethod.deleted_at.is_(None),
        )

    async def list(
        self, tenant_id: int, page: int = 1, limit: int = 20, search: str | None = None,
    ) -> tuple[list[dict], int]:
        base = self._base_query(tenant_id)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(CookingMethod.name.ilike(pattern), CookingMethod.code.ilike(pattern))
            )

        total = (await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar() or 0

        offset = (page - 1) * limit
        result = await self._db.execute(
            base.order_by(CookingMethod.is_system.desc(), CookingMethod.name)
            .offset(offset).limit(limit)
        )
        return [_to_dict(cm) for cm in result.scalars().all()], total

    async def get_by_id(self, method_id: int, tenant_id: int) -> dict:
        cm = await self._fetch(method_id, tenant_id)
        return _to_dict(cm)

    async def create(self, tenant_id: int, data: dict) -> dict:
        cm = CookingMethod(
            code=data["codigo"],
            name=data["nombre"],
            icon=data.get("icono"),
            is_system=False,
            tenant_id=tenant_id,
        )
        self._db.add(cm)
        await safe_commit(self._db)
        await self._db.refresh(cm)
        return _to_dict(cm)

    async def update(self, method_id: int, tenant_id: int, data: dict) -> dict:
        cm = await self._fetch(method_id, tenant_id)
        self._check_not_system(cm)

        if "nombre" in data and data["nombre"] is not None:
            cm.name = data["nombre"]
        if "icono" in data:
            cm.icon = data["icono"]

        await safe_commit(self._db)
        await self._db.refresh(cm)
        return _to_dict(cm)

    async def delete(self, method_id: int, tenant_id: int, user_id: int) -> dict:
        cm = await self._fetch(method_id, tenant_id)
        self._check_not_system(cm)
        cm.soft_delete(user_id)
        await safe_commit(self._db)
        return {"message": "Metodo de coccion eliminado"}

    async def _fetch(self, method_id: int, tenant_id: int) -> CookingMethod:
        result = await self._db.execute(
            self._base_query(tenant_id).where(CookingMethod.id == method_id)
        )
        cm = result.scalar_one_or_none()
        if cm is None:
            raise NotFoundError(message="Metodo de coccion no encontrado")
        return cm

    @staticmethod
    def _check_not_system(cm: CookingMethod) -> None:
        if cm.is_system:
            raise ForbiddenError(message="No se puede modificar un metodo de coccion del sistema")
