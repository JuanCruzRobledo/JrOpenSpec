"""Check model — the bill/check for a table session."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.billing.charge import Charge
    from shared.models.billing.payment import Payment
    from shared.models.core.user import User
    from shared.models.room.table_session import TableSession


class Check(BaseModel):
    """The bill/check associated with a table session (one-to-one)."""

    __table_args__ = (
        CheckConstraint("subtotal_cents >= 0", name="ck_checks_subtotal_positive"),
    )

    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("table_sessions.id"), nullable=False, unique=True
    )
    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tax_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tip_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    session: Mapped[TableSession] = relationship("TableSession", back_populates="check")
    charges: Mapped[list[Charge]] = relationship("Charge", back_populates="check")
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="check")
    closer: Mapped[User | None] = relationship("User", foreign_keys=[closed_by])
