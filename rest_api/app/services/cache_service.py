"""Cache service — Redis get_or_set with TTL and pattern-based invalidation.

This is pure infrastructure; no FastAPI imports.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Attempt to use orjson for speed, fall back to stdlib json
try:
    import orjson

    def _dumps(obj: Any) -> bytes:
        return orjson.dumps(obj)

    def _loads(raw: str | bytes) -> Any:
        return orjson.loads(raw)

except ImportError:
    import json as _json

    def _dumps(obj: Any) -> bytes:  # type: ignore[misc]
        return _json.dumps(obj, default=str).encode()

    def _loads(raw: str | bytes) -> Any:  # type: ignore[misc]
        return _json.loads(raw)


class CacheService:
    """Redis-backed cache with get_or_set and invalidation."""

    def __init__(self, redis: aioredis.Redis, default_ttl: int = 300) -> None:
        self._redis = redis
        self._default_ttl = default_ttl

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: int | None = None,
    ) -> Any:
        """Return cached value or compute via factory, store, and return.

        On Redis failure, falls through to factory (fail-open for reads).
        """
        try:
            cached = await self._redis.get(key)
            if cached is not None:
                return _loads(cached)
        except Exception:
            logger.warning("Cache GET failed for key=%s, falling through", key, exc_info=True)

        result = await factory()

        try:
            serialized = _dumps(result)
            await self._redis.setex(key, ttl or self._default_ttl, serialized)
        except Exception:
            logger.warning("Cache SET failed for key=%s", key, exc_info=True)

        return result

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob pattern using SCAN (non-blocking).

        Returns count of deleted keys.
        """
        deleted = 0
        try:
            async for key in self._redis.scan_iter(match=pattern, count=100):
                await self._redis.delete(key)
                deleted += 1
        except Exception:
            logger.warning("Cache invalidate_pattern failed for pattern=%s", pattern, exc_info=True)
        return deleted

    async def invalidate_keys(self, *keys: str) -> int:
        """Delete specific keys. Returns count deleted."""
        if not keys:
            return 0
        try:
            return await self._redis.delete(*keys)
        except Exception:
            logger.warning("Cache invalidate_keys failed for keys=%s", keys, exc_info=True)
            return 0
