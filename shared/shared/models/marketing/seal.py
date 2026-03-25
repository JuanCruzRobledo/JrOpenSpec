"""Seal model — certification/dietary seal for products (e.g., Sin TACC, Vegano)."""

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class Seal(BaseModel):
    """A dietary/certification seal (e.g., Sin TACC, Vegano, Organico)."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_seals_tenant_name"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
