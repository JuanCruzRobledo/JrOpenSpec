"""BranchProduct model — product availability and pricing per branch."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.product import Product
    from shared.models.core.branch import Branch


class BranchProduct(BaseModel):
    """Per-branch product availability, pricing override, and sort order."""

    __table_args__ = (
        UniqueConstraint("branch_id", "product_id", name="uq_branch_products_branch_product"),
        CheckConstraint(
            "price_cents IS NULL OR price_cents >= 0",
            name="ck_branch_products_price_positive",
        ),
    )

    branch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Relationships
    branch: Mapped[Branch] = relationship("Branch", back_populates="branch_products")
    product: Mapped[Product] = relationship("Product", back_populates="branch_products")

    @property
    def effective_price_cents(self) -> int:
        """Resolve price: branch override or product base price."""
        if self.price_cents is not None:
            return self.price_cents
        return self.product.base_price_cents
