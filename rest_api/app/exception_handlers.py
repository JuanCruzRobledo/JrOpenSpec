"""Exception handlers — map domain exceptions to standardized JSON responses.

Registered in main.py at application startup.  All errors follow the
format: ``{"detail": "<human-readable message>"}``
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from shared.exceptions import AppError

logger = logging.getLogger(__name__)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle all AppError subclasses using their status_code attribute."""
    status_code = getattr(exc, "status_code", 500)

    if status_code >= 500:
        logger.error(
            "Server error [%s %s]: %s — %s",
            request.method,
            request.url.path,
            exc.message,
            exc.detail,
        )
    else:
        logger.warning(
            "Client error %d [%s %s]: %s",
            status_code,
            request.method,
            request.url.path,
            exc.message,
        )

    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Override FastAPI's default 422 handler to use consistent error format.

    Returns the first validation error message as ``detail`` for simplicity.
    The full error list is logged for debugging.
    """
    errors = exc.errors()
    logger.warning(
        "Validation error [%s %s]: %s",
        request.method,
        request.url.path,
        errors,
    )

    # Build a human-readable message from the first error
    if errors:
        first = errors[0]
        loc = " -> ".join(str(part) for part in first.get("loc", []))
        msg = first.get("msg", "Validation error")
        detail = f"{loc}: {msg}" if loc else msg
    else:
        detail = "Validation error"

    return JSONResponse(
        status_code=422,
        content={"detail": detail},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application.

    Called from create_app() in main.py.
    """
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
