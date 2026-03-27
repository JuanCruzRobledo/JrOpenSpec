"""Category model — top-level menu grouping within a tenant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.subcategory import Subcategory
    from shared.models.core.branch import Branch
    from shared.models.core.tenant import Tenant


class Category(BaseModel):
    """Menu category (e.g., Entradas, Platos Principales, Postres)."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_categories_tenant_slug"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    branch_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("branches.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_home: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Relationships
    tenant: Mapped[Tenant] = relationship("Tenant")
    branch: Mapped[Branch | None] = relationship("Branch")
    subcategories: Mapped[list[Subcategory]] = relationship("Subcategory", back_populates="category")
