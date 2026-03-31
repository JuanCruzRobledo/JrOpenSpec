"""WaiterSectorAssignment model — daily waiter-to-sector assignment by shift."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.core.branch import Branch
    from shared.models.core.user import User
    from shared.models.room.sector import Sector


class WaiterSectorAssignment(BaseModel):
    """Daily waiter-to-sector assignment by shift."""

    __table_args__ = (
        UniqueConstraint(
            "user_id", "sector_id", "date", "shift",
            name="uq_waiter_sector_date_shift",
        ),
        Index("ix_assignments_date_shift", "date", "shift"),
        Index("ix_assignments_waiter_date", "user_id", "date"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    branch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("branches.id"), nullable=False, index=True
    )
    sector_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sectors.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    shift: Mapped[str] = mapped_column(String(15), nullable=False)

    # Relationships
    user: Mapped[User] = relationship("User")
    branch: Mapped[Branch] = relationship("Branch", back_populates="waiter_assignments")
    sector: Mapped[Sector] = relationship("Sector", back_populates="waiter_assignments")
