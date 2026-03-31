"""Table model — individual table within a sector."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.room.sector import Sector
    from shared.models.room.table_session import TableSession


class Table(BaseModel):
    """A physical table in a restaurant sector."""

    __table_args__ = (
        # Partial unique: no duplicate number per sector among non-deleted rows
        Index(
            "uq_tables_sector_number_active",
            "sector_id",
            "number",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
        # Composite index for status queries within a sector
        Index(
            "ix_tables_sector_status_active",
            "sector_id",
            "status",
            postgresql_where="deleted_at IS NULL",
        ),
        CheckConstraint("capacity >= 1 AND capacity <= 20", name="ck_table_capacity_range"),
        CheckConstraint("number > 0", name="ck_table_number_positive"),
    )

    sector_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sectors.id"), nullable=False, index=True
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    status: Mapped[str] = mapped_column(String(25), nullable=False, default="libre")
    code: Mapped[str | None] = mapped_column(String(15), nullable=True)
    pos_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    pos_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Optimistic locking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Timestamp tracking for FSM states
    status_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    occupied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    order_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    order_fulfilled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    check_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Session counter
    session_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    sector: Mapped[Sector] = relationship("Sector", back_populates="tables")
    sessions: Mapped[list[TableSession]] = relationship("TableSession", back_populates="table")
