"""Product service — pure business logic."""

from __future__ import annotations

import logging
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.exceptions import NotFoundError, ValidationError
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


def _product_to_dict(
    prod: Product,
    cat_name: str = "",
    sub_name: str | None = None,
    cat_id: int | None = None,
) -> dict:
    """Map Product DB model to Spanish API dict."""
    return {
        "id": prod.id,
        "nombre": prod.name,
        "descripcion": prod.description,
        "categoria_id": cat_id or 0,
        "categoria_nombre": cat_name,
        "subcategoria_id": prod.subcategory_id,
        "subcategoria_nombre": sub_name,
        "precio": prod.base_price_cents,
        "imagen_url": prod.image_url,
        "destacado": prod.is_featured,
        "popular": prod.is_popular,
        "estado": "activo" if prod.is_active else "inactivo",
        "created_at": prod.created_at.isoformat() if prod.created_at else "",
        "updated_at": prod.updated_at.isoformat() if prod.updated_at else "",
    }


class ProductService:
    """Business logic for product CRUD."""

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

    async def _subcategory_ids_for_branch(self, tenant_id: int, branch_id: int) -> list[int]:
        """Get subcategory IDs scoped to this tenant/branch."""
        cat_ids = await self._category_ids_for_branch(tenant_id, branch_id)
        if not cat_ids:
            return []
        result = await self._db.execute(
            select(Subcategory.id).where(
                Subcategory.category_id.in_(cat_ids),
                Subcategory.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def list(
        self,
        tenant_id: int,
        branch_id: int,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[dict], int]:
        """List products with pagination."""
        sub_ids = await self._subcategory_ids_for_branch(tenant_id, branch_id)
        if not sub_ids:
            return [], 0

        filters = [
            Product.subcategory_id.in_(sub_ids),
            Product.deleted_at.is_(None),
        ]

        total = (await self._db.execute(
            select(func.count(Product.id)).where(*filters)
        )).scalar() or 0

        offset = (page - 1) * limit
        result = await self._db.execute(
            select(Product)
            .options(
                selectinload(Product.subcategory).selectinload(Subcategory.category),
            )
            .where(*filters)
            .order_by(Product.id)
            .offset(offset)
            .limit(limit)
        )
        products = result.scalars().all()

        items = []
        for prod in products:
            sub_name = prod.subcategory.name if prod.subcategory else None
            cat = prod.subcategory.category if prod.subcategory else None
            cat_name = cat.name if cat else ""
            cat_id = cat.id if cat else 0
            items.append(_product_to_dict(prod, cat_name, sub_name, cat_id))

        return items, total

    async def create(
        self,
        tenant_id: int,
        branch_id: int,
        data: dict,
        user_id: int,
    ) -> dict:
        """Create a product. Validates subcategory belongs to category if both provided."""
        cat_id = data["categoria_id"]
        sub_id = data.get("subcategoria_id")

        # Validate category exists in this branch
        cat_ids = await self._category_ids_for_branch(tenant_id, branch_id)
        if cat_id not in cat_ids:
            raise NotFoundError(message="Categoria no encontrada en esta sucursal")

        # Get category name
        cat_result = await self._db.execute(
            select(Category).where(Category.id == cat_id)
        )
        cat = cat_result.scalar_one_or_none()
        cat_name = cat.name if cat else ""

        # Validate subcategory if provided
        sub_name = None
        actual_sub_id = sub_id
        if sub_id is not None:
            sub_result = await self._db.execute(
                select(Subcategory).where(
                    Subcategory.id == sub_id,
                    Subcategory.deleted_at.is_(None),
                )
            )
            sub = sub_result.scalar_one_or_none()
            if sub is None:
                raise NotFoundError(message="Subcategoria no encontrada")
            if sub.category_id != cat_id:
                raise ValidationError(
                    message="Subcategoria no pertenece a la categoria seleccionada"
                )
            sub_name = sub.name
        else:
            # Product requires subcategory_id in DB — find or create a default one
            # If no subcategory provided, try the first one in the category
            default_sub = await self._db.execute(
                select(Subcategory).where(
                    Subcategory.category_id == cat_id,
                    Subcategory.deleted_at.is_(None),
                ).order_by(Subcategory.display_order).limit(1)
            )
            default_sub_obj = default_sub.scalar_one_or_none()
            if default_sub_obj is None:
                # Auto-create a default subcategory
                default_sub_obj = Subcategory(
                    category_id=cat_id,
                    name="General",
                    slug=f"general-{cat_id}",
                    display_order=0,
                    created_by=user_id,
                )
                self._db.add(default_sub_obj)
                await safe_commit(self._db)
                await self._db.refresh(default_sub_obj)
            actual_sub_id = default_sub_obj.id
            sub_name = default_sub_obj.name

        nombre = data["nombre"]
        prod = Product(
            tenant_id=tenant_id,
            subcategory_id=actual_sub_id,
            name=nombre,
            slug=_slug_from_name(nombre),
            description=data.get("descripcion"),
            image_url=data.get("imagen_url"),
            base_price_cents=data.get("precio", 0),
            is_active=data.get("estado", "activo") == "activo",
            created_by=user_id,
        )

        prod.is_featured = data.get("destacado", False)
        prod.is_popular = data.get("popular", False)

        self._db.add(prod)
        await safe_commit(self._db)
        await self._db.refresh(prod)

        return _product_to_dict(prod, cat_name, sub_name, cat_id)

    async def update(
        self,
        product_id: int,
        tenant_id: int,
        branch_id: int,
        data: dict,
        user_id: int,
    ) -> dict:
        """Update a product."""
        prod = await self._get_product(product_id, tenant_id, branch_id)

        if "nombre" in data and data["nombre"] is not None:
            prod.name = data["nombre"]
            prod.slug = _slug_from_name(data["nombre"])
        if "descripcion" in data:
            prod.description = data["descripcion"]
        if "imagen_url" in data:
            prod.image_url = data["imagen_url"]
        if "precio" in data and data["precio"] is not None:
            prod.base_price_cents = data["precio"]
        if "estado" in data and data["estado"] is not None:
            prod.is_active = data["estado"] == "activo"
        if "destacado" in data and data["destacado"] is not None:
            prod.is_featured = data["destacado"]
        if "popular" in data and data["popular"] is not None:
            prod.is_popular = data["popular"]

        # Handle category/subcategory change
        if "subcategoria_id" in data and data["subcategoria_id"] is not None:
            sub_result = await self._db.execute(
                select(Subcategory).where(
                    Subcategory.id == data["subcategoria_id"],
                    Subcategory.deleted_at.is_(None),
                )
            )
            sub = sub_result.scalar_one_or_none()
            if sub is None:
                raise NotFoundError(message="Subcategoria no encontrada")
            if "categoria_id" in data and data["categoria_id"] is not None:
                if sub.category_id != data["categoria_id"]:
                    raise ValidationError(
                        message="Subcategoria no pertenece a la categoria seleccionada"
                    )
            prod.subcategory_id = data["subcategoria_id"]

        prod.updated_by = user_id
        await safe_commit(self._db)
        await self._db.refresh(prod)

        # Load related data for response
        sub_result = await self._db.execute(
            select(Subcategory)
            .options(selectinload(Subcategory.category))
            .where(Subcategory.id == prod.subcategory_id)
        )
        sub = sub_result.scalar_one_or_none()
        sub_name = sub.name if sub else None
        cat = sub.category if sub else None
        cat_name = cat.name if cat else ""
        cat_id = cat.id if cat else 0

        return _product_to_dict(prod, cat_name, sub_name, cat_id)

    async def delete(
        self,
        product_id: int,
        tenant_id: int,
        branch_id: int,
        user_id: int,
    ) -> dict:
        """Soft-delete a product."""
        prod = await self._get_product(product_id, tenant_id, branch_id)
        prod.soft_delete(user_id)
        await safe_commit(self._db)

        return {"message": "Producto eliminado"}

    async def _get_product(self, product_id: int, tenant_id: int, branch_id: int) -> Product:
        """Fetch a product ensuring it belongs to the tenant/branch."""
        sub_ids = await self._subcategory_ids_for_branch(tenant_id, branch_id)
        if not sub_ids:
            raise NotFoundError(message="Producto no encontrado")

        result = await self._db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.subcategory_id.in_(sub_ids),
                Product.deleted_at.is_(None),
            )
        )
        prod = result.scalar_one_or_none()
        if prod is None:
            raise NotFoundError(message="Producto no encontrado")
        return prod
