"""Public API schemas — camelCase field names for frontend consumption."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


def _to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class _CamelModel(BaseModel):
    """Base model with camelCase serialization."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
    )


# ── Public Menu ──


class PublicBadge(_CamelModel):
    code: str
    name: str
    color: str
    icon: str | None = None


class PublicSeal(_CamelModel):
    code: str
    name: str
    color: str
    icon: str | None = None


class PublicAllergenSummary(_CamelModel):
    contains: list[str] = []
    may_contain: list[str] = []
    free_of: list[str] = []


class PublicMenuProduct(_CamelModel):
    id: int
    name: str
    short_description: str | None = None
    price_cents: int
    image_url: str | None = None
    badges: list[PublicBadge] = []
    seals: list[PublicSeal] = []
    dietary_profiles: list[str] = []
    allergen_summary: PublicAllergenSummary | None = None
    cooking_methods: list[str] = []
    flavor_profiles: list[str] = []
    is_available: bool = True


class PublicMenuCategory(_CamelModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    sort_order: int = 0
    products: list[PublicMenuProduct] = []


class PublicBranchInfo(_CamelModel):
    id: int
    name: str
    slug: str
    address: str | None = None
    phone: str | None = None
    open_now: bool = False


class PublicAllergenLegendItem(_CamelModel):
    code: str
    name: str
    icon: str | None = None


class PublicMenuResponse(_CamelModel):
    branch: PublicBranchInfo
    categories: list[PublicMenuCategory] = []
    allergen_legend: list[PublicAllergenLegendItem] = []
    generated_at: datetime


# ── Public Product Detail ──


class PublicProductCrossReaction(_CamelModel):
    code: str
    name: str
    description: str
    severity: str


class PublicProductAllergen(_CamelModel):
    code: str
    name: str
    icon: str | None = None
    presence_type: str
    risk_level: str
    notes: str | None = None
    cross_reactions: list[PublicProductCrossReaction] = []


class PublicProductDietaryProfile(_CamelModel):
    code: str
    name: str
    icon: str | None = None


class PublicProductCookingMethod(_CamelModel):
    code: str
    name: str
    icon: str | None = None


class PublicProductIngredient(_CamelModel):
    name: str
    quantity: float
    unit: str
    is_optional: bool = False


class PublicProductCategory(_CamelModel):
    id: int
    name: str
    slug: str


class PublicProductBranchInfo(_CamelModel):
    id: int
    name: str
    slug: str


class PublicProductDetailResponse(_CamelModel):
    id: int
    name: str
    description: str | None = None
    short_description: str | None = None
    price_cents: int
    image_url: str | None = None
    badges: list[PublicBadge] = []
    seals: list[PublicSeal] = []
    dietary_profiles: list[PublicProductDietaryProfile] = []
    allergens: list[PublicProductAllergen] = []
    cooking_methods: list[PublicProductCookingMethod] = []
    flavor_profiles: list[str] = []
    texture_profiles: list[str] = []
    ingredients: list[PublicProductIngredient] = []
    branch: PublicProductBranchInfo
    category: PublicProductCategory
    generated_at: datetime


# ── Public Branches ──


class PublicBranchItem(_CamelModel):
    id: int
    name: str
    slug: str
    address: str | None = None
    phone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    open_now: bool = False
    product_count: int = 0
    category_count: int = 0


class PublicBranchesResponse(_CamelModel):
    branches: list[PublicBranchItem] = []
    generated_at: datetime


# ── Public Allergens ──


class PublicCrossReactionItem(_CamelModel):
    related_code: str
    related_name: str
    description: str
    severity: str


class PublicAllergenItem(_CamelModel):
    code: str
    name: str
    description: str | None = None
    icon: str | None = None
    is_system: bool = False
    cross_reactions: list[PublicCrossReactionItem] = []


class PublicAllergensResponse(_CamelModel):
    allergens: list[PublicAllergenItem] = []
    generated_at: datetime
