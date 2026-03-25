"""Repository layer — data access abstraction."""

from shared.repositories.base import BaseRepository
from shared.repositories.branch import BranchRepository
from shared.repositories.tenant import TenantRepository

__all__ = [
    "BaseRepository",
    "BranchRepository",
    "TenantRepository",
]
