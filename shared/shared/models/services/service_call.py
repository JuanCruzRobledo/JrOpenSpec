"""ServiceCall model — customer request for service (waiter, water, bill)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.core.user import User
    from shared.models.room.table import Table
    from shared.models.room.table_session import TableSession


class ServiceCall(BaseModel):
    """A service request from a table (waiter call, water request, bill request)."""

    table_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tables.id"), nullable=False, index=True
    )
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("table_sessions.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    called_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    table: Mapped[Table] = relationship("Table")
    session: Mapped[TableSession] = relationship("TableSession")
    resolver: Mapped[User | None] = relationship("User", foreign_keys=[resolved_by])
