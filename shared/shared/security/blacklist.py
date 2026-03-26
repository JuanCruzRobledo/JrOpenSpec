"""Redis-based JWT blacklist with fail-closed pattern.

If Redis is unreachable, ALL tokens are treated as blacklisted (rejected).
This is a security decision: we prefer denying service over accepting
potentially-revoked tokens.
"""

import logging

import redis.asyncio as aioredis

from shared.config.constants import REDIS_BLACKLIST_PREFIX

logger = logging.getLogger(__name__)


async def add_to_blacklist(redis_client: aioredis.Redis, jti: str, ttl_seconds: int) -> None:
    """Add a token JTI to the blacklist with a TTL matching remaining token life.

    Args:
        redis_client: Async Redis client.
        jti: The JWT ID to blacklist.
        ttl_seconds: Time-to-live in seconds (should match remaining token expiry).
    """
    key = f"{REDIS_BLACKLIST_PREFIX}{jti}"
    try:
        await redis_client.setex(key, ttl_seconds, "1")
        logger.debug("Blacklisted token jti=%s ttl=%ds", jti, ttl_seconds)
    except Exception:
        logger.error("Failed to blacklist token jti=%s — Redis error", jti)
        # Fail-closed: even if we can't write, is_blacklisted will reject
        # when Redis is down, so this is safe.
        raise


async def is_blacklisted(redis_client: aioredis.Redis, jti: str) -> bool:
    """Check if a token JTI is blacklisted.

    FAIL-CLOSED: If Redis is unreachable, returns True (token rejected).

    Args:
        redis_client: Async Redis client.
        jti: The JWT ID to check.

    Returns:
        True if blacklisted or Redis is unreachable, False if valid.
    """
    key = f"{REDIS_BLACKLIST_PREFIX}{jti}"
    try:
        result = await redis_client.get(key)
        return result is not None
    except Exception:
        logger.error(
            "Redis unreachable during blacklist check for jti=%s — FAIL CLOSED (rejecting token)",
            jti,
        )
        return True  # Fail-closed: Redis down → reject token
