"""TableSession model — active or closed session at a table."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.billing.check import Check
    from shared.models.core.user import User
    from shared.models.room.diner import Diner
    from shared.models.room.table import Table


class TableSession(BaseModel):
    """Represents an active or past session at a table."""

    table_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tables.id"), nullable=False, index=True
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    opened_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    closed_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # Relationships
    table: Mapped[Table] = relationship("Table", back_populates="sessions")
    diners: Mapped[list[Diner]] = relationship("Diner", back_populates="session")
    check: Mapped[Check | None] = relationship("Check", back_populates="session", uselist=False)
    opener: Mapped[User] = relationship("User", foreign_keys=[opened_by])
    closer: Mapped[User | None] = relationship("User", foreign_keys=[closed_by])
