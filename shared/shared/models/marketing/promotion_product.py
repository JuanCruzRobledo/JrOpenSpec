"""PromotionProduct model — links promotions to specific products."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.product import Product
    from shared.models.marketing.promotion import Promotion


class PromotionProduct(BaseModel):
    """Association between a promotion and a product."""

    __table_args__ = (
        UniqueConstraint("promotion_id", "product_id", name="uq_promotion_products_promotion_product"),
    )

    promotion_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("promotions.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id"), nullable=False, index=True
    )

    # Relationships
    promotion: Mapped[Promotion] = relationship("Promotion", back_populates="promotion_products")
    product: Mapped[Product] = relationship("Product")
