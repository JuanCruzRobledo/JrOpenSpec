"""RecipeIngredient model — ingredient usage within a recipe."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.ingredients.ingredient import Ingredient
    from shared.models.recipes.recipe import Recipe


class RecipeIngredient(BaseModel):
    """An ingredient used in a recipe with quantity and unit."""

    __table_args__ = (
        UniqueConstraint("recipe_id", "ingredient_id", name="uq_recipe_ingredients_recipe_ingredient"),
    )

    recipe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("recipes.id"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ingredients.id"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    recipe: Mapped[Recipe] = relationship("Recipe", back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship("Ingredient", back_populates="recipe_ingredients")
