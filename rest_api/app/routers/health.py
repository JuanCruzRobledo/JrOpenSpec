"""Health check endpoints for liveness and readiness probes."""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from shared.infrastructure.db import async_session_factory
from shared.infrastructure.redis import get_redis
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/live")
async def liveness() -> dict:
    """Liveness probe — returns alive if the process is running."""
    return {"status": "alive"}


@router.get("/ready")
async def readiness() -> JSONResponse:
    """Readiness probe — checks PostgreSQL and Redis connectivity."""
    checks: dict[str, str] = {}

    # Check PostgreSQL
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        logger.exception("PostgreSQL readiness check failed")
        checks["postgres"] = "error"

    # Check Redis
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        logger.exception("Redis readiness check failed")
        checks["redis"] = "error"

    all_healthy = all(v == "ok" for v in checks.values())
    status_code = 200 if all_healthy else 503
    status = "ready" if all_healthy else "not_ready"

    return JSONResponse(
        status_code=status_code,
        content={"status": status, "checks": checks},
    )
