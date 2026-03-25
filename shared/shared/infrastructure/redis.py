"""Redis infrastructure: async client factory."""

import logging

import redis.asyncio as aioredis

from shared.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return a shared async Redis client, creating it on first call."""
    global _redis_client  # noqa: PLW0603
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        logger.info("Redis client created for %s", settings.REDIS_URL)
    return _redis_client


async def close_redis() -> None:
    """Close the Redis client connection if it exists."""
    global _redis_client  # noqa: PLW0603
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")
