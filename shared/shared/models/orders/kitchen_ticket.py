"""KitchenTicket model — ticket for kitchen/station processing."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.core.user import User
    from shared.models.orders.round_item import RoundItem


class KitchenTicket(BaseModel):
    """A kitchen ticket dispatched to a station for a round item."""

    round_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("round_items.id"), nullable=False, index=True
    )
    station: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_to: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    round_item: Mapped[RoundItem] = relationship("RoundItem", back_populates="kitchen_ticket")
    assignee: Mapped[User | None] = relationship("User", foreign_keys=[assigned_to])
