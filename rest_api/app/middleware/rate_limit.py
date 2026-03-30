"""Rate limiting setup and shared auth rate-limit response helpers.

Implements REQ-RATE-01:
- Public endpoints: 100/min per IP
- Authenticated endpoints: 30/min per user_id
- Login endpoint: 5/min per email

In-memory storage for Phase 2; Redis backend planned for Phase 12.
"""

import logging

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

LOGIN_RATE_LIMIT_DETAIL = "Too many login attempts"
LOGIN_RATE_LIMIT_CODE = "login_rate_limited"


def _get_user_id_or_ip(request: Request) -> str:
    """Key function: use user_id from JWT if available, otherwise fall back to IP."""
    # After get_current_user runs, user info is on request.state
    user = getattr(request.state, "current_user", None)
    if user and isinstance(user, dict):
        return f"user:{user.get('sub', get_remote_address(request))}"
    return get_remote_address(request)


def _get_login_key(request: Request) -> str:
    """Key function for login: rate limit by email from request body.

    Falls back to IP if email cannot be extracted (body not yet parsed).
    """
    # slowapi calls key_func before the route handler, so we use IP
    # The actual brute-force per-email protection is in brute_force.py (Redis-based)
    return get_remote_address(request)


# Global limiter instance — attach to app.state in main.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://",
)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    logger.warning(
        "Rate limit exceeded: %s %s (limit=%s)",
        request.method,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests"},
    )


def build_login_rate_limit_response(retry_after: int) -> JSONResponse:
    """Build the stable 429 response body for auth login protection."""
    retry_after = max(retry_after, 1)
    return JSONResponse(
        status_code=429,
        content={
            "detail": LOGIN_RATE_LIMIT_DETAIL,
            "code": LOGIN_RATE_LIMIT_CODE,
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


__all__ = [
    "limiter",
    "rate_limit_exceeded_handler",
    "build_login_rate_limit_response",
    "LOGIN_RATE_LIMIT_CODE",
    "LOGIN_RATE_LIMIT_DETAIL",
]
