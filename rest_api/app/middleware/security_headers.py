"""Security headers middleware — adds protective HTTP headers to all responses.

Implements REQ-SEC-01:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: restrictive defaults
- Content-Security-Policy: default-src 'self'
- Strict-Transport-Security: only in production
- Server header: removed
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from shared.config import settings

logger = logging.getLogger(__name__)

# Headers applied to every response
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), "
        "interest-cohort=(), payment=(), usb=()"
    ),
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
}

# HSTS header — only added in production to avoid dev issues
_HSTS_VALUE = "max-age=63072000; includeSubDomains; preload"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security headers into every HTTP response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Apply standard security headers
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value

        # HSTS only in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = _HSTS_VALUE

        # Remove server header to avoid fingerprinting
        if "server" in response.headers:
            del response.headers["server"]

        return response
