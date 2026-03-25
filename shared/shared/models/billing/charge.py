"""Charge model — individual line item on a check."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.billing.allocation import Allocation
    from shared.models.billing.check import Check
    from shared.models.orders.round_item import RoundItem


class Charge(BaseModel):
    """A line item charge on a check, linked to a round item."""

    __table_args__ = (
        CheckConstraint("amount_cents >= 0", name="ck_charges_amount_positive"),
    )

    check_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checks.id"), nullable=False, index=True
    )
    round_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("round_items.id"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    check: Mapped[Check] = relationship("Check", back_populates="charges")
    round_item: Mapped[RoundItem] = relationship("RoundItem")
    allocations: Mapped[list[Allocation]] = relationship("Allocation", back_populates="charge")
