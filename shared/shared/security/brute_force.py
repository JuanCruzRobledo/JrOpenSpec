"""Redis-backed login abuse protection with a single explicit contract.

This module tracks failed login attempts in a sliding window per IP+email pair
and applies progressive lockouts. Redis failures remain fail-open for login
attempt accounting so authentication itself is not blocked by rate-limit state.
"""

import hashlib
import logging
import time
from dataclasses import dataclass

import redis.asyncio as aioredis

from shared.config.constants import LOGIN_LOCKOUT_SECONDS, LOGIN_MAX_ATTEMPTS

logger = logging.getLogger(__name__)

_KEY_PREFIX = "auth:login"
_WINDOW_SECONDS = 300
_MAX_LOCKOUT_SECONDS = 900


@dataclass(slots=True)
class LoginProtectionState:
    """Resolved login protection state for one IP+email tuple."""

    blocked: bool
    retry_after: int = 0
    attempts: int = 0


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_identifier(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _window_key(email: str, ip_address: str) -> str:
    return f"{_KEY_PREFIX}:window:{_hash_identifier(f'{ip_address}:{_normalize_email(email)}')}"


def _lockout_key(email: str, ip_address: str) -> str:
    return f"{_KEY_PREFIX}:lockout:{_hash_identifier(f'{ip_address}:{_normalize_email(email)}')}"


def _lockout_level_key(email: str, ip_address: str) -> str:
    return f"{_KEY_PREFIX}:lockout-level:{_hash_identifier(f'{ip_address}:{_normalize_email(email)}')}"


async def check_login_protection(
    redis_client: aioredis.Redis,
    email: str,
    ip_address: str,
) -> LoginProtectionState:
    """Resolve whether login is currently blocked for one IP+email pair."""
    try:
        lockout_key = _lockout_key(email, ip_address)
        retry_after = await redis_client.ttl(lockout_key)
        if retry_after is not None and retry_after > 0:
            return LoginProtectionState(blocked=True, retry_after=retry_after)

        window_key = _window_key(email, ip_address)
        now = int(time.time())
        await redis_client.zremrangebyscore(window_key, 0, now - _WINDOW_SECONDS)
        attempts = await redis_client.zcard(window_key)
        return LoginProtectionState(blocked=False, attempts=int(attempts or 0))
    except Exception:
        logger.exception("Redis error during login protection check for %s", email)
        return LoginProtectionState(blocked=False)


async def record_failed_attempt(
    redis_client: aioredis.Redis,
    email: str,
    ip_address: str,
) -> LoginProtectionState:
    """Record a failed login and apply progressive lockout when needed."""
    window_key = _window_key(email, ip_address)
    lockout_key = _lockout_key(email, ip_address)
    lockout_level_key = _lockout_level_key(email, ip_address)
    now = int(time.time())
    member = f"{now}:{time.monotonic_ns()}"

    try:
        pipe = redis_client.pipeline()
        pipe.zadd(window_key, {member: now})
        pipe.zremrangebyscore(window_key, 0, now - _WINDOW_SECONDS)
        pipe.zcard(window_key)
        pipe.expire(window_key, _WINDOW_SECONDS)
        results = await pipe.execute()
        attempts = int(results[2] or 0)

        if attempts < LOGIN_MAX_ATTEMPTS:
            logger.info("Failed login attempt %d for %s from %s", attempts, email, ip_address)
            return LoginProtectionState(blocked=False, attempts=attempts)

        level = await redis_client.incr(lockout_level_key)
        duration = min(LOGIN_LOCKOUT_SECONDS * (2 ** (max(level, 1) - 1)), _MAX_LOCKOUT_SECONDS)
        pipe = redis_client.pipeline()
        pipe.expire(lockout_level_key, _MAX_LOCKOUT_SECONDS)
        pipe.setex(lockout_key, duration, str(attempts))
        pipe.delete(window_key)
        await pipe.execute()

        logger.warning(
            "Login lockout applied for %s from %s: attempts=%d duration=%ds level=%d",
            email,
            ip_address,
            attempts,
            duration,
            level,
        )
        return LoginProtectionState(blocked=True, retry_after=duration, attempts=attempts)
    except Exception:
        logger.exception("Redis error recording failed attempt for %s", email)
        return LoginProtectionState(blocked=False)


async def reset_login_protection(
    redis_client: aioredis.Redis,
    email: str,
    ip_address: str,
) -> None:
    """Reset login-abuse state after a successful login."""
    try:
        await redis_client.delete(
            _window_key(email, ip_address),
            _lockout_key(email, ip_address),
            _lockout_level_key(email, ip_address),
        )
    except Exception:
        logger.exception("Redis error resetting login protection for %s", email)


__all__ = [
    "LoginProtectionState",
    "check_login_protection",
    "record_failed_attempt",
    "reset_login_protection",
]
