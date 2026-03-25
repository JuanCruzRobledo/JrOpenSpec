"""Payment model — payment against a check."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.billing.check import Check
    from shared.models.room.diner import Diner


class Payment(BaseModel):
    """A payment made against a check (cash, card, mercadopago, transfer)."""

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_payments_amount_positive"),
    )

    check_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checks.id"), nullable=False, index=True
    )
    diner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("diners.id"), nullable=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    check: Mapped[Check] = relationship("Check", back_populates="payments")
    diner: Mapped[Diner | None] = relationship("Diner")
