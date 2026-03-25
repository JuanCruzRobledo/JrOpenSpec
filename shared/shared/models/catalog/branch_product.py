"""BranchProduct model — product availability and pricing override per branch."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.product import Product
    from shared.models.core.branch import Branch


class BranchProduct(BaseModel):
    """Per-branch product availability and optional price override."""

    __table_args__ = (
        UniqueConstraint("branch_id", "product_id", name="uq_branch_products_branch_product"),
        CheckConstraint(
            "price_override_cents >= 0 OR price_override_cents IS NULL",
            name="ck_branch_products_override_positive",
        ),
    )

    branch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("branches.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id"), nullable=False, index=True
    )
    price_override_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    stock_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    branch: Mapped[Branch] = relationship("Branch", back_populates="branch_products")
    product: Mapped[Product] = relationship("Product", back_populates="branch_products")
