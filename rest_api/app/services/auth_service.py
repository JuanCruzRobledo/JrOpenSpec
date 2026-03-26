"""Auth domain service — login, refresh, logout, me.

Implements REQ-AUTH-01 through REQ-AUTH-07 and REQ-RATE-02.
"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import settings
from shared.config.constants import (
    LOGIN_LOCKOUT_SECONDS,
    LOGIN_MAX_ATTEMPTS,
    REDIS_LOGIN_ATTEMPTS_PREFIX,
)
from shared.exceptions import AppError, NotFoundError
from shared.infrastructure.db import safe_commit
from shared.models.core.refresh_token import RefreshToken
from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
from shared.security.blacklist import add_to_blacklist, is_blacklisted
from shared.security.jwt import create_access_token, create_refresh_token, decode_token
from shared.security.passwords import verify_password

logger = logging.getLogger(__name__)


class AuthenticationError(AppError):
    """Raised on invalid credentials or token validation failure."""

    status_code = 401

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message)


class RateLimitError(AppError):
    """Raised when brute-force threshold is exceeded."""

    status_code = 429

    def __init__(self, message: str = "Too many requests"):
        super().__init__(message=message)


def _hash_token(token: str) -> str:
    """Create a SHA-256 hash of a token for storage (not the JWT secret)."""
    return hashlib.sha256(token.encode()).hexdigest()


async def _check_brute_force(redis_client: aioredis.Redis, email: str) -> None:
    """Check and enforce brute-force protection via Redis counter.

    Raises RateLimitError if threshold exceeded.
    """
    key = f"{REDIS_LOGIN_ATTEMPTS_PREFIX}{email}"
    try:
        attempts = await redis_client.get(key)
        if attempts is not None and int(attempts) >= LOGIN_MAX_ATTEMPTS:
            raise RateLimitError("Too many requests")
    except RateLimitError:
        raise
    except Exception:
        # Redis error during check — log but allow (rate limit is secondary to auth)
        logger.warning("Redis error during brute-force check for %s", email)


async def _increment_login_attempts(redis_client: aioredis.Redis, email: str) -> None:
    """Increment the failed login counter for an email."""
    key = f"{REDIS_LOGIN_ATTEMPTS_PREFIX}{email}"
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, LOGIN_LOCKOUT_SECONDS)
        await pipe.execute()
    except Exception:
        logger.warning("Redis error incrementing login attempts for %s", email)


async def _clear_login_attempts(redis_client: aioredis.Redis, email: str) -> None:
    """Clear the failed login counter on successful login."""
    key = f"{REDIS_LOGIN_ATTEMPTS_PREFIX}{email}"
    try:
        await redis_client.delete(key)
    except Exception:
        logger.warning("Redis error clearing login attempts for %s", email)


async def _load_user_with_roles(
    db: AsyncSession, email: str
) -> tuple[User, list[int], list[str]] | None:
    """Load a user by email with their branch_ids and roles.

    Returns None if user not found or inactive.
    """
    stmt = select(User).where(User.email == email, User.is_active.is_(True))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        return None

    # Load branch roles
    roles_stmt = select(UserBranchRole).where(
        UserBranchRole.user_id == user.id,
        UserBranchRole.is_active.is_(True),
    )
    roles_result = await db.execute(roles_stmt)
    branch_roles = roles_result.scalars().all()

    branch_ids = list({br.branch_id for br in branch_roles})
    roles = list({br.role for br in branch_roles})

    return user, branch_ids, roles


async def _build_user_profile(
    db: AsyncSession, user_id: int
) -> dict:
    """Build user profile dict from database."""
    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    roles_stmt = select(UserBranchRole).where(
        UserBranchRole.user_id == user.id,
        UserBranchRole.is_active.is_(True),
    )
    roles_result = await db.execute(roles_stmt)
    branch_roles = roles_result.scalars().all()

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "tenant_id": user.tenant_id,
        "branch_ids": list({br.branch_id for br in branch_roles}),
        "roles": list({br.role for br in branch_roles}),
        "is_superadmin": user.is_superadmin,
    }


class AuthService:
    """Authentication domain service."""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def login(self, email: str, password: str) -> tuple[str, str]:
        """Authenticate user and issue tokens.

        Returns:
            Tuple of (access_token, refresh_token).

        Raises:
            RateLimitError: If brute-force threshold exceeded.
            AuthenticationError: If credentials are invalid.
        """
        # Check brute-force protection
        await _check_brute_force(self.redis, email)

        # Load user
        user_data = await _load_user_with_roles(self.db, email)
        if user_data is None:
            await _increment_login_attempts(self.redis, email)
            raise AuthenticationError()

        user, branch_ids, roles = user_data

        # Verify password (async — runs in executor)
        if not await verify_password(password, user.hashed_password):
            await _increment_login_attempts(self.redis, email)
            raise AuthenticationError()

        # Clear brute-force counter on success
        await _clear_login_attempts(self.redis, email)

        # Create tokens
        access_token, _access_jti = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            branch_ids=branch_ids,
            roles=roles,
        )

        family_id = str(uuid.uuid4())
        refresh_token, refresh_jti = create_refresh_token(
            user_id=user.id,
            family_id=family_id,
        )

        # Store refresh token in DB
        db_refresh = RefreshToken(
            jti=refresh_jti,
            user_id=user.id,
            family_id=family_id,
            token_hash=_hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        )
        self.db.add(db_refresh)
        await safe_commit(self.db)

        # Update last_login_at
        user.last_login_at = datetime.now(timezone.utc)
        await safe_commit(self.db)

        logger.info("User %s logged in successfully", user.id)
        return access_token, refresh_token

    async def refresh(self, refresh_token_str: str) -> tuple[str, str]:
        """Rotate refresh token and issue new access token.

        Implements reuse detection: if the incoming refresh token is already
        revoked, ALL tokens in that family are invalidated.

        Returns:
            Tuple of (new_access_token, new_refresh_token).

        Raises:
            AuthenticationError: If token is invalid, expired, or reuse detected.
        """
        # Decode the refresh token
        try:
            payload = decode_token(refresh_token_str)
        except JWTError:
            raise AuthenticationError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        jti = payload.get("jti")
        family_id = payload.get("family_id")
        user_id = int(payload["sub"])

        if not jti or not family_id:
            raise AuthenticationError("Invalid refresh token")

        # Look up the token in DB
        stmt = select(RefreshToken).where(
            RefreshToken.jti == jti,
            RefreshToken.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        db_token = result.scalar_one_or_none()

        # REUSE DETECTION: token not found or already revoked
        if db_token is None or db_token.revoked_at is not None:
            logger.warning(
                "Refresh token reuse detected for family=%s user=%s — revoking entire family",
                family_id,
                user_id,
            )
            # Revoke ALL tokens in this family
            await self.db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.family_id == family_id,
                    RefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=datetime.now(timezone.utc))
            )
            await safe_commit(self.db)
            raise AuthenticationError("Token reuse detected")

        # Check expiry
        if db_token.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token expired")

        # Revoke current token
        db_token.revoked_at = datetime.now(timezone.utc)

        # Load user data for new access token
        stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
        user_result = await self.db.execute(stmt)
        user = user_result.scalar_one_or_none()
        if user is None:
            raise AuthenticationError("User not found")

        roles_stmt = select(UserBranchRole).where(
            UserBranchRole.user_id == user.id,
            UserBranchRole.is_active.is_(True),
        )
        roles_result = await self.db.execute(roles_stmt)
        branch_roles = roles_result.scalars().all()
        branch_ids = list({br.branch_id for br in branch_roles})
        roles = list({br.role for br in branch_roles})

        # Issue new tokens (same family)
        new_access_token, _access_jti = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            branch_ids=branch_ids,
            roles=roles,
        )

        new_refresh_token, new_refresh_jti = create_refresh_token(
            user_id=user.id,
            family_id=family_id,
        )

        # Store new refresh token
        new_db_refresh = RefreshToken(
            jti=new_refresh_jti,
            user_id=user.id,
            family_id=family_id,
            token_hash=_hash_token(new_refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        )
        self.db.add(new_db_refresh)
        await safe_commit(self.db)

        logger.info("Refreshed tokens for user %s (family=%s)", user.id, family_id)
        return new_access_token, new_refresh_token

    async def logout(self, access_token: str) -> None:
        """Blacklist the access token and revoke the associated refresh token.

        Args:
            access_token: The current access token to blacklist.

        Raises:
            AuthenticationError: If the token is invalid.
        """
        try:
            payload = decode_token(access_token)
        except JWTError:
            raise AuthenticationError("Invalid token")

        jti = payload.get("jti")
        user_id = int(payload["sub"])
        exp = payload.get("exp", 0)

        # Blacklist access token in Redis (TTL = remaining lifetime)
        now = int(datetime.now(timezone.utc).timestamp())
        remaining_ttl = max(exp - now, 1)
        await add_to_blacklist(self.redis, jti, remaining_ttl)

        # Revoke all active refresh tokens for this user
        # (conservative approach — user must re-login)
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await safe_commit(self.db)

        logger.info("User %s logged out, access token blacklisted", user_id)

    async def get_me(self, user_id: int) -> dict:
        """Return the current user's profile.

        Args:
            user_id: The authenticated user's ID (from JWT).

        Returns:
            User profile dict matching UserProfileResponse schema.

        Raises:
            NotFoundError: If user not found or inactive.
        """
        return await _build_user_profile(self.db, user_id)
