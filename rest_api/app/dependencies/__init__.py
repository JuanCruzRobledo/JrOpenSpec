"""FastAPI dependencies package — auth, tenant, table-token, and infrastructure injection.

Consolidates Batch B (dependencies.py) and Batch C (dependencies/ package).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import redis.asyncio as aioredis
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import settings
from shared.exceptions import AuthenticationError, InsufficientRoleError
from shared.infrastructure.db import get_db
from shared.infrastructure.redis import get_redis
from shared.security.table_tokens import verify_table_token as _verify_table_token

from rest_api.app.dependencies.table_token import get_table_session

logger = logging.getLogger(__name__)

__all__ = [
    "get_db",
    "get_current_user",
    "get_optional_user",
    "get_current_tenant",
    "require_roles",
    "verify_table_token_dep",
    "get_table_session",
]


# ---------------------------------------------------------------------------
# JWT helpers (imported lazily to avoid circular deps)
# ---------------------------------------------------------------------------

def _decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT access token — delegates to shared.security.jwt."""
    from shared.security.jwt import decode_token
    return decode_token(token)


async def _is_blacklisted(redis_client: aioredis.Redis, jti: str) -> bool:
    """Check Redis blacklist — delegates to shared.security.blacklist."""
    from shared.security.blacklist import is_blacklisted
    return await is_blacklisted(redis_client, jti)


# ---------------------------------------------------------------------------
# Core dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
) -> dict[str, Any]:
    """Extract and validate the JWT from the Authorization header.

    Steps:
    1. Parse ``Authorization: Bearer <token>``
    2. Decode the JWT (validates signature + expiration)
    3. Check Redis blacklist (fail-closed: Redis down = 401)
    4. Return user payload dict

    Raises:
        AuthenticationError: On missing/invalid/blacklisted token or Redis failure.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError(message="Missing or invalid authorization header")

    token = auth_header[7:]  # Strip "Bearer "

    try:
        payload = _decode_token(token)
    except Exception as exc:
        raise AuthenticationError(message="Invalid or expired token") from exc

    # Fail-closed blacklist check
    jti = payload.get("jti")
    if not jti:
        raise AuthenticationError(message="Token missing jti claim")

    if await _is_blacklisted(redis_client, jti):
        raise AuthenticationError(message="Token has been revoked")

    return payload


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
) -> dict[str, Any] | None:
    """Like get_current_user but returns None when no token is present."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        return await get_current_user(request, db, redis_client)
    except AuthenticationError:
        return None


async def get_current_tenant(
    user: dict[str, Any] = Depends(get_current_user),
) -> int:
    """Extract tenant_id from the authenticated user's JWT payload."""
    tenant_id = user.get("tenant_id")
    if tenant_id is None:
        raise AuthenticationError(message="Token missing tenant_id claim")
    return int(tenant_id)


def require_roles(*roles: str) -> Callable:
    """Factory that returns a dependency checking the user holds at least one of *roles*."""

    async def _check_roles(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        user_roles = set(user.get("roles", []))
        if not user_roles & set(roles):
            raise InsufficientRoleError(
                message="Insufficient role",
                detail=f"Required one of {list(roles)}, got {list(user_roles)}",
            )
        return user

    return _check_roles


async def verify_table_token_dep(request: Request) -> dict[str, Any]:
    """Extract and verify the HMAC table token from X-Table-Token header."""
    token = request.headers.get("X-Table-Token")
    if not token:
        raise AuthenticationError(message="Missing X-Table-Token header")

    return _verify_table_token(settings.TABLE_TOKEN_SECRET, token)
