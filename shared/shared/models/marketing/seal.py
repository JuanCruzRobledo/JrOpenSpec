"""Seal model — certification/dietary seal for products."""

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class Seal(BaseModel):
    """A dietary/certification seal (e.g., Orgánico, Producto local, Sin conservantes)."""

    __table_args__ = (
        UniqueConstraint("code", "tenant_id", name="uq_seals_code_tenant"),
        CheckConstraint(
            "is_system = false OR tenant_id IS NULL",
            name="ck_seals_system_no_tenant",
        ),
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, server_default="#000000")
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    tenant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
