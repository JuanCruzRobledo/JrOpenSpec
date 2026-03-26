"""FastAPI dependency for table token validation.

Extracts and verifies the X-Table-Token header using HMAC-SHA256.
Used by diner-facing endpoints (pwaMenu) that authenticate via table session.
"""

import logging

from fastapi import Header, HTTPException

from shared.config import settings
from shared.security.table_tokens import verify_table_token

from rest_api.app.schemas.table_token import TableTokenPayload

logger = logging.getLogger(__name__)


async def get_table_session(
    x_table_token: str = Header(..., alias="X-Table-Token"),
) -> TableTokenPayload:
    """Extract and verify the table token from the X-Table-Token header.

    Returns a TableTokenPayload with branch_id, table_id, session_id.

    Raises:
        HTTPException 401: If the token is missing, invalid, or expired.
    """
    secret = getattr(settings, "TABLE_TOKEN_SECRET", None)
    if not secret:
        logger.error("TABLE_TOKEN_SECRET not configured")
        raise HTTPException(status_code=500, detail="Server configuration error")

    try:
        payload = verify_table_token(secret, x_table_token)
        return TableTokenPayload(**payload)
    except ValueError as exc:
        logger.warning("Table token validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired table token") from exc
