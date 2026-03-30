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
from shared.exceptions import AppError, NotFoundError
from shared.infrastructure.db import safe_commit
from shared.models.core.refresh_token import RefreshToken
from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
from shared.security.blacklist import add_to_blacklist
from shared.security.brute_force import (
    check_login_protection,
    record_failed_attempt,
    reset_login_protection,
)
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

    def __init__(
        self,
        message: str = "Too many login attempts",
        *,
        retry_after: int | None = None,
        code: str = "login_rate_limited",
    ):
        super().__init__(message=message)
        self.retry_after = retry_after
        self.code = code


def _hash_token(token: str) -> str:
    """Create a SHA-256 hash of a token for storage (not the JWT secret)."""
    return hashlib.sha256(token.encode()).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _maybe_blacklist_access_token(
    redis_client: aioredis.Redis,
    access_token: str | None,
    expected_user_id: int | None = None,
) -> None:
    """Best-effort blacklist of the current access token during refresh/logout."""
    if not access_token:
        return

    try:
        payload = decode_token(access_token)
    except JWTError:
        logger.info("Skipping access-token blacklist because token decode failed")
        return

    if payload.get("type") == "refresh":
        logger.info("Skipping access-token blacklist because token type is refresh")
        return

    jti = payload.get("jti")
    subject = payload.get("sub")
    exp = int(payload.get("exp", 0))

    if not jti or not subject:
        return

    if expected_user_id is not None and int(subject) != expected_user_id:
        logger.warning(
            "Skipping access-token blacklist because subject mismatch: expected=%s actual=%s",
            expected_user_id,
            subject,
        )
        return

    now = int(_utcnow().timestamp())
    remaining_ttl = max(exp - now, 1)
    await add_to_blacklist(redis_client, jti, remaining_ttl)


async def _revoke_token_family(db: AsyncSession, family_id: str) -> None:
    """Revoke every active refresh token in a family."""
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=_utcnow())
    )


async def _load_active_user_with_roles(
    db: AsyncSession, user_id: int
) -> tuple[User, list[int], list[str]]:
    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    user_result = await db.execute(stmt)
    user = user_result.scalar_one_or_none()
    if user is None:
        raise AuthenticationError("User not found")

    roles_stmt = select(UserBranchRole).where(
        UserBranchRole.user_id == user.id,
        UserBranchRole.is_active.is_(True),
    )
    roles_result = await db.execute(roles_stmt)
    branch_roles = roles_result.scalars().all()
    branch_ids = list({br.branch_id for br in branch_roles})
    roles = list({br.role for br in branch_roles})
    return user, branch_ids, roles


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

    async def login(self, email: str, password: str, ip_address: str = "unknown") -> tuple[str, str]:
        """Authenticate user and issue tokens.

        Returns:
            Tuple of (access_token, refresh_token).

        Raises:
            RateLimitError: If brute-force threshold exceeded.
            AuthenticationError: If credentials are invalid.
        """
        login_state = await check_login_protection(self.redis, email, ip_address)
        if login_state.blocked:
            raise RateLimitError(retry_after=login_state.retry_after)

        # Load user
        user_data = await _load_user_with_roles(self.db, email)
        if user_data is None:
            failed_state = await record_failed_attempt(self.redis, email, ip_address)
            if failed_state.blocked:
                raise RateLimitError(retry_after=failed_state.retry_after)
            raise AuthenticationError()

        user, branch_ids, roles = user_data

        # Verify password (async — runs in executor)
        if not await verify_password(password, user.hashed_password):
            failed_state = await record_failed_attempt(self.redis, email, ip_address)
            if failed_state.blocked:
                raise RateLimitError(retry_after=failed_state.retry_after)
            raise AuthenticationError()

        await reset_login_protection(self.redis, email, ip_address)

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
            expires_at=_utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        )
        self.db.add(db_refresh)
        user.last_login_at = _utcnow()
        await safe_commit(self.db)

        logger.info("User %s logged in successfully", user.id)
        return access_token, refresh_token

    async def refresh(
        self,
        refresh_token_str: str,
        current_access_token: str | None = None,
    ) -> tuple[str, str]:
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
        ).with_for_update()
        result = await self.db.execute(stmt)
        db_token = result.scalar_one_or_none()

        # REUSE DETECTION: token not found, replaced, revoked, or hash mismatch
        if db_token is None:
            logger.warning(
                "Refresh token reuse detected for family=%s user=%s — revoking entire family",
                family_id,
                user_id,
            )
            await _revoke_token_family(self.db, family_id)
            await safe_commit(self.db)
            raise AuthenticationError("Refresh token reuse detected")

        incoming_hash = _hash_token(refresh_token_str)
        if db_token.token_hash != incoming_hash or db_token.revoked_at is not None or db_token.replaced_by_id is not None:
            logger.warning(
                "Refresh token reuse detected for family=%s user=%s token_id=%s",
                family_id,
                user_id,
                db_token.id,
            )
            await _revoke_token_family(self.db, family_id)
            await safe_commit(self.db)
            raise AuthenticationError("Refresh token reuse detected")

        # Check expiry
        if db_token.expires_at < _utcnow():
            db_token.revoked_at = _utcnow()
            await safe_commit(self.db)
            raise AuthenticationError("Refresh token expired")

        user, branch_ids, roles = await _load_active_user_with_roles(self.db, user_id)

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
            expires_at=_utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        )
        self.db.add(new_db_refresh)
        await self.db.flush()

        db_token.revoked_at = _utcnow()
        db_token.replaced_by_id = new_db_refresh.id
        await safe_commit(self.db)

        await _maybe_blacklist_access_token(
            self.redis,
            current_access_token,
            expected_user_id=user.id,
        )

        logger.info("Refreshed tokens for user %s (family=%s)", user.id, family_id)
        return new_access_token, new_refresh_token

    async def logout(self, access_token: str, refresh_token_str: str | None = None) -> None:
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
        now = int(_utcnow().timestamp())
        remaining_ttl = max(exp - now, 1)
        await add_to_blacklist(self.redis, jti, remaining_ttl)

        if refresh_token_str:
            try:
                refresh_payload = decode_token(refresh_token_str)
            except JWTError:
                refresh_payload = None

            if refresh_payload and refresh_payload.get("family_id"):
                await _revoke_token_family(self.db, refresh_payload["family_id"])
            else:
                await self.db.execute(
                    update(RefreshToken)
                    .where(
                        RefreshToken.user_id == user_id,
                        RefreshToken.revoked_at.is_(None),
                    )
                    .values(revoked_at=_utcnow())
                )
        else:
            await self.db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=_utcnow())
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
