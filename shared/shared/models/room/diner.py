"""Diner model — individual guest at a table session."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.orders.round_item import RoundItem
    from shared.models.room.table_session import TableSession


class Diner(BaseModel):
    """An individual guest/diner at a table session."""

    __table_args__ = (
        UniqueConstraint(
            "session_id", "seat_number",
            name="uq_diners_session_seat",
            sqlite_on_conflict="FAIL",
        ),
    )

    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("table_sessions.id"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seat_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    session: Mapped[TableSession] = relationship("TableSession", back_populates="diners")
    round_items: Mapped[list[RoundItem]] = relationship("RoundItem", back_populates="diner")
