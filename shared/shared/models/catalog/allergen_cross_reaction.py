"""AllergenCrossReaction model — bidirectional cross-reaction between allergens."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.allergen import Allergen


class AllergenCrossReaction(BaseModel):
    """Records a cross-reaction between two allergens.

    Canonical ordering: allergen_id < related_allergen_id to prevent
    duplicate pairs. Bidirectional queries go through Allergen.all_cross_reactions.
    """

    __table_args__ = (
        UniqueConstraint(
            "allergen_id", "related_allergen_id",
            name="uq_allergen_cross_reactions_pair",
        ),
        CheckConstraint(
            "allergen_id < related_allergen_id",
            name="ck_allergen_cross_reactions_canonical_order",
        ),
    )

    allergen_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("allergens.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    related_allergen_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("allergens.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    allergen: Mapped[Allergen] = relationship(
        "Allergen",
        foreign_keys=[allergen_id],
        back_populates="cross_reactions_as_source",
    )
    related_allergen: Mapped[Allergen] = relationship(
        "Allergen",
        foreign_keys=[related_allergen_id],
        back_populates="cross_reactions_as_related",
    )
