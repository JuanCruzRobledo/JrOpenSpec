"""UserBranchRole model — maps users to branches with specific roles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.core.branch import Branch
    from shared.models.core.user import User


class UserBranchRole(BaseModel):
    """Associates a user with a branch and a role (owner, manager, chef, waiter, cashier, kitchen_display)."""

    __table_args__ = (
        UniqueConstraint("user_id", "branch_id", "role", name="uq_user_branch_roles_user_branch_role"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    branch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("branches.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="branch_roles")
    branch: Mapped[Branch] = relationship("Branch")
