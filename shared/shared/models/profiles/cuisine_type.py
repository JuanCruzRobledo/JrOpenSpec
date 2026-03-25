"""CuisineType model — tenant-scoped cuisine classification."""

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class CuisineType(BaseModel):
    """Cuisine type (e.g., Argentina, Italiana, Japonesa)."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_cuisine_types_tenant_name"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
