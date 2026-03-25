"""CookingMethod model — tenant-scoped cooking technique."""

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class CookingMethod(BaseModel):
    """Cooking method/technique (e.g., A la parrilla, Frito, Al horno)."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_cooking_methods_tenant_name"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
