"""Subcategory service — pure business logic."""

from __future__ import annotations

import logging
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.exceptions import NotFoundError
from shared.infrastructure.db import safe_commit
from shared.models.catalog.category import Category
from shared.models.catalog.product import Product
from shared.models.catalog.subcategory import Subcategory

logger = logging.getLogger(__name__)


def _slug_from_name(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


def _sub_to_dict(sub: Subcategory, cat_name: str = "", products_count: int = 0) -> dict:
    """Map Subcategory DB model to Spanish API dict."""
    return {
        "id": sub.id,
        "nombre": sub.name,
        "imagen_url": sub.image_url,
        "categoria_id": sub.category_id,
        "categoria_nombre": cat_name,
        "orden": sub.display_order,
        "estado": "activo" if sub.is_active else "inactivo",
        "productos_count": products_count,
        "created_at": sub.created_at.isoformat() if sub.created_at else "",
        "updated_at": sub.updated_at.isoformat() if sub.updated_at else "",
    }


class SubcategoryService:
    """Business logic for subcategory CRUD."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _category_ids_for_branch(self, tenant_id: int, branch_id: int) -> list[int]:
        """Get category IDs accessible for the given tenant/branch."""
        filters = [
            Category.tenant_id == tenant_id,
            Category.branch_id == branch_id,
            Category.deleted_at.is_(None),
        ]

        result = await self._db.execute(select(Category.id).where(*filters))
        return list(result.scalars().all())

    async def list(
        self,
        tenant_id: int,
        branch_id: int,
        page: int = 1,
        limit: int = 10,
        category_id: int | None = None,
    ) -> tuple[list[dict], int]:
        """List subcategories with pagination, optionally filtered by category."""
        cat_ids = await self._category_ids_for_branch(tenant_id, branch_id)
        if not cat_ids:
            return [], 0

        filters = [
            Subcategory.category_id.in_(cat_ids),
            Subcategory.deleted_at.is_(None),
        ]
        if category_id is not None:
            filters.append(Subcategory.category_id == category_id)

        total = (await self._db.execute(
            select(func.count(Subcategory.id)).where(*filters)
        )).scalar() or 0

        offset = (page - 1) * limit
        result = await self._db.execute(
            select(Subcategory)
            .options(selectinload(Subcategory.category))
            .where(*filters)
            .order_by(Subcategory.display_order, Subcategory.id)
            .offset(offset)
            .limit(limit)
        )
        subcategories = result.scalars().all()

        # Single aggregated query instead of one COUNT per subcategory (N+1 fix)
        sub_ids = [s.id for s in subcategories]
        counts_result = await self._db.execute(
            select(Product.subcategory_id, func.count(Product.id).label("cnt"))
            .where(
                Product.subcategory_id.in_(sub_ids),
                Product.deleted_at.is_(None),
            )
            .group_by(Product.subcategory_id)
        )
        prod_counts: dict[int, int] = {row.subcategory_id: row.cnt for row in counts_result}

        items = []
        for sub in subcategories:
            cat_name = sub.category.name if sub.category else ""
            items.append(_sub_to_dict(sub, cat_name, prod_counts.get(sub.id, 0)))

        return items, total

    async def create(
        self,
        tenant_id: int,
        branch_id: int,
        data: dict,
        user_id: int,
    ) -> dict:
        """Create a subcategory."""
        cat_id = data["categoria_id"]

        # Verify category belongs to this tenant/branch
        cat = await self._get_category(cat_id, tenant_id, branch_id)

        # Auto-increment orden
        orden = data.get("orden")
        if orden is None:
            max_order = (await self._db.execute(
                select(func.max(Subcategory.display_order)).where(
                    Subcategory.category_id == cat_id,
                    Subcategory.deleted_at.is_(None),
                )
            )).scalar()
            orden = (max_order or 0) + 1

        nombre = data["nombre"]
        sub = Subcategory(
            category_id=cat_id,
            name=nombre,
            slug=_slug_from_name(nombre),
            image_url=data.get("imagen_url"),
            display_order=orden,
            is_active=data.get("estado", "activo") == "activo",
            created_by=user_id,
        )

        self._db.add(sub)
        await safe_commit(self._db)
        await self._db.refresh(sub)

        return _sub_to_dict(sub, cat.name, 0)

    async def update(
        self,
        subcategory_id: int,
        tenant_id: int,
        branch_id: int,
        data: dict,
        user_id: int,
    ) -> dict:
        """Update a subcategory."""
        sub = await self._get_subcategory(subcategory_id, tenant_id, branch_id)

        if "nombre" in data and data["nombre"] is not None:
            sub.name = data["nombre"]
            sub.slug = _slug_from_name(data["nombre"])
        if "imagen_url" in data:
            sub.image_url = data["imagen_url"]
        if "orden" in data and data["orden"] is not None:
            sub.display_order = data["orden"]
        if "estado" in data and data["estado"] is not None:
            sub.is_active = data["estado"] == "activo"
        if "categoria_id" in data and data["categoria_id"] is not None:
            # Verify new category belongs to tenant/branch
            new_cat = await self._get_category(data["categoria_id"], tenant_id, branch_id)
            sub.category_id = new_cat.id

        sub.updated_by = user_id
        await safe_commit(self._db)
        await self._db.refresh(sub)

        # Load category name
        cat_result = await self._db.execute(
            select(Category).where(Category.id == sub.category_id)
        )
        cat = cat_result.scalar_one_or_none()
        cat_name = cat.name if cat else ""

        prod_count = (await self._db.execute(
            select(func.count(Product.id)).where(
                Product.subcategory_id == sub.id,
                Product.deleted_at.is_(None),
            )
        )).scalar() or 0

        return _sub_to_dict(sub, cat_name, prod_count)

    async def delete(
        self,
        subcategory_id: int,
        tenant_id: int,
        branch_id: int,
        user_id: int,
    ) -> dict:
        """Soft-delete a subcategory with cascade."""
        sub = await self._get_subcategory(subcategory_id, tenant_id, branch_id)

        # Count products
        prod_count = (await self._db.execute(
            select(func.count(Product.id)).where(
                Product.subcategory_id == subcategory_id,
                Product.deleted_at.is_(None),
            )
        )).scalar() or 0

        # Cascade soft-delete products
        prod_result = await self._db.execute(
            select(Product).where(
                Product.subcategory_id == subcategory_id,
                Product.deleted_at.is_(None),
            )
        )
        for prod in prod_result.scalars().all():
            prod.soft_delete(user_id)

        sub.soft_delete(user_id)
        await safe_commit(self._db)

        return {
            "message": "Subcategoria eliminada",
            "cascade": {"productos": prod_count},
        }

    async def _get_category(self, category_id: int, tenant_id: int, branch_id: int) -> Category:
        """Fetch and validate a category belongs to this tenant/branch."""
        filters = [
            Category.id == category_id,
            Category.tenant_id == tenant_id,
            Category.branch_id == branch_id,
            Category.deleted_at.is_(None),
        ]

        result = await self._db.execute(select(Category).where(*filters))
        cat = result.scalar_one_or_none()
        if cat is None:
            raise NotFoundError(message="Categoria no encontrada")
        return cat

    async def _get_subcategory(
        self, subcategory_id: int, tenant_id: int, branch_id: int
    ) -> Subcategory:
        """Fetch a subcategory ensuring it belongs to the tenant/branch."""
        cat_ids = await self._category_ids_for_branch(tenant_id, branch_id)
        if not cat_ids:
            raise NotFoundError(message="Subcategoria no encontrada")

        result = await self._db.execute(
            select(Subcategory).where(
                Subcategory.id == subcategory_id,
                Subcategory.category_id.in_(cat_ids),
                Subcategory.deleted_at.is_(None),
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            raise NotFoundError(message="Subcategoria no encontrada")
        return sub
