"""FastAPI dependencies — re-exports from shared for convenience."""

from shared.infrastructure.db import get_db

__all__ = ["get_db"]
