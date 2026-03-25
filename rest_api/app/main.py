"""FastAPI application factory and lifespan management."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from shared.config import settings
from shared.infrastructure.db import engine
from shared.infrastructure.redis import close_redis

from app.routers import health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info(
        "Starting Integrador API [env=%s, debug=%s]",
        settings.ENVIRONMENT,
        settings.DEBUG,
    )

    # Verify database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        logger.info("Database connection verified")
    except Exception:
        logger.exception("Failed to verify database connection")

    yield

    # Shutdown
    logger.info("Shutting down Integrador API")
    await engine.dispose()
    await close_redis()
    logger.info("All connections closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Integrador - Buen Sabor API",
        description="Restaurant management system API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register routers
    application.include_router(health.router, prefix=f"{settings.API_PREFIX}/health")

    return application


app = create_app()
