"""Recipe model — recipe for a product (one-to-one)."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.product import Product
    from shared.models.recipes.recipe_ingredient import RecipeIngredient
    from shared.models.recipes.recipe_step import RecipeStep


class Recipe(BaseModel):
    """A recipe linked to a product (one-to-one)."""

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id"), nullable=False, unique=True
    )
    yield_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=1)
    yield_unit: Mapped[str] = mapped_column(String(50), nullable=False, default="porcion")
    total_cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    product: Mapped[Product] = relationship("Product", back_populates="recipe")
    ingredients: Mapped[list[RecipeIngredient]] = relationship("RecipeIngredient", back_populates="recipe")
    steps: Mapped[list[RecipeStep]] = relationship("RecipeStep", back_populates="recipe")
