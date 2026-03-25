"""Ingredient model — individual ingredient with cost and stock tracking."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.ingredients.ingredient_group import IngredientGroup
    from shared.models.ingredients.sub_ingredient import SubIngredient
    from shared.models.recipes.recipe_ingredient import RecipeIngredient


class Ingredient(BaseModel):
    """A raw ingredient used in recipes and tracked in stock."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_ingredients_tenant_name"),
        CheckConstraint("cost_per_unit_cents >= 0", name="ck_ingredients_cost_positive"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ingredient_groups.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    cost_per_unit_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    min_stock_threshold: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)

    # Relationships
    group: Mapped[IngredientGroup] = relationship("IngredientGroup", back_populates="ingredients")
    sub_ingredients: Mapped[list[SubIngredient]] = relationship(
        "SubIngredient",
        foreign_keys="SubIngredient.parent_ingredient_id",
        back_populates="parent_ingredient",
    )
    recipe_ingredients: Mapped[list[RecipeIngredient]] = relationship("RecipeIngredient", back_populates="ingredient")
