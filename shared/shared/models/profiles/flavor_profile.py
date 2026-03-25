"""FlavorProfile model — tenant-scoped flavor descriptor."""

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class FlavorProfile(BaseModel):
    """Flavor profile (e.g., Dulce, Salado, Umami, Picante)."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_flavor_profiles_tenant_name"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
