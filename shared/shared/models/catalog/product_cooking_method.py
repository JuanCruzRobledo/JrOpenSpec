"""ProductCookingMethod — junction table linking products to cooking methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.cooking_method import CookingMethod


class ProductCookingMethod(BaseModel):
    """Associates a product with a cooking method."""

    __table_args__ = (
        UniqueConstraint(
            "product_id", "cooking_method_id",
            name="uq_product_cooking_methods_product_method",
        ),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    cooking_method_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cooking_methods.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    cooking_method: Mapped["CookingMethod"] = relationship("CookingMethod")
