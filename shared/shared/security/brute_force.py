"""Redis-based brute-force protection for login attempts.

Implements REQ-RATE-02:
- Tracks consecutive failed login attempts per email
- Key format: login_attempts:{email}
- Lockout after MAX_ATTEMPTS (5) failed attempts
- Lockout duration: LOCKOUT_SECONDS (900 = 15 minutes)
- Reset counter on successful login
- Fail-open: if Redis is down, allow the attempt (auth itself is fail-closed)
"""

import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Brute-force protection constants
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 900  # 15 minutes
_KEY_PREFIX = "login_attempts"


def _key(email: str) -> str:
    """Build the Redis key for a given email."""
    return f"{_KEY_PREFIX}:{email.lower()}"


async def check_brute_force(redis_client: aioredis.Redis, email: str) -> bool:
    """Check if the email is currently locked out due to too many failed attempts.

    Returns True if the login attempt should be BLOCKED (locked out).
    Returns False if the attempt is allowed.

    On Redis failure, returns False (fail-open for brute-force check;
    the JWT blacklist is fail-closed which is the critical path).
    """
    try:
        attempts = await redis_client.get(_key(email))
        if attempts is not None and int(attempts) >= MAX_ATTEMPTS:
            ttl = await redis_client.ttl(_key(email))
            logger.warning(
                "Login blocked for %s: %s attempts, %ss remaining",
                email,
                attempts,
                ttl,
            )
            return True
    except Exception:
        logger.exception("Redis error during brute-force check for %s", email)
        # Fail-open: allow the attempt if Redis is down
    return False


async def record_failed_attempt(redis_client: aioredis.Redis, email: str) -> int:
    """Increment the failed attempt counter for an email.

    Returns the new count. Sets TTL on first attempt.
    """
    key = _key(email)
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, LOCKOUT_SECONDS)
        results = await pipe.execute()
        count = results[0]
        logger.info("Failed login attempt %d for %s", count, email)
        return count
    except Exception:
        logger.exception("Redis error recording failed attempt for %s", email)
        return 0


async def reset_attempts(redis_client: aioredis.Redis, email: str) -> None:
    """Reset the failed attempt counter after a successful login."""
    try:
        await redis_client.delete(_key(email))
    except Exception:
        logger.exception("Redis error resetting attempts for %s", email)
