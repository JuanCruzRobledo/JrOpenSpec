"""Tenant model — top-level multi-tenancy entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.core.branch import Branch
    from shared.models.core.user import User


class Tenant(BaseModel):
    """Represents a restaurant organization (multi-tenant root)."""

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Relationships
    branches: Mapped[list[Branch]] = relationship("Branch", back_populates="tenant")
    users: Mapped[list[User]] = relationship("User", back_populates="tenant")
