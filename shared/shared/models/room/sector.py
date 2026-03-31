"""Sector model — physical area within a branch (e.g., Salon, Terraza, Barra)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.core.branch import Branch
    from shared.models.room.table import Table
    from shared.models.services.waiter_sector_assignment import WaiterSectorAssignment


class Sector(BaseModel):
    """A physical area/section within a restaurant branch."""

    __table_args__ = (
        UniqueConstraint("branch_id", "name", name="uq_sectors_branch_name"),
        UniqueConstraint("branch_id", "prefix", name="uq_sectors_branch_prefix"),
        CheckConstraint("capacity > 0", name="ck_sector_capacity_positive"),
    )

    branch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("branches.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="interior")
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    branch: Mapped[Branch] = relationship("Branch", back_populates="sectors")
    tables: Mapped[list[Table]] = relationship(
        "Table", back_populates="sector", lazy="selectin"
    )
    waiter_assignments: Mapped[list[WaiterSectorAssignment]] = relationship(
        "WaiterSectorAssignment", back_populates="sector"
    )
