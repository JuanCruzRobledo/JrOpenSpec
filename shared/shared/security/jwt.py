"""JWT token creation and validation using python-jose."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from shared.config import settings

logger = logging.getLogger(__name__)


def _generate_jti() -> str:
    """Generate a unique JWT ID for blacklist tracking."""
    return str(uuid.uuid4())


def create_access_token(
    user_id: int,
    tenant_id: int,
    branch_ids: list[int],
    roles: list[str],
) -> tuple[str, str]:
    """Create an access token with user claims.

    Returns:
        Tuple of (encoded_token, jti) so the caller can track the JTI.
    """
    jti = _generate_jti()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tenant_id": tenant_id,
        "branch_ids": branch_ids,
        "roles": roles,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)).timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_refresh_token(
    user_id: int,
    family_id: str,
) -> tuple[str, str]:
    """Create a refresh token with family tracking.

    Args:
        user_id: The user this token belongs to.
        family_id: Token family ID for reuse detection.

    Returns:
        Tuple of (encoded_token, jti).
    """
    jti = _generate_jti()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "family_id": family_id,
        "jti": jti,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)).timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Returns:
        The decoded payload dict.

    Raises:
        JWTError: If the token is invalid, expired, or tampered with.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        logger.debug("JWT decode failed for token")
        raise
