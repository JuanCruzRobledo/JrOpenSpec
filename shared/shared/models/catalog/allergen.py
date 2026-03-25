"""Allergen model — global (NOT tenant-scoped) allergen definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.product_allergen import ProductAllergen


class Allergen(BaseModel):
    """Global allergen definition (14 EU allergens). NOT tenant-scoped."""

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    product_allergens: Mapped[list[ProductAllergen]] = relationship("ProductAllergen", back_populates="allergen")
