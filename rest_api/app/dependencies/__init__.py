"""FastAPI dependencies package.

NOTE: This package replaces the original dependencies.py module.
Original exports are preserved here. Batch B should add get_current_user,
require_roles, etc. to this __init__.py during merge.
"""

from shared.infrastructure.db import get_db

from rest_api.app.dependencies.table_token import get_table_session

__all__ = ["get_db", "get_table_session"]
