"""ProductBadge — junction table linking products to badges."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class ProductBadge(BaseModel):
    """Associates a product with a badge, with sort order."""

    __table_args__ = (
        UniqueConstraint(
            "product_id", "badge_id",
            name="uq_product_badges_product_badge",
        ),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    badge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
