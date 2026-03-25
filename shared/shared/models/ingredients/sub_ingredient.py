"""SubIngredient model — ingredient composition (ingredient made of other ingredients)."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.ingredients.ingredient import Ingredient


class SubIngredient(BaseModel):
    """Composition link: one ingredient is composed of another with a quantity."""

    __table_args__ = (
        UniqueConstraint(
            "parent_ingredient_id", "child_ingredient_id",
            name="uq_sub_ingredients_parent_child",
        ),
    )

    parent_ingredient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ingredients.id"), nullable=False, index=True
    )
    child_ingredient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ingredients.id"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    parent_ingredient: Mapped[Ingredient] = relationship(
        "Ingredient",
        foreign_keys=[parent_ingredient_id],
        back_populates="sub_ingredients",
    )
    child_ingredient: Mapped[Ingredient] = relationship(
        "Ingredient",
        foreign_keys=[child_ingredient_id],
    )
