"""Batch price update service — preview and apply with audit logging.

Pure business logic — no FastAPI imports.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.enums import BatchPriceOperation
from shared.exceptions import ValidationError
from shared.infrastructure.db import safe_commit
from shared.models.catalog.branch_product import BranchProduct
from shared.models.core.branch import Branch

logger = logging.getLogger(__name__)


class BatchPriceService:
    """Two-step batch price update: preview (read-only) and apply (transactional)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def preview(
        self,
        product_ids: list[int],
        operation: BatchPriceOperation,
        amount: Decimal,
        branch_id: int | None,
        tenant_id: int,
    ) -> dict:
        """Generate preview of price changes without side effects."""
        if len(product_ids) > 500:
            raise ValidationError(message="Maximo 500 productos por lote")

        branch_products = await self._fetch_affected(product_ids, branch_id, tenant_id)

        changes = []
        branch_ids_set = set()
        product_ids_set = set()

        for bp in branch_products:
            old_price = bp.effective_price_cents
            new_price = self._calculate(old_price, operation, amount)
            changes.append({
                "product_id": bp.product_id,
                "nombre_producto": bp.product.name if bp.product else "",
                "branch_id": bp.branch_id,
                "nombre_sucursal": bp.branch.name if bp.branch else "",
                "precio_anterior_centavos": old_price,
                "precio_nuevo_centavos": new_price,
            })
            branch_ids_set.add(bp.branch_id)
            product_ids_set.add(bp.product_id)

        return {
            "cambios": changes,
            "total_productos": len(product_ids_set),
            "total_sucursales": len(branch_ids_set),
            "total_cambios": len(changes),
        }

    async def apply(
        self,
        product_ids: list[int],
        operation: BatchPriceOperation,
        amount: Decimal,
        branch_id: int | None,
        tenant_id: int,
        user_id: int,
    ) -> dict:
        """Apply batch price update transactionally with audit logging."""
        preview = await self.preview(product_ids, operation, amount, branch_id, tenant_id)

        audit_ids: list[int] = []
        for change in preview["cambios"]:
            # Update the BranchProduct price
            bp = await self._db.execute(
                select(BranchProduct).where(
                    BranchProduct.branch_id == change["branch_id"],
                    BranchProduct.product_id == change["product_id"],
                )
            )
            bp_obj = bp.scalar_one()
            bp_obj.price_cents = change["precio_nuevo_centavos"]

            # Create audit log entry (if AuditLog model exists; otherwise just log)
            try:
                from shared.models.audit.audit_log import AuditLog

                audit = AuditLog(
                    entity_type="branch_product",
                    entity_id=f"{change['branch_id']}:{change['product_id']}",
                    action="batch_price_update",
                    old_value=str(change["precio_anterior_centavos"]),
                    new_value=str(change["precio_nuevo_centavos"]),
                    user_id=user_id,
                    tenant_id=tenant_id,
                )
                self._db.add(audit)
            except ImportError:
                # AuditLog model not yet available — log only
                logger.info(
                    "Batch price audit: product=%s branch=%s old=%s new=%s user=%s",
                    change["product_id"],
                    change["branch_id"],
                    change["precio_anterior_centavos"],
                    change["precio_nuevo_centavos"],
                    user_id,
                )

        await safe_commit(self._db)

        # Collect audit IDs if available
        # For now return empty list as AuditLog may not exist
        return {
            "applied": preview["total_cambios"],
            "audit_log_ids": audit_ids,
        }

    async def _fetch_affected(
        self,
        product_ids: list[int],
        branch_id: int | None,
        tenant_id: int,
    ) -> list[BranchProduct]:
        """Fetch BranchProduct records affected by the batch operation."""
        stmt = (
            select(BranchProduct)
            .join(Branch, Branch.id == BranchProduct.branch_id)
            .where(
                BranchProduct.product_id.in_(product_ids),
                Branch.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
            )
            .options(
                joinedload(BranchProduct.product),
                joinedload(BranchProduct.branch),
            )
        )

        if branch_id is not None:
            stmt = stmt.where(BranchProduct.branch_id == branch_id)

        result = await self._db.execute(stmt)
        return list(result.scalars().unique().all())

    @staticmethod
    def _calculate(old_price: int, operation: BatchPriceOperation, amount: Decimal) -> int:
        """Calculate new price based on operation. Clamps to >= 0."""
        match operation:
            case BatchPriceOperation.FIXED_ADD:
                new = old_price + int(amount)
            case BatchPriceOperation.FIXED_SUBTRACT:
                new = old_price - int(amount)
            case BatchPriceOperation.PERCENTAGE_INCREASE:
                new = round(old_price * (1 + float(amount) / 100))
            case BatchPriceOperation.PERCENTAGE_DECREASE:
                new = round(old_price * (1 - float(amount) / 100))
        return max(0, new)
