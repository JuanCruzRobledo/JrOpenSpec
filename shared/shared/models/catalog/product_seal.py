"""ProductSeal — junction table linking products to seals."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class ProductSeal(BaseModel):
    """Associates a product with a seal, with sort order."""

    __table_args__ = (
        UniqueConstraint(
            "product_id", "seal_id",
            name="uq_product_seals_product_seal",
        ),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    seal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("seals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
