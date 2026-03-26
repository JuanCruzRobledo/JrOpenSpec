"""HMAC-SHA256 table tokens for diner session authentication.

Table tokens are lightweight, non-JWT tokens used to authenticate
QR-scanned diner sessions.  Format: base64url(json_payload).base64url(hmac_sig)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from shared.exceptions import AuthenticationError


def _b64url_encode(data: bytes) -> str:
    """URL-safe base64 encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """URL-safe base64 decode, re-adding stripped padding."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(secret: str, payload_b64: str) -> str:
    """Compute HMAC-SHA256 signature over the encoded payload."""
    sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(sig)


def generate_table_token(
    secret: str,
    branch_id: int,
    table_id: int,
    session_id: int,
    ttl: int = 10800,  # 3 hours in seconds
) -> str:
    """Generate an HMAC-SHA256 table token.

    Args:
        secret: TABLE_TOKEN_SECRET from env.
        branch_id: Branch this table belongs to.
        table_id: The physical table identifier.
        session_id: Active diner session id.
        ttl: Lifetime in seconds (default 3h).

    Returns:
        Token string in format ``base64url(payload).base64url(signature)``.
    """
    payload = {
        "branch_id": branch_id,
        "table_id": table_id,
        "session_id": session_id,
        "exp": int(time.time()) + ttl,
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(secret, payload_b64)
    return f"{payload_b64}.{signature}"


def verify_table_token(secret: str, token: str) -> dict:
    """Verify an HMAC-SHA256 table token and return its payload.

    Args:
        secret: TABLE_TOKEN_SECRET from env.
        token: The token string to verify.

    Returns:
        Dict with keys: branch_id, table_id, session_id, exp.

    Raises:
        AuthenticationError: If the token is malformed, tampered, or expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise AuthenticationError(message="Invalid table token format")

        payload_b64, provided_sig = parts

        # Verify signature
        expected_sig = _sign(secret, payload_b64)
        if not hmac.compare_digest(provided_sig, expected_sig):
            raise AuthenticationError(message="Invalid table token signature")

        # Decode payload
        payload = json.loads(_b64url_decode(payload_b64))

        # Check expiration
        if payload.get("exp", 0) < time.time():
            raise AuthenticationError(message="Table token expired")

        return payload

    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError(message="Invalid table token") from exc
