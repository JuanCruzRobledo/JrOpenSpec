"""Subcategory model — second-level menu grouping under a category."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.category import Category
    from shared.models.catalog.product import Product


class Subcategory(BaseModel):
    """Menu subcategory within a category."""

    __table_args__ = (
        UniqueConstraint("category_id", "slug", name="uq_subcategories_category_slug"),
    )

    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categories.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    category: Mapped[Category] = relationship("Category", back_populates="subcategories")
    products: Mapped[list[Product]] = relationship("Product", back_populates="subcategory")
