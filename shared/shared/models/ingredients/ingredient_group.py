"""IngredientGroup model — grouping for ingredients within a tenant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.ingredients.ingredient import Ingredient


class IngredientGroup(BaseModel):
    """Ingredient grouping (e.g., Lacteos, Verduras, Carnes)."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_ingredient_groups_tenant_name"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    ingredients: Mapped[list[Ingredient]] = relationship("Ingredient", back_populates="group")
