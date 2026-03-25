"""RoundItem model — individual item within a round."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.product import Product
    from shared.models.orders.kitchen_ticket import KitchenTicket
    from shared.models.orders.round import Round
    from shared.models.room.diner import Diner


class RoundItem(BaseModel):
    """An individual ordered item within a round."""

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_round_items_quantity_positive"),
        CheckConstraint("unit_price_cents >= 0", name="ck_round_items_unit_price_positive"),
    )

    round_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("rounds.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id"), nullable=False, index=True
    )
    diner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("diners.id"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # Relationships
    round: Mapped[Round] = relationship("Round", back_populates="items")
    product: Mapped[Product] = relationship("Product")
    diner: Mapped[Diner | None] = relationship("Diner", back_populates="round_items")
    kitchen_ticket: Mapped[KitchenTicket | None] = relationship(
        "KitchenTicket", back_populates="round_item", uselist=False
    )
