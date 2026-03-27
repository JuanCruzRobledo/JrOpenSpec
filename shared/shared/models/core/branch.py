"""Branch model — physical restaurant location within a tenant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.branch_product import BranchProduct
    from shared.models.core.tenant import Tenant
    from shared.models.room.sector import Sector
    from shared.models.services.waiter_sector_assignment import WaiterSectorAssignment


class Branch(BaseModel):
    """Represents a physical restaurant branch/location."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_branches_tenant_slug"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="America/Argentina/Buenos_Aires"
    )
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    opening_time: Mapped[str] = mapped_column(String(5), nullable=False, default="09:00", server_default="09:00")
    closing_time: Mapped[str] = mapped_column(String(5), nullable=False, default="23:00", server_default="23:00")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Relationships
    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="branches")
    sectors: Mapped[list[Sector]] = relationship("Sector", back_populates="branch")
    branch_products: Mapped[list[BranchProduct]] = relationship("BranchProduct", back_populates="branch")
    waiter_assignments: Mapped[list[WaiterSectorAssignment]] = relationship(
        "WaiterSectorAssignment", back_populates="branch"
    )
