"""CookingMethod model — system + tenant-scoped cooking technique."""

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class CookingMethod(BaseModel):
    """Cooking method/technique (e.g., Parrilla, Horno, Fritura)."""

    __table_args__ = (
        UniqueConstraint("code", "tenant_id", name="uq_cooking_methods_code_tenant"),
        CheckConstraint(
            "is_system = false OR tenant_id IS NULL",
            name="ck_cooking_methods_system_no_tenant",
        ),
    )

    tenant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
