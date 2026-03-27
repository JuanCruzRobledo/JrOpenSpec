"""Category service — pure business logic.

Categories are scoped to tenant_id in the DB. The spec shows them as
branch-scoped in the API (GET /branches/{branch_id}/categories).
If the Category model has a branch_id field, we filter by it.
Otherwise, we filter by tenant_id only (all categories visible across branches).
"""

from __future__ import annotations

import logging
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import NotFoundError, ValidationError
from shared.infrastructure.db import safe_commit
from shared.models.catalog.category import Category
from shared.models.catalog.product import Product
from shared.models.catalog.subcategory import Subcategory

logger = logging.getLogger(__name__)


def _slug_from_name(name: str) -> str:
    """Generate a URL slug from a name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


def _cat_to_dict(cat: Category) -> dict:
    """Map Category DB model to Spanish API dict."""
    return {
        "id": cat.id,
        "nombre": cat.name,
        "icono": cat.icon,
        "imagen_url": cat.image_url,
        "orden": cat.display_order,
        "estado": "activo" if cat.is_active else "inactivo",
        "es_home": cat.is_home,
        "created_at": cat.created_at.isoformat() if cat.created_at else "",
        "updated_at": cat.updated_at.isoformat() if cat.updated_at else "",
    }


class CategoryService:
    """Business logic for category CRUD."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_filters(self, tenant_id: int, branch_id: int) -> list:
        """Build base query filters scoped to tenant + branch."""
        return [
            Category.tenant_id == tenant_id,
            Category.branch_id == branch_id,
            Category.deleted_at.is_(None),
        ]

    async def list(
        self,
        tenant_id: int,
        branch_id: int,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[dict], int]:
        """List categories with pagination."""
        filters = self._base_filters(tenant_id, branch_id)

        total = (await self._db.execute(
            select(func.count(Category.id)).where(*filters)
        )).scalar() or 0

        offset = (page - 1) * limit
        result = await self._db.execute(
            select(Category)
            .where(*filters)
            .order_by(Category.display_order, Category.id)
            .offset(offset)
            .limit(limit)
        )
        categories = result.scalars().all()

        return [_cat_to_dict(c) for c in categories], total

    async def create(
        self,
        tenant_id: int,
        branch_id: int,
        data: dict,
        user_id: int,
    ) -> dict:
        """Create a new category."""
        nombre = data["nombre"]

        # Auto-increment orden if not provided
        orden = data.get("orden")
        if orden is None:
            filters = self._base_filters(tenant_id, branch_id)
            max_order = (await self._db.execute(
                select(func.max(Category.display_order)).where(*filters)
            )).scalar()
            orden = (max_order or 0) + 1

        cat = Category(
            tenant_id=tenant_id,
            branch_id=branch_id,
            name=nombre,
            slug=_slug_from_name(nombre),
            icon=data.get("icono"),
            image_url=data.get("imagen_url"),
            display_order=orden,
            is_active=data.get("estado", "activo") == "activo",
            created_by=user_id,
        )

        self._db.add(cat)
        await safe_commit(self._db)
        await self._db.refresh(cat)

        return _cat_to_dict(cat)

    async def update(
        self,
        category_id: int,
        tenant_id: int,
        branch_id: int,
        data: dict,
        user_id: int,
    ) -> dict:
        """Update a category."""
        cat = await self._get_category(category_id, tenant_id, branch_id)

        if "nombre" in data and data["nombre"] is not None:
            cat.name = data["nombre"]
            cat.slug = _slug_from_name(data["nombre"])
        if "imagen_url" in data:
            cat.image_url = data["imagen_url"]
        if "orden" in data and data["orden"] is not None:
            cat.display_order = data["orden"]
        if "estado" in data and data["estado"] is not None:
            cat.is_active = data["estado"] == "activo"
        if "icono" in data:
            cat.icon = data["icono"]

        cat.updated_by = user_id
        await safe_commit(self._db)
        await self._db.refresh(cat)

        return _cat_to_dict(cat)

    async def delete(
        self,
        category_id: int,
        tenant_id: int,
        branch_id: int,
        user_id: int,
    ) -> dict:
        """Soft-delete a category with cascade. Protects Home category."""
        cat = await self._get_category(category_id, tenant_id, branch_id)

        # Protect Home category
        if cat.is_home:
            raise ValidationError(message="No se puede eliminar la categoria Home")

        # Count cascade
        sub_count = (await self._db.execute(
            select(func.count(Subcategory.id)).where(
                Subcategory.category_id == category_id,
                Subcategory.deleted_at.is_(None),
            )
        )).scalar() or 0

        sub_ids = select(Subcategory.id).where(
            Subcategory.category_id == category_id,
            Subcategory.deleted_at.is_(None),
        )
        prod_count = (await self._db.execute(
            select(func.count(Product.id)).where(
                Product.subcategory_id.in_(sub_ids),
                Product.deleted_at.is_(None),
            )
        )).scalar() or 0

        # Cascade soft-delete: products -> subcategories -> category
        prod_result = await self._db.execute(
            select(Product).where(
                Product.subcategory_id.in_(sub_ids),
                Product.deleted_at.is_(None),
            )
        )
        for prod in prod_result.scalars().all():
            prod.soft_delete(user_id)

        sub_result = await self._db.execute(
            select(Subcategory).where(
                Subcategory.category_id == category_id,
                Subcategory.deleted_at.is_(None),
            )
        )
        for sub in sub_result.scalars().all():
            sub.soft_delete(user_id)

        cat.soft_delete(user_id)
        await safe_commit(self._db)

        return {
            "message": "Categoria eliminada",
            "cascade": {
                "subcategorias": sub_count,
                "productos": prod_count,
            },
        }

    async def _get_category(self, category_id: int, tenant_id: int, branch_id: int) -> Category:
        """Fetch a category or raise NotFoundError."""
        filters = self._base_filters(tenant_id, branch_id)
        filters.append(Category.id == category_id)

        result = await self._db.execute(select(Category).where(*filters))
        cat = result.scalar_one_or_none()

        if cat is None:
            raise NotFoundError(message="Categoria no encontrada")

        return cat
