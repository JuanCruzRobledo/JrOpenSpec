"""WaiterSectorAssignment model — waiter-to-sector assignment tracking."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.core.branch import Branch
    from shared.models.core.user import User
    from shared.models.room.sector import Sector


class WaiterSectorAssignment(BaseModel):
    """Tracks which waiter is assigned to which sector. Partial unique on active assignments."""

    __table_args__ = (
        # Partial unique index: only one active assignment per user per sector
        Index(
            "uq_waiter_sector_active",
            "user_id",
            "sector_id",
            unique=True,
            postgresql_where="unassigned_at IS NULL",
        ),
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
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    unassigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped[User] = relationship("User")
    branch: Mapped[Branch] = relationship("Branch", back_populates="waiter_assignments")
    sector: Mapped[Sector] = relationship("Sector", back_populates="waiter_assignments")
