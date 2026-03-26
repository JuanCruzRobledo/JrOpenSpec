"""Content-Type validation middleware — rejects mutating requests with wrong content type.

Implements REQ-SEC-02:
- POST/PUT/PATCH must use application/json or application/x-www-form-urlencoded
- Returns 415 Unsupported Media Type for invalid content types
- Exempt paths: /api/billing/webhook, /api/health
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# HTTP methods that require content-type validation
_MUTATING_METHODS = {"POST", "PUT", "PATCH"}

# Allowed content types for mutating requests
_ALLOWED_CONTENT_TYPES = {
    "application/json",
    "application/x-www-form-urlencoded",
}

# Paths exempt from content-type validation
_EXEMPT_PATHS = {
    "/api/billing/webhook",
    "/api/health",
}


def _is_exempt(path: str) -> bool:
    """Check if the request path is exempt from content-type validation."""
    return any(path.startswith(exempt) for exempt in _EXEMPT_PATHS)


def _get_base_content_type(content_type: str | None) -> str | None:
    """Extract the base content type, stripping charset and parameters."""
    if not content_type:
        return None
    # "application/json; charset=utf-8" → "application/json"
    return content_type.split(";")[0].strip().lower()


class ContentTypeValidationMiddleware(BaseHTTPMiddleware):
    """Validate Content-Type header on mutating HTTP requests."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method in _MUTATING_METHODS and not _is_exempt(request.url.path):
            base_type = _get_base_content_type(request.headers.get("content-type"))

            if base_type not in _ALLOWED_CONTENT_TYPES:
                logger.warning(
                    "Rejected request with invalid content-type: %s %s (type=%s)",
                    request.method,
                    request.url.path,
                    base_type,
                )
                return JSONResponse(
                    status_code=415,
                    content={"detail": "Unsupported Media Type"},
                )

        return await call_next(request)
