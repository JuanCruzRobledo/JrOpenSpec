"""Badge model — visual labels for products (e.g., Nuevo, Popular)."""

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class Badge(BaseModel):
    """A visual badge/label for products (e.g., Nuevo, Popular, Chef Recomienda)."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_badges_tenant_name"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
