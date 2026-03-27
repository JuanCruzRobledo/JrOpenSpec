"""Allergen service — CRUD + cross-reactions with system protection and tenant scoping.

Pure business logic — no FastAPI imports.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.exceptions import ForbiddenError, NotFoundError, ValidationError
from shared.infrastructure.db import safe_commit
from shared.models.catalog.allergen import Allergen
from shared.models.catalog.allergen_cross_reaction import AllergenCrossReaction

logger = logging.getLogger(__name__)


def _allergen_to_dict(a: Allergen, cross_reactions: list[dict] | None = None) -> dict:
    """Map Allergen model to Spanish API dict."""
    return {
        "id": a.id,
        "codigo": a.code,
        "nombre": a.name,
        "descripcion": a.description,
        "icono": a.icon,
        "es_sistema": a.is_system,
        "reacciones_cruzadas": cross_reactions or [],
        "created_at": a.created_at.isoformat() if a.created_at else "",
        "updated_at": a.updated_at.isoformat() if a.updated_at else "",
    }


def _cross_reaction_to_dict(cr: AllergenCrossReaction, from_allergen_id: int) -> dict:
    """Map cross-reaction to dict, resolving the 'other' allergen direction."""
    if cr.allergen_id == from_allergen_id:
        related = cr.related_allergen
    else:
        related = cr.allergen
    return {
        "id": cr.id,
        "allergen_id": cr.allergen_id,
        "related_allergen_id": cr.related_allergen_id,
        "related_code": related.code if related else "",
        "related_name": related.name if related else "",
        "descripcion": cr.description,
        "severidad": cr.severity,
    }


class AllergenService:
    """Business logic for allergen management."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_query(self, tenant_id: int):
        """System allergens (tenant_id IS NULL) + tenant-specific, excluding soft-deleted."""
        return select(Allergen).where(
            or_(Allergen.tenant_id.is_(None), Allergen.tenant_id == tenant_id),
            Allergen.deleted_at.is_(None),
        )

    async def list(
        self,
        tenant_id: int,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
    ) -> tuple[list[dict], int]:
        """List allergens with pagination and optional search."""
        base = self._base_query(tenant_id)

        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(Allergen.name.ilike(pattern), Allergen.code.ilike(pattern))
            )

        total = (await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar() or 0

        offset = (page - 1) * limit
        result = await self._db.execute(
            base.order_by(Allergen.is_system.desc(), Allergen.name)
            .offset(offset)
            .limit(limit)
        )
        allergens = result.scalars().all()

        return [_allergen_to_dict(a) for a in allergens], total

    async def get_by_id(self, allergen_id: int, tenant_id: int) -> dict:
        """Get a single allergen with cross-reactions."""
        a = await self._fetch_allergen(allergen_id, tenant_id)

        # Load cross-reactions bidirectionally
        crs = await self._get_cross_reactions(allergen_id)
        cr_dicts = [_cross_reaction_to_dict(cr, allergen_id) for cr in crs]

        return _allergen_to_dict(a, cross_reactions=cr_dicts)

    async def create(self, tenant_id: int, data: dict) -> dict:
        """Create a custom allergen."""
        allergen = Allergen(
            code=data["codigo"],
            name=data["nombre"],
            description=data.get("descripcion"),
            icon=data.get("icono"),
            is_system=False,
            tenant_id=tenant_id,
        )
        self._db.add(allergen)
        await safe_commit(self._db)
        await self._db.refresh(allergen)
        return _allergen_to_dict(allergen)

    async def update(self, allergen_id: int, tenant_id: int, data: dict) -> dict:
        """Update a custom allergen. System allergens are immutable."""
        a = await self._fetch_allergen(allergen_id, tenant_id)
        self._check_not_system(a, "actualizar")

        if "nombre" in data and data["nombre"] is not None:
            a.name = data["nombre"]
        if "descripcion" in data:
            a.description = data["descripcion"]
        if "icono" in data:
            a.icon = data["icono"]

        await safe_commit(self._db)
        await self._db.refresh(a)
        return _allergen_to_dict(a)

    async def delete(self, allergen_id: int, tenant_id: int, user_id: int) -> dict:
        """Soft-delete a custom allergen. System allergens are protected."""
        a = await self._fetch_allergen(allergen_id, tenant_id)
        self._check_not_system(a, "eliminar")

        a.soft_delete(user_id)
        await safe_commit(self._db)
        return {"message": "Alergeno eliminado"}

    # ── Cross-reactions ──

    async def list_cross_reactions(self, allergen_id: int, tenant_id: int) -> list[dict]:
        """List all cross-reactions for an allergen (bidirectional)."""
        await self._fetch_allergen(allergen_id, tenant_id)
        crs = await self._get_cross_reactions(allergen_id)
        return [_cross_reaction_to_dict(cr, allergen_id) for cr in crs]

    async def add_cross_reaction(
        self,
        allergen_id: int,
        tenant_id: int,
        data: dict,
    ) -> dict:
        """Add a cross-reaction between two allergens."""
        await self._fetch_allergen(allergen_id, tenant_id)
        related_id = data["related_allergen_id"]
        await self._fetch_allergen(related_id, tenant_id)

        # Enforce canonical ordering
        a_id = min(allergen_id, related_id)
        b_id = max(allergen_id, related_id)

        if a_id == b_id:
            raise ValidationError(message="Cannot create cross-reaction with self")

        cr = AllergenCrossReaction(
            allergen_id=a_id,
            related_allergen_id=b_id,
            description=data["descripcion"],
            severity=data["severidad"],
        )
        self._db.add(cr)
        await safe_commit(self._db)
        await self._db.refresh(cr)

        # Load relationships for response
        cr_loaded = await self._db.execute(
            select(AllergenCrossReaction)
            .where(AllergenCrossReaction.id == cr.id)
            .options(
                selectinload(AllergenCrossReaction.allergen),
                selectinload(AllergenCrossReaction.related_allergen),
            )
        )
        cr = cr_loaded.scalar_one()
        return _cross_reaction_to_dict(cr, allergen_id)

    async def remove_cross_reaction(self, cross_reaction_id: int) -> dict:
        """Delete a cross-reaction record."""
        result = await self._db.execute(
            select(AllergenCrossReaction).where(AllergenCrossReaction.id == cross_reaction_id)
        )
        cr = result.scalar_one_or_none()
        if cr is None:
            raise NotFoundError(message="Reaccion cruzada no encontrada")

        await self._db.delete(cr)
        await safe_commit(self._db)
        return {"message": "Reaccion cruzada eliminada"}

    # ── Helpers ──

    async def _fetch_allergen(self, allergen_id: int, tenant_id: int) -> Allergen:
        """Fetch allergen ensuring tenant scope."""
        result = await self._db.execute(
            self._base_query(tenant_id).where(Allergen.id == allergen_id)
        )
        allergen = result.scalar_one_or_none()
        if allergen is None:
            raise NotFoundError(message="Alergeno no encontrado")
        return allergen

    async def _get_cross_reactions(self, allergen_id: int) -> list[AllergenCrossReaction]:
        """Fetch all cross-reactions for an allergen (bidirectional)."""
        result = await self._db.execute(
            select(AllergenCrossReaction)
            .where(
                or_(
                    AllergenCrossReaction.allergen_id == allergen_id,
                    AllergenCrossReaction.related_allergen_id == allergen_id,
                )
            )
            .options(
                selectinload(AllergenCrossReaction.allergen),
                selectinload(AllergenCrossReaction.related_allergen),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    def _check_not_system(allergen: Allergen, action: str) -> None:
        """Raise ForbiddenError if allergen is a system allergen."""
        if allergen.is_system:
            raise ForbiddenError(
                message=f"No se puede {action} un alergeno del sistema"
            )
