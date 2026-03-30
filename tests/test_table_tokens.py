"""Tests for HMAC table token generation and validation.

Covers REQ-TABLE-01.
"""

import time

import pytest

from shared.security.table_tokens import (
    DEFAULT_TTL_SECONDS,
    generate_table_token,
    verify_table_token,
)

TEST_SECRET = "test-secret-key-for-table-tokens-minimum-32-chars"


class TestTableTokenGeneration:
    """Test token generation produces valid, verifiable tokens."""

    def test_generate_returns_two_part_token(self):
        """Generated token should have format: payload.signature."""
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=1,
            table_id=5,
            session_id=100,
        )
        parts = token.split(".")
        assert len(parts) == 2
        assert len(parts[0]) > 0
        assert len(parts[1]) > 0

    def test_generate_with_custom_ttl(self):
        """Token with custom TTL should have correct expiration."""
        custom_ttl = 1800  # 30 minutes
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=1,
            table_id=5,
            session_id=100,
            ttl=custom_ttl,
        )
        payload = verify_table_token(TEST_SECRET, token)
        # exp should be approximately now + custom_ttl
        assert abs(payload["exp"] - (int(time.time()) + custom_ttl)) <= 2

    def test_default_ttl_is_3_hours(self):
        """Default TTL should be 3 hours (10800 seconds)."""
        assert DEFAULT_TTL_SECONDS == 3 * 60 * 60


class TestTableTokenVerification:
    """Test token verification: valid, expired, tampered."""

    def test_verify_valid_token(self):
        """Valid token should decode successfully."""
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=1,
            table_id=5,
            session_id=100,
        )
        payload = verify_table_token(TEST_SECRET, token)
        assert payload["branch_id"] == 1
        assert payload["table_id"] == 5
        assert payload["session_id"] == 100
        assert "exp" in payload
        assert "iat" in payload

    def test_verify_expired_token(self):
        """Expired token should raise ValueError."""
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=1,
            table_id=5,
            session_id=100,
            ttl=-10,  # Already expired
        )
        with pytest.raises(ValueError, match="expired"):
            verify_table_token(TEST_SECRET, token)

    def test_verify_wrong_secret(self):
        """Token verified with wrong secret should raise ValueError."""
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=1,
            table_id=5,
            session_id=100,
        )
        with pytest.raises(ValueError, match="signature"):
            verify_table_token("wrong-secret-key-that-is-also-32-chars", token)

    def test_verify_tampered_payload(self):
        """Token with tampered payload should fail signature check."""
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=1,
            table_id=5,
            session_id=100,
        )
        parts = token.split(".")
        # Tamper with the payload (flip a character)
        tampered_payload = parts[0][:-1] + ("A" if parts[0][-1] != "A" else "B")
        tampered_token = f"{tampered_payload}.{parts[1]}"
        with pytest.raises(ValueError):
            verify_table_token(TEST_SECRET, tampered_token)

    def test_verify_malformed_token_no_dot(self):
        """Token without dot separator should raise ValueError."""
        with pytest.raises(ValueError, match="Malformed"):
            verify_table_token(TEST_SECRET, "nodottoken")

    def test_verify_malformed_token_empty(self):
        """Empty token should raise ValueError."""
        with pytest.raises(ValueError, match="Malformed"):
            verify_table_token(TEST_SECRET, "")

    def test_verify_malformed_token_too_many_parts(self):
        """Token with 3 parts should raise ValueError."""
        with pytest.raises(ValueError, match="Malformed"):
            verify_table_token(TEST_SECRET, "a.b.c")


class TestTableTokenPayloadContent:
    """Verify the payload structure matches the design spec."""

    def test_payload_contains_required_fields(self):
        """Payload must contain branch_id, table_id, session_id, exp, iat."""
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=42,
            table_id=7,
            session_id=999,
        )
        payload = verify_table_token(TEST_SECRET, token)
        assert set(payload.keys()) == {"branch_id", "table_id", "session_id", "exp", "iat"}

    def test_payload_does_not_include_staff_jwt_claims(self):
        """Table tokens stay table-scoped and never impersonate staff JWTs."""
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=42,
            table_id=7,
            session_id=999,
        )

        payload = verify_table_token(TEST_SECRET, token)

        assert "sub" not in payload
        assert "tenant_id" not in payload
        assert "branch_ids" not in payload
        assert "roles" not in payload

    def test_iat_is_current_timestamp(self):
        """iat should be approximately the current Unix timestamp."""
        before = int(time.time())
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=1,
            table_id=1,
            session_id=1,
        )
        after = int(time.time())
        payload = verify_table_token(TEST_SECRET, token)
        assert before <= payload["iat"] <= after

    def test_exp_is_iat_plus_ttl(self):
        """exp should equal iat + ttl."""
        token = generate_table_token(
            secret=TEST_SECRET,
            branch_id=1,
            table_id=1,
            session_id=1,
            ttl=600,
        )
        payload = verify_table_token(TEST_SECRET, token)
        assert payload["exp"] - payload["iat"] == 600
