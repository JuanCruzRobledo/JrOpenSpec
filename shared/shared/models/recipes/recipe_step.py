"""RecipeStep model — individual step in a recipe."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.recipes.recipe import Recipe


class RecipeStep(BaseModel):
    """An ordered step in a recipe with instructions."""

    __table_args__ = (
        UniqueConstraint("recipe_id", "step_number", name="uq_recipe_steps_recipe_step"),
    )

    recipe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("recipes.id"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    recipe: Mapped[Recipe] = relationship("Recipe", back_populates="steps")
