"""Allocation model — how a charge is split among diners."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.billing.charge import Charge
    from shared.models.room.diner import Diner


class Allocation(BaseModel):
    """Allocation of a charge amount to a specific diner."""

    __table_args__ = (
        UniqueConstraint("charge_id", "diner_id", name="uq_allocations_charge_diner"),
    )

    charge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("charges.id"), nullable=False, index=True
    )
    diner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("diners.id"), nullable=False, index=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    split_type: Mapped[str] = mapped_column(String(20), nullable=False, default="equal")

    # Relationships
    charge: Mapped[Charge] = relationship("Charge", back_populates="allocations")
    diner: Mapped[Diner] = relationship("Diner")
