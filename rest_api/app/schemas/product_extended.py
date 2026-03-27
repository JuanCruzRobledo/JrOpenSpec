"""Product extended schemas — sub-resource inputs for product enrichment."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator
from typing import Annotated

from shared.enums import (
    AllergenSeverity,
    FlavorProfileEnum,
    IngredientUnit,
    PresenceType,
    TextureProfileEnum,
)


class ProductAllergenInput(BaseModel):
    """Input for assigning an allergen to a product."""

    allergen_id: int
    presence_type: PresenceType
    risk_level: AllergenSeverity
    notes: str | None = None

    @field_validator("risk_level")
    @classmethod
    def free_of_must_be_low(cls, v: AllergenSeverity, info) -> AllergenSeverity:
        """Validate free_of presence must have low risk level."""
        presence = info.data.get("presence_type")
        if presence == PresenceType.FREE_OF and v != AllergenSeverity.LOW:
            msg = "free_of presence must have low risk level"
            raise ValueError(msg)
        return v


class ProductAllergenRead(BaseModel):
    """Allergen association in a product response."""

    allergen_id: int
    codigo: str
    nombre: str
    icono: str | None = None
    tipo_presencia: str
    nivel_riesgo: str
    notas: str | None = None


class ProductDietarySet(BaseModel):
    """Input for setting dietary profiles on a product."""

    profile_ids: list[int]


class ProductCookingMethodSet(BaseModel):
    """Input for setting cooking methods on a product."""

    method_ids: list[int]


class ProductFlavorProfileSet(BaseModel):
    """Input for setting flavor profiles on a product."""

    profiles: list[FlavorProfileEnum]


class ProductTextureProfileSet(BaseModel):
    """Input for setting texture profiles on a product."""

    profiles: list[TextureProfileEnum]


class ProductIngredientInput(BaseModel):
    """Input for a single ingredient in the ingredient list."""

    nombre: Annotated[str, Field(min_length=1, max_length=200)]
    cantidad: Annotated[Decimal, Field(gt=0)]
    unidad: IngredientUnit
    orden: int = 0
    es_opcional: bool = False
    notas: str | None = None


class ProductIngredientSet(BaseModel):
    """Input for replacing all ingredients on a product."""

    ingredientes: list[ProductIngredientInput]


class ProductIngredientRead(BaseModel):
    """Ingredient in a product response."""

    id: int
    nombre: str
    cantidad: Decimal
    unidad: str
    orden: int
    es_opcional: bool = False
    notas: str | None = None


class ProductBadgeInput(BaseModel):
    """Input for assigning a badge to a product."""

    badge_id: int
    sort_order: int = 0


class ProductBadgeSet(BaseModel):
    """Input for replacing all badges on a product."""

    badges: list[ProductBadgeInput]


class ProductSealInput(BaseModel):
    """Input for assigning a seal to a product."""

    seal_id: int
    sort_order: int = 0


class ProductSealSet(BaseModel):
    """Input for replacing all seals on a product."""

    seals: list[ProductSealInput]
