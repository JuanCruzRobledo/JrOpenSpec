"""Branch service — pure business logic.

Maps DB Branch fields (English) to API fields (Spanish).
Handles auto-creation of "General" category on branch creation.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import NotFoundError, ValidationError
from shared.infrastructure.db import safe_commit
from shared.models.catalog.category import Category
from shared.models.catalog.product import Product
from shared.models.catalog.subcategory import Subcategory
from shared.models.core.branch import Branch

logger = logging.getLogger(__name__)


def _slug_from_name(name: str) -> str:
    """Generate a URL slug from a name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


def _branch_to_dict(branch: Branch) -> dict:
    """Map Branch DB model to Spanish API dict."""
    return {
        "id": branch.id,
        "nombre": branch.name,
        "direccion": branch.address,
        "telefono": branch.phone,
        "email": branch.email,
        "imagen_url": branch.image_url,
        "horario_apertura": branch.opening_time,
        "horario_cierre": branch.closing_time,
        "estado": "activo" if branch.is_open else "inactivo",
        "orden": branch.display_order,
        "created_at": branch.created_at.isoformat() if branch.created_at else "",
        "updated_at": branch.updated_at.isoformat() if branch.updated_at else "",
    }


class BranchService:
    """Business logic for branch CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        tenant_id: int,
        page: int = 1,
        limit: int = 10,
        branch_ids: list[int] | None = None,
    ) -> tuple[list[dict], int]:
        """List branches with pagination. Returns (items, total)."""
        base_filter = [
            Branch.tenant_id == tenant_id,
            Branch.deleted_at.is_(None),
        ]

        if branch_ids is not None:
            base_filter.append(Branch.id.in_(branch_ids))

        # Count
        count_stmt = select(func.count(Branch.id)).where(*base_filter)
        total = (await self._db.execute(count_stmt)).scalar() or 0

        # Items
        offset = (page - 1) * limit
        items_stmt = (
            select(Branch)
            .where(*base_filter)
            .order_by(Branch.id)
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(items_stmt)
        branches = result.scalars().all()

        return [_branch_to_dict(b) for b in branches], total

    async def create(self, tenant_id: int, data: dict, user_id: int) -> dict:
        """Create a new branch and auto-create a 'General' category."""
        nombre = data["nombre"]
        slug = _slug_from_name(nombre)

        branch = Branch(
            tenant_id=tenant_id,
            name=nombre,
            slug=slug,
            address=data.get("direccion"),
            phone=data.get("telefono"),
            email=data.get("email"),
            image_url=data.get("imagen_url"),
            opening_time=data.get("horario_apertura", "09:00"),
            closing_time=data.get("horario_cierre", "23:00"),
            display_order=data.get("orden", 0),
            is_open=data.get("estado", "activo") == "activo",
            created_by=user_id,
        )

        self._db.add(branch)
        await safe_commit(self._db)
        await self._db.refresh(branch)

        # Auto-create "General" category for this branch
        general_cat = Category(
            tenant_id=tenant_id,
            branch_id=branch.id,
            name="General",
            slug=f"general-{branch.id}",
            display_order=0,
            created_by=user_id,
        )

        self._db.add(general_cat)
        await safe_commit(self._db)

        return _branch_to_dict(branch)

    async def update(self, branch_id: int, tenant_id: int, data: dict, user_id: int) -> dict:
        """Update a branch."""
        branch = await self._get_branch(branch_id, tenant_id)

        field_map = {
            "nombre": "name",
            "direccion": "address",
            "telefono": "phone",
            "email": "email",
            "imagen_url": "image_url",
            "horario_apertura": "opening_time",
            "horario_cierre": "closing_time",
            "orden": "display_order",
        }

        for api_field, db_field in field_map.items():
            if api_field in data and data[api_field] is not None:
                setattr(branch, db_field, data[api_field])

        # Handle estado -> is_open
        if "estado" in data and data["estado"] is not None:
            branch.is_open = data["estado"] == "activo"

        # Update slug if nombre changed
        if "nombre" in data and data["nombre"] is not None:
            branch.slug = _slug_from_name(data["nombre"])

        branch.updated_by = user_id
        await safe_commit(self._db)
        await self._db.refresh(branch)

        return _branch_to_dict(branch)

    async def delete(self, branch_id: int, tenant_id: int, user_id: int) -> dict:
        """Soft-delete a branch and return cascade counts."""
        branch = await self._get_branch(branch_id, tenant_id)
        now = datetime.now(timezone.utc)

        # Count cascade items — categories scoped to this branch
        cat_filter = [
            Category.tenant_id == tenant_id,
            Category.branch_id == branch_id,
            Category.deleted_at.is_(None),
        ]

        cat_count = (await self._db.execute(
            select(func.count(Category.id)).where(*cat_filter)
        )).scalar() or 0

        # Count subcategories of those categories
        cat_ids_stmt = select(Category.id).where(*cat_filter)
        sub_count = (await self._db.execute(
            select(func.count(Subcategory.id)).where(
                Subcategory.category_id.in_(cat_ids_stmt),
                Subcategory.deleted_at.is_(None),
            )
        )).scalar() or 0

        # Count products of those subcategories
        sub_ids_stmt = select(Subcategory.id).where(
            Subcategory.category_id.in_(cat_ids_stmt),
            Subcategory.deleted_at.is_(None),
        )
        prod_count = (await self._db.execute(
            select(func.count(Product.id)).where(
                Product.subcategory_id.in_(sub_ids_stmt),
                Product.deleted_at.is_(None),
            )
        )).scalar() or 0

        # Soft-delete cascade: products -> subcategories -> categories -> branch
        # Products
        prod_ids_result = await self._db.execute(
            select(Product).where(
                Product.subcategory_id.in_(sub_ids_stmt),
                Product.deleted_at.is_(None),
            )
        )
        for prod in prod_ids_result.scalars().all():
            prod.soft_delete(user_id)

        # Subcategories
        sub_result = await self._db.execute(
            select(Subcategory).where(
                Subcategory.category_id.in_(cat_ids_stmt),
                Subcategory.deleted_at.is_(None),
            )
        )
        for sub in sub_result.scalars().all():
            sub.soft_delete(user_id)

        # Categories
        cat_result = await self._db.execute(
            select(Category).where(*cat_filter)
        )
        for cat in cat_result.scalars().all():
            cat.soft_delete(user_id)

        # Branch
        branch.soft_delete(user_id)
        await safe_commit(self._db)

        return {
            "message": "Sucursal eliminada",
            "cascade": {
                "categorias": cat_count,
                "subcategorias": sub_count,
                "productos": prod_count,
            },
        }

    async def _get_branch(self, branch_id: int, tenant_id: int) -> Branch:
        """Fetch a branch or raise NotFoundError."""
        stmt = select(Branch).where(
            Branch.id == branch_id,
            Branch.tenant_id == tenant_id,
            Branch.deleted_at.is_(None),
        )
        result = await self._db.execute(stmt)
        branch = result.scalar_one_or_none()

        if branch is None:
            raise NotFoundError(message="Sucursal no encontrada")

        return branch
