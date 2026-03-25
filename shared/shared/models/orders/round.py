"""Round model — a round of orders within a table session."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.core.user import User
    from shared.models.orders.round_item import RoundItem
    from shared.models.room.table_session import TableSession


class Round(BaseModel):
    """A round of orders sent to the kitchen from a table session."""

    __table_args__ = (
        UniqueConstraint("session_id", "round_number", name="uq_rounds_session_number"),
    )

    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("table_sessions.id"), nullable=False, index=True
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    session: Mapped[TableSession] = relationship("TableSession")
    items: Mapped[list[RoundItem]] = relationship("RoundItem", back_populates="round")
    sender: Mapped[User | None] = relationship("User", foreign_keys=[sent_by])
