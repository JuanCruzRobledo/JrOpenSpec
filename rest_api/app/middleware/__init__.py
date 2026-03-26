"""Security middlewares package for the Integrador REST API.

Exports a `register_middlewares(app)` function that wires all middlewares
in the correct order. Call this from `create_app()` in main.py.
"""

from starlette.middleware.cors import CORSMiddleware

from shared.config import settings

from rest_api.app.middleware.content_type import ContentTypeValidationMiddleware
from rest_api.app.middleware.correlation_id import CorrelationIdMiddleware
from rest_api.app.middleware.security_headers import SecurityHeadersMiddleware

# Default CORS origins for development (localhost with common Vite ports)
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://localhost:5178",
    "http://localhost:5179",
    "http://localhost:5180",
]

ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-Table-Token",
    "X-Request-ID",
]


def register_middlewares(app):  # noqa: ANN001
    """Register all middlewares in the correct order.

    Starlette processes middlewares in REVERSE registration order,
    so the last added middleware executes first.

    Execution order:
    1. CORS (first — handles preflight before anything else)
    2. ContentTypeValidation
    3. SecurityHeaders
    4. CorrelationId (last — adds X-Request-ID to every response)
    """
    # Registered LAST → executes FIRST
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ContentTypeValidationMiddleware)

    # CORS must be registered FIRST → executes LAST (outermost)
    origins = (
        settings.CORS_ORIGINS.split(",")
        if hasattr(settings, "CORS_ORIGINS") and settings.CORS_ORIGINS
        else DEFAULT_CORS_ORIGINS
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=ALLOWED_HEADERS,
        expose_headers=["X-Request-ID"],
    )


__all__ = [
    "ContentTypeValidationMiddleware",
    "CorrelationIdMiddleware",
    "SecurityHeadersMiddleware",
    "register_middlewares",
]
