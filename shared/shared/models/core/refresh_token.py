"""RefreshToken model — tracks issued refresh tokens for rotation and reuse detection."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.core.user import User


class RefreshToken(BaseModel):
    """Stores refresh tokens for rotation tracking and reuse detection.

    Each token belongs to a family (family_id). When a refresh token is
    rotated, the old one is revoked and a new one with the same family_id
    is created. If a revoked token is reused, ALL tokens in the family
    are invalidated (potential token theft).
    """

    jti: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    family_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    user: Mapped[User] = relationship("User")
