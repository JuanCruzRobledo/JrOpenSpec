"""Health check endpoints — liveness and readiness probes.

Registration (Agent 1 adds this to main.py):
    from rest_api.app.routers.health import router as health_router
    app.include_router(health_router, prefix="/api/health")
"""

import logging

from fastapi import APIRouter, Response
from sqlalchemy import text

from shared.infrastructure.db import async_session_factory
from shared.infrastructure.redis import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/live")
async def liveness() -> dict:
    """Liveness probe — confirms the process is running. No external calls."""
    return {"status": "alive"}


@router.get("/ready")
async def readiness(response: Response) -> dict:
    """Readiness probe — checks PostgreSQL and Redis connectivity."""
    checks: dict[str, str] = {}

    # Check PostgreSQL
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        logger.exception("Readiness check: PostgreSQL is unreachable")
        checks["postgres"] = "error"

    # Check Redis
    try:
        redis = await get_redis()
        pong = await redis.ping()
        if pong:
            checks["redis"] = "ok"
        else:
            checks["redis"] = "error"
        await redis.aclose()
    except Exception:
        logger.exception("Readiness check: Redis is unreachable")
        checks["redis"] = "error"

    # Determine overall status
    all_ok = all(v == "ok" for v in checks.values())
    status = "ready" if all_ok else "not_ready"

    if not all_ok:
        response.status_code = 503

    return {"status": status, "checks": checks}
