"""HMAC-SHA256 table token generation and validation.

Implements REQ-TABLE-01:
- Tokens contain branch_id, table_id, session_id, timestamp
- Signed with HMAC-SHA256 using TABLE_TOKEN_SECRET
- Format: base64url(json(payload)) + "." + base64url(hmac_signature)
- Default lifetime: 3 hours
"""

import base64
import hashlib
import hmac
import json
import logging
import time

logger = logging.getLogger(__name__)

# Default token lifetime: 3 hours
DEFAULT_TTL_SECONDS = 3 * 60 * 60


def _b64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Base64url decode with padding restoration."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(payload_b64: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature of the payload."""
    sig = hmac.new(
        secret.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(sig)


def generate_table_token(
    secret: str,
    branch_id: int,
    table_id: int,
    session_id: int,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> str:
    """Generate an HMAC-SHA256 signed table token.

    Args:
        secret: TABLE_TOKEN_SECRET from environment.
        branch_id: The branch this table belongs to.
        table_id: The table ID.
        session_id: The active table session ID.
        ttl: Token lifetime in seconds (default: 3 hours).

    Returns:
        Token string in format: base64url(payload).base64url(signature)
    """
    payload = {
        "branch_id": branch_id,
        "table_id": table_id,
        "session_id": session_id,
        "exp": int(time.time()) + ttl,
        "iat": int(time.time()),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)
    signature = _sign(payload_b64, secret)
    return f"{payload_b64}.{signature}"


def verify_table_token(secret: str, token: str) -> dict:
    """Verify and decode an HMAC-SHA256 table token.

    Args:
        secret: TABLE_TOKEN_SECRET from environment.
        token: The token string to verify.

    Returns:
        Decoded payload dict with branch_id, table_id, session_id, exp, iat.

    Raises:
        ValueError: If the token is malformed, signature is invalid, or expired.
    """
    parts = token.split(".")
    if len(parts) != 2:
        raise ValueError("Malformed table token: expected 2 parts")

    payload_b64, signature = parts

    # Verify signature
    expected_sig = _sign(payload_b64, secret)
    if not hmac.compare_digest(signature, expected_sig):
        raise ValueError("Invalid table token signature")

    # Decode payload
    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes)
    except (json.JSONDecodeError, Exception) as exc:
        raise ValueError("Malformed table token payload") from exc

    # Check expiration
    if payload.get("exp", 0) < time.time():
        raise ValueError("Table token has expired")

    return payload
