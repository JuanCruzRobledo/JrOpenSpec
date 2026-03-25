"""Table model — individual table within a sector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.room.sector import Sector
    from shared.models.room.table_session import TableSession


class Table(BaseModel):
    """A physical table in a restaurant sector."""

    __table_args__ = (
        UniqueConstraint("sector_id", "number", name="uq_tables_sector_number"),
    )

    sector_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sectors.id"), nullable=False, index=True
    )
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")
    pos_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    pos_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    sector: Mapped[Sector] = relationship("Sector", back_populates="tables")
    sessions: Mapped[list[TableSession]] = relationship("TableSession", back_populates="table")
