"""ProductDietaryProfile — junction table linking products to dietary profiles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.dietary_profile import DietaryProfile


class ProductDietaryProfile(BaseModel):
    """Associates a product with a dietary profile."""

    __table_args__ = (
        UniqueConstraint(
            "product_id", "dietary_profile_id",
            name="uq_product_dietary_profiles_product_profile",
        ),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    dietary_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("dietary_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    dietary_profile: Mapped["DietaryProfile"] = relationship("DietaryProfile")
