"""Public session router — no auth required.

POST /api/sessions/join — customer QR entry flow
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.middleware.rate_limit import limiter
from rest_api.app.schemas.session import SessionJoinRequest, SessionJoinResponse
from rest_api.app.services.domain.session_service import SessionService
from shared.config import settings
from shared.infrastructure.db import get_db
from starlette.requests import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Thin dependency — constructs SessionService with injected DB and secret."""
    return SessionService(db=db, secret=settings.TABLE_TOKEN_SECRET)


@router.post("/join", response_model=SessionJoinResponse)
@limiter.limit("60/minute")
async def join_session(
    request: Request,
    body: SessionJoinRequest,
    service: SessionService = Depends(_get_service),
) -> SessionJoinResponse:
    """POST /api/sessions/join — validates table and issues an HMAC session token.

    Returns:
        200 with token and session info on success.
        404 if branch or table not found.
        409 if table is inactive.
        429 if rate limit exceeded (60/min per IP via slowapi).
    """
    result = await service.join_session(
        branch_slug=body.branchSlug,
        table_identifier=body.tableIdentifier,
        display_name=body.displayName,
        avatar_color=body.avatarColor,
        locale=body.locale,
    )
    return SessionJoinResponse(**result)
