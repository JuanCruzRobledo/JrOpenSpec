"""Product model — menu item within a subcategory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import BaseModel

if TYPE_CHECKING:
    from shared.models.catalog.branch_product import BranchProduct
    from shared.models.catalog.product_allergen import ProductAllergen
    from shared.models.catalog.product_badge import ProductBadge
    from shared.models.catalog.product_cooking_method import ProductCookingMethod
    from shared.models.catalog.product_dietary_profile import ProductDietaryProfile
    from shared.models.catalog.product_ingredient import ProductIngredient
    from shared.models.catalog.product_seal import ProductSeal
    from shared.models.catalog.subcategory import Subcategory
    from shared.models.core.tenant import Tenant
    from shared.models.profiles.cooking_method import CookingMethod
    from shared.models.profiles.cuisine_type import CuisineType
    from shared.models.profiles.flavor_profile import FlavorProfile
    from shared.models.profiles.texture_profile import TextureProfile
    from shared.models.recipes.recipe import Recipe


class Product(BaseModel):
    """A menu product/item."""

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_products_tenant_slug"),
        CheckConstraint("base_price_cents >= 0", name="ck_products_price_positive"),
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenants.id"), nullable=False, index=True
    )
    subcategory_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("subcategories.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    base_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_visible_in_menu: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_popular: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Legacy FK columns (kept for backwards compat, prefer junction tables)
    cooking_method_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("cooking_methods.id"), nullable=True
    )
    flavor_profile_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("flavor_profiles.id"), nullable=True
    )
    texture_profile_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("texture_profiles.id"), nullable=True
    )
    cuisine_type_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("cuisine_types.id"), nullable=True
    )

    # Sprint 4: ARRAY columns for flavor/texture profiles
    flavor_profiles_array: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(20)), nullable=True, server_default="{}"
    )
    texture_profiles_array: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(20)), nullable=True, server_default="{}"
    )

    # ── Relationships ──

    tenant: Mapped[Tenant] = relationship("Tenant")
    subcategory: Mapped[Subcategory] = relationship("Subcategory", back_populates="products")
    branch_products: Mapped[list[BranchProduct]] = relationship("BranchProduct", back_populates="product")
    product_allergens: Mapped[list[ProductAllergen]] = relationship(
        "ProductAllergen", back_populates="product", cascade="all, delete-orphan"
    )
    recipe: Mapped[Recipe | None] = relationship("Recipe", back_populates="product", uselist=False)

    # Legacy FK relationships
    cooking_method: Mapped[CookingMethod | None] = relationship("CookingMethod")
    flavor_profile: Mapped[FlavorProfile | None] = relationship("FlavorProfile")
    texture_profile: Mapped[TextureProfile | None] = relationship("TextureProfile")
    cuisine_type: Mapped[CuisineType | None] = relationship("CuisineType")

    # Sprint 4 junction relationships
    product_cooking_methods: Mapped[list[ProductCookingMethod]] = relationship(
        "ProductCookingMethod", cascade="all, delete-orphan"
    )
    product_dietary_profiles: Mapped[list[ProductDietaryProfile]] = relationship(
        "ProductDietaryProfile", cascade="all, delete-orphan"
    )
    product_badges: Mapped[list[ProductBadge]] = relationship(
        "ProductBadge", cascade="all, delete-orphan"
    )
    product_seals: Mapped[list[ProductSeal]] = relationship(
        "ProductSeal", cascade="all, delete-orphan"
    )
    ingredients: Mapped[list[ProductIngredient]] = relationship(
        "ProductIngredient", back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductIngredient.sort_order",
    )
