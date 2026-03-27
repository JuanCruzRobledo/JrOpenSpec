"""Shared enums for domain models — Sprint 4: Menu Domain."""

from enum import Enum


class PresenceType(str, Enum):
    """How an allergen relates to a product."""

    CONTAINS = "contains"
    MAY_CONTAIN = "may_contain"
    FREE_OF = "free_of"


class AllergenSeverity(str, Enum):
    """Severity level for allergen presence or cross-reactions."""

    LOW = "low"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"


class IngredientUnit(str, Enum):
    """Measurement units for product ingredients."""

    G = "g"
    KG = "kg"
    ML = "ml"
    L = "l"
    UNIT = "unit"
    TBSP = "tbsp"
    TSP = "tsp"
    CUP = "cup"
    OZ = "oz"
    LB = "lb"
    PINCH = "pinch"


class FlavorProfileEnum(str, Enum):
    """Valid flavor profile values for Product.flavor_profiles ARRAY."""

    SWEET = "sweet"
    SALTY = "salty"
    SOUR = "sour"
    BITTER = "bitter"
    UMAMI = "umami"
    SPICY = "spicy"


class TextureProfileEnum(str, Enum):
    """Valid texture profile values for Product.texture_profiles ARRAY."""

    CRISPY = "crispy"
    CREAMY = "creamy"
    CRUNCHY = "crunchy"
    SOFT = "soft"
    CHEWY = "chewy"
    LIQUID = "liquid"


class BatchPriceOperation(str, Enum):
    """Operation types for batch price updates."""

    FIXED_ADD = "fixed_add"
    FIXED_SUBTRACT = "fixed_subtract"
    PERCENTAGE_INCREASE = "percentage_increase"
    PERCENTAGE_DECREASE = "percentage_decrease"
