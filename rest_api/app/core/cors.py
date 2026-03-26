"""CORS configuration for the Integrador REST API.

Implements REQ-SEC-03:
- Development: localhost ports 5173-5180 (Vite dev servers)
- Production: ALLOWED_ORIGINS env var (comma-separated)
- allow_credentials: true (for HttpOnly cookies)
- Expose X-Request-ID header
"""

from shared.config import settings

# Default origins for local development (all common Vite ports)
DEFAULT_CORS_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://localhost:5178",
    "http://localhost:5179",
    "http://localhost:5180",
]

ALLOWED_HEADERS: list[str] = [
    "Authorization",
    "Content-Type",
    "X-Table-Token",
    "X-Request-ID",
]

EXPOSE_HEADERS: list[str] = [
    "X-Request-ID",
]


def get_cors_origins() -> list[str]:
    """Resolve CORS origins based on environment.

    Production: uses CORS_ORIGINS env var (comma-separated).
    Development: uses DEFAULT_CORS_ORIGINS (localhost ports).
    """
    cors_origins = getattr(settings, "CORS_ORIGINS", None)
    if cors_origins:
        return [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    return DEFAULT_CORS_ORIGINS
