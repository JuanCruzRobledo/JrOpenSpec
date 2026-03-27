"""BranchProduct service — pricing, availability, auto-creation.

Pure business logic — no FastAPI imports.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.exceptions import NotFoundError
from shared.infrastructure.db import safe_commit
from shared.models.catalog.branch_product import BranchProduct
from shared.models.catalog.product import Product
from shared.models.core.branch import Branch

logger = logging.getLogger(__name__)


def _bp_to_dict(bp: BranchProduct) -> dict:
    return {
        "id": bp.id,
        "branch_id": bp.branch_id,
        "nombre_sucursal": bp.branch.name if bp.branch else "",
        "product_id": bp.product_id,
        "nombre_producto": bp.product.name if bp.product else "",
        "esta_activo": bp.is_available,
        "precio_centavos": bp.price_cents,
        "precio_efectivo_centavos": bp.effective_price_cents,
        "orden": bp.sort_order,
    }


class BranchProductService:
    """Manages per-branch product pricing and availability."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_product(self, product_id: int, tenant_id: int) -> list[dict]:
        """Get all branch-product records for a product."""
        result = await self._db.execute(
            select(BranchProduct)
            .join(Branch, Branch.id == BranchProduct.branch_id)
            .where(
                BranchProduct.product_id == product_id,
                Branch.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
            )
            .options(
                joinedload(BranchProduct.branch),
                joinedload(BranchProduct.product),
            )
            .order_by(Branch.name)
        )
        return [_bp_to_dict(bp) for bp in result.scalars().unique().all()]

    async def bulk_upsert(
        self, product_id: int, tenant_id: int, items: list[dict],
    ) -> list[dict]:
        """Create or update branch-product records for a product."""
        # Verify product exists
        prod = await self._db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
                Product.deleted_at.is_(None),
            )
        )
        if prod.scalar_one_or_none() is None:
            raise NotFoundError(message="Producto no encontrado")

        for item in items:
            bp = await self._get_or_create(item["branch_id"], product_id)
            if "esta_activo" in item:
                bp.is_available = item["esta_activo"]
            if "precio_centavos" in item:
                bp.price_cents = item["precio_centavos"]

        await safe_commit(self._db)
        return await self.get_by_product(product_id, tenant_id)

    async def toggle_availability(
        self, product_id: int, branch_id: int, tenant_id: int,
    ) -> dict:
        """Toggle is_available for a branch-product."""
        bp = await self._fetch_bp(branch_id, product_id, tenant_id)
        bp.is_available = not bp.is_available
        await safe_commit(self._db)

        return {
            "branch_id": bp.branch_id,
            "product_id": bp.product_id,
            "esta_activo": bp.is_available,
        }

    async def update_price(
        self, product_id: int, branch_id: int, tenant_id: int, price_cents: int | None,
    ) -> dict:
        """Update the price for a single branch-product."""
        bp = await self._fetch_bp(branch_id, product_id, tenant_id)
        bp.price_cents = price_cents
        await safe_commit(self._db)
        await self._db.refresh(bp)

        # Need to load product for effective_price
        await self._db.refresh(bp, ["product"])

        return {
            "branch_id": bp.branch_id,
            "product_id": bp.product_id,
            "precio_centavos": bp.price_cents,
            "precio_efectivo_centavos": bp.effective_price_cents,
        }

    async def auto_create_for_product(self, product_id: int, tenant_id: int) -> int:
        """Create BranchProduct records for all active branches of the tenant.

        Returns count of records created.
        """
        branches = await self._db.execute(
            select(Branch).where(
                Branch.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
                Branch.is_active.is_(True),
            )
        )
        created = 0
        for branch in branches.scalars().all():
            existing = await self._db.execute(
                select(BranchProduct).where(
                    BranchProduct.branch_id == branch.id,
                    BranchProduct.product_id == product_id,
                )
            )
            if existing.scalar_one_or_none() is None:
                self._db.add(BranchProduct(
                    branch_id=branch.id,
                    product_id=product_id,
                    is_available=True,
                    price_cents=None,
                ))
                created += 1

        if created > 0:
            await safe_commit(self._db)
        return created

    async def _get_or_create(self, branch_id: int, product_id: int) -> BranchProduct:
        """Get existing or create new BranchProduct."""
        result = await self._db.execute(
            select(BranchProduct).where(
                BranchProduct.branch_id == branch_id,
                BranchProduct.product_id == product_id,
            )
        )
        bp = result.scalar_one_or_none()
        if bp is None:
            bp = BranchProduct(
                branch_id=branch_id,
                product_id=product_id,
                is_available=True,
                price_cents=None,
            )
            self._db.add(bp)
        return bp

    async def _fetch_bp(
        self, branch_id: int, product_id: int, tenant_id: int,
    ) -> BranchProduct:
        """Fetch a BranchProduct with tenant scope check."""
        result = await self._db.execute(
            select(BranchProduct)
            .join(Branch, Branch.id == BranchProduct.branch_id)
            .where(
                BranchProduct.branch_id == branch_id,
                BranchProduct.product_id == product_id,
                Branch.tenant_id == tenant_id,
            )
        )
        bp = result.scalar_one_or_none()
        if bp is None:
            raise NotFoundError(message="Producto en sucursal no encontrado")
        return bp
