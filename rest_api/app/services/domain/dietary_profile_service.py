"""DietaryProfile service — CRUD with system protection and tenant scoping.

Pure business logic — no FastAPI imports.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import ForbiddenError, NotFoundError
from shared.infrastructure.db import safe_commit
from shared.models.catalog.dietary_profile import DietaryProfile

logger = logging.getLogger(__name__)


def _to_dict(dp: DietaryProfile) -> dict:
    return {
        "id": dp.id,
        "codigo": dp.code,
        "nombre": dp.name,
        "descripcion": dp.description,
        "icono": dp.icon,
        "es_sistema": dp.is_system,
        "created_at": dp.created_at.isoformat() if dp.created_at else "",
        "updated_at": dp.updated_at.isoformat() if dp.updated_at else "",
    }


class DietaryProfileService:
    """Business logic for dietary profile management."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_query(self, tenant_id: int):
        return select(DietaryProfile).where(
            or_(DietaryProfile.tenant_id.is_(None), DietaryProfile.tenant_id == tenant_id),
            DietaryProfile.deleted_at.is_(None),
        )

    async def list(
        self, tenant_id: int, page: int = 1, limit: int = 20, search: str | None = None,
    ) -> tuple[list[dict], int]:
        base = self._base_query(tenant_id)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(DietaryProfile.name.ilike(pattern), DietaryProfile.code.ilike(pattern))
            )

        total = (await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar() or 0

        offset = (page - 1) * limit
        result = await self._db.execute(
            base.order_by(DietaryProfile.is_system.desc(), DietaryProfile.name)
            .offset(offset).limit(limit)
        )
        return [_to_dict(dp) for dp in result.scalars().all()], total

    async def get_by_id(self, profile_id: int, tenant_id: int) -> dict:
        dp = await self._fetch(profile_id, tenant_id)
        return _to_dict(dp)

    async def create(self, tenant_id: int, data: dict) -> dict:
        dp = DietaryProfile(
            code=data["codigo"],
            name=data["nombre"],
            description=data.get("descripcion"),
            icon=data.get("icono"),
            is_system=False,
            tenant_id=tenant_id,
        )
        self._db.add(dp)
        await safe_commit(self._db)
        await self._db.refresh(dp)
        return _to_dict(dp)

    async def update(self, profile_id: int, tenant_id: int, data: dict) -> dict:
        dp = await self._fetch(profile_id, tenant_id)
        self._check_not_system(dp)

        if "nombre" in data and data["nombre"] is not None:
            dp.name = data["nombre"]
        if "descripcion" in data:
            dp.description = data["descripcion"]
        if "icono" in data:
            dp.icon = data["icono"]

        await safe_commit(self._db)
        await self._db.refresh(dp)
        return _to_dict(dp)

    async def delete(self, profile_id: int, tenant_id: int, user_id: int) -> dict:
        dp = await self._fetch(profile_id, tenant_id)
        self._check_not_system(dp)
        dp.soft_delete(user_id)
        await safe_commit(self._db)
        return {"message": "Perfil dietetico eliminado"}

    async def _fetch(self, profile_id: int, tenant_id: int) -> DietaryProfile:
        result = await self._db.execute(
            self._base_query(tenant_id).where(DietaryProfile.id == profile_id)
        )
        dp = result.scalar_one_or_none()
        if dp is None:
            raise NotFoundError(message="Perfil dietetico no encontrado")
        return dp

    @staticmethod
    def _check_not_system(dp: DietaryProfile) -> None:
        if dp.is_system:
            raise ForbiddenError(message="No se puede modificar un perfil dietetico del sistema")
