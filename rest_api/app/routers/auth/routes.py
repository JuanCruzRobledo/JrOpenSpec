"""Auth router — thin handlers delegating to AuthService.

POST /login  — authenticate and issue tokens
POST /refresh — rotate refresh token
POST /logout — blacklist access + revoke refresh
GET /me      — return current user profile
"""

import logging

from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.routers.auth.schemas import (
    ErrorResponse,
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
)
from rest_api.app.services.auth_service import AuthenticationError, AuthService, RateLimitError
from shared.config import settings
from shared.infrastructure.db import get_db
from shared.infrastructure.redis import get_redis
from shared.security.blacklist import is_blacklisted
from shared.security.jwt import decode_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> AuthService:
    """Build AuthService with injected dependencies."""
    return AuthService(db=db, redis_client=redis)


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an HttpOnly cookie."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        domain=settings.COOKIE_DOMAIN,
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 86400,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh token cookie."""
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        domain=settings.COOKIE_DOMAIN,
        path="/api/auth",
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def login(
    body: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(_get_auth_service),
):
    """Authenticate user with email + password, return access token + refresh cookie."""
    try:
        access_token, refresh_token = await auth_service.login(
            email=body.email, password=body.password
        )
    except RateLimitError as exc:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=429, content={"detail": exc.message})
    except AuthenticationError as exc:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": exc.message})

    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(_get_auth_service),
):
    """Rotate refresh token and issue new access token."""
    if not refresh_token:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": "Missing refresh token"})

    try:
        new_access_token, new_refresh_token = await auth_service.refresh(refresh_token)
    except AuthenticationError as exc:
        from fastapi.responses import JSONResponse

        _clear_refresh_cookie(response)
        return JSONResponse(status_code=401, content={"detail": exc.message})

    _set_refresh_cookie(response, new_refresh_token)
    return TokenResponse(access_token=new_access_token)


@router.post(
    "/logout",
    responses={401: {"model": ErrorResponse}},
)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(_get_auth_service),
    redis=Depends(get_redis),
):
    """Blacklist access token and revoke refresh tokens."""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": "Missing token"})

    token = auth_header[7:]  # Strip "Bearer "

    # Validate the token is not already blacklisted
    try:
        payload = decode_token(token)
        jti = payload.get("jti", "")
        if await is_blacklisted(redis, jti):
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=401, content={"detail": "Token already invalidated"})
    except Exception:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    try:
        await auth_service.logout(token)
    except AuthenticationError as exc:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": exc.message})

    _clear_refresh_cookie(response)
    return {"detail": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserProfileResponse,
    responses={401: {"model": ErrorResponse}},
)
async def me(
    request: Request,
    auth_service: AuthService = Depends(_get_auth_service),
    redis=Depends(get_redis),
):
    """Return the current user's profile."""
    # Extract and validate token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": "Missing token"})

    token = auth_header[7:]

    try:
        payload = decode_token(token)
        jti = payload.get("jti", "")
        if await is_blacklisted(redis, jti):
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=401, content={"detail": "Token has been revoked"})
    except Exception:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    user_id = int(payload["sub"])
    profile = await auth_service.get_me(user_id)
    return UserProfileResponse(**profile)
