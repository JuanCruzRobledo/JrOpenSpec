"""ProductAllergen model — association between products and allergens with severity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.allergen import Allergen
    from shared.models.catalog.product import Product


class ProductAllergen(BaseModel):
    """Links a product to an allergen with severity level (contains, may_contain, trace)."""

    __table_args__ = (
        UniqueConstraint("product_id", "allergen_id", name="uq_product_allergens_product_allergen"),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id"), nullable=False, index=True
    )
    allergen_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("allergens.id"), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="contains")

    # Relationships
    product: Mapped[Product] = relationship("Product", back_populates="product_allergens")
    allergen: Mapped[Allergen] = relationship("Allergen", back_populates="product_allergens")
