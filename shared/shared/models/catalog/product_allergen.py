"""ProductAllergen model — association between products and allergens with presence type and risk."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.allergen import Allergen
    from shared.models.catalog.product import Product


class ProductAllergen(BaseModel):
    """Links a product to an allergen with presence type and risk level."""

    __table_args__ = (
        UniqueConstraint(
            "product_id", "allergen_id",
            name="uq_product_allergens_product_allergen",
        ),
        CheckConstraint(
            "presence_type != 'free_of' OR risk_level = 'low'",
            name="ck_product_allergens_free_of_low_risk",
        ),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    allergen_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("allergens.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    presence_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="contains"
    )
    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="moderate"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    product: Mapped[Product] = relationship("Product", back_populates="product_allergens")
    allergen: Mapped[Allergen] = relationship("Allergen", back_populates="product_allergens")
