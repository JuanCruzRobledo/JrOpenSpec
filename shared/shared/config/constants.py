"""Shared constants: roles, enums, and configuration values."""

from enum import StrEnum


class Roles(StrEnum):
    """System role identifiers — must match UserBranchRole.role values."""

    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    KITCHEN = "KITCHEN"
    WAITER = "WAITER"


# Roles with management-level access (can manage resources)
MANAGEMENT_ROLES: frozenset[str] = frozenset({Roles.ADMIN, Roles.MANAGER})


class RoundStatus(StrEnum):
    """Lifecycle states for order rounds."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# Brute-force protection
LOGIN_MAX_ATTEMPTS: int = 5
LOGIN_LOCKOUT_SECONDS: int = 60

# Redis key prefixes
REDIS_BLACKLIST_PREFIX: str = "blacklist:"
REDIS_LOGIN_ATTEMPTS_PREFIX: str = "login_attempts:"

# Default CORS origins for development
DEFAULT_CORS_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://localhost:5178",
    "http://localhost:5179",
    "http://localhost:5180",
]
