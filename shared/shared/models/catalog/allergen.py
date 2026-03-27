"""Allergen model — system + tenant-scoped allergen definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.allergen_cross_reaction import AllergenCrossReaction
    from shared.models.catalog.product_allergen import ProductAllergen


class Allergen(BaseModel):
    """Allergen definition. System allergens (EU 14) have is_system=True and tenant_id=None."""

    __table_args__ = (
        UniqueConstraint("code", "tenant_id", name="uq_allergens_code_tenant"),
        CheckConstraint(
            "is_system = false OR tenant_id IS NULL",
            name="ck_allergens_system_no_tenant",
        ),
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    tenant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Relationships
    product_allergens: Mapped[list[ProductAllergen]] = relationship(
        "ProductAllergen", back_populates="allergen"
    )
    cross_reactions_as_source: Mapped[list[AllergenCrossReaction]] = relationship(
        "AllergenCrossReaction",
        foreign_keys="AllergenCrossReaction.allergen_id",
        back_populates="allergen",
        cascade="all, delete-orphan",
    )
    cross_reactions_as_related: Mapped[list[AllergenCrossReaction]] = relationship(
        "AllergenCrossReaction",
        foreign_keys="AllergenCrossReaction.related_allergen_id",
        back_populates="related_allergen",
        cascade="all, delete-orphan",
    )

    @property
    def all_cross_reactions(self) -> list[AllergenCrossReaction]:
        """Return union of cross-reactions from both directions."""
        return self.cross_reactions_as_source + self.cross_reactions_as_related
