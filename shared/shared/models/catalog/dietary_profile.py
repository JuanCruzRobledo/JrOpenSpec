"""DietaryProfile model — system + tenant-scoped dietary profile definitions."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class DietaryProfile(BaseModel):
    """Dietary profile (e.g., Vegano, Sin Gluten, Keto). System profiles are immutable."""

    __table_args__ = (
        UniqueConstraint("code", "tenant_id", name="uq_dietary_profiles_code_tenant"),
        CheckConstraint(
            "is_system = false OR tenant_id IS NULL",
            name="ck_dietary_profiles_system_no_tenant",
        ),
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    tenant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
