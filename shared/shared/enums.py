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


# --- Sprint 5: Table & Staff Domain ---


class SectorType(str, Enum):
    """Type of sector within a branch."""

    INTERIOR = "interior"
    TERRAZA = "terraza"
    BARRA = "barra"
    VIP = "vip"


class TableStatus(str, Enum):
    """FSM states for a restaurant table."""

    LIBRE = "libre"
    OCUPADA = "ocupada"
    PEDIDO_SOLICITADO = "pedido_solicitado"
    PEDIDO_CUMPLIDO = "pedido_cumplido"
    CUENTA = "cuenta"
    INACTIVA = "inactiva"


class ShiftType(str, Enum):
    """Work shift for waiter assignments."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"


# Table FSM transition map: current_status -> list of valid next statuses
TABLE_TRANSITIONS: dict[str, list[str]] = {
    TableStatus.LIBRE: [TableStatus.OCUPADA, TableStatus.INACTIVA],
    TableStatus.OCUPADA: [TableStatus.PEDIDO_SOLICITADO, TableStatus.LIBRE],
    TableStatus.PEDIDO_SOLICITADO: [TableStatus.PEDIDO_CUMPLIDO],
    TableStatus.PEDIDO_CUMPLIDO: [TableStatus.CUENTA, TableStatus.PEDIDO_SOLICITADO],
    TableStatus.CUENTA: [TableStatus.LIBRE],
    TableStatus.INACTIVA: [TableStatus.LIBRE],
}

# Urgency score per status — used for waiter dashboard sorting
TABLE_URGENCY_SCORE: dict[str, int] = {
    TableStatus.CUENTA: 50,
    TableStatus.PEDIDO_SOLICITADO: 40,
    TableStatus.PEDIDO_CUMPLIDO: 30,
    TableStatus.OCUPADA: 20,
    TableStatus.LIBRE: 10,
    TableStatus.INACTIVA: 0,
}

# Auto-prefix for table codes per sector type
SECTOR_PREFIX_MAP: dict[str, str] = {
    SectorType.INTERIOR: "INT",
    SectorType.TERRAZA: "TER",
    SectorType.BARRA: "BAR",
    SectorType.VIP: "VIP",
}
