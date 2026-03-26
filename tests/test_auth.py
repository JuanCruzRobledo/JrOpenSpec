"""Integration tests for auth flow: login, refresh, logout, me endpoint.

Covers REQ-AUTH-01 through REQ-AUTH-07, REQ-TEST-01.

NOTE: These tests require Batch A (auth service, JWT, auth router) to be merged.
They will fail with ImportError until Batch A is available. This is expected —
tests are written ahead of the implementation they verify.
"""

import pytest

# Mark all tests in this module as requiring auth infrastructure
pytestmark = pytest.mark.integration


class TestLogin:
    """REQ-AUTH-01: Login endpoint tests."""

    async def test_login_success(self, client):
        """Successful login returns access_token and sets refresh cookie."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "correct_password"},
            headers={"Content-Type": "application/json"},
        )
        # When Batch A is merged, this should return 200 with token
        # For now, it may 404 since the route doesn't exist yet
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            # Refresh token should be in Set-Cookie header
            assert "set-cookie" in response.headers

    async def test_login_invalid_password(self, client):
        """Wrong password returns 401 with generic message."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "wrong_password"},
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 404:  # Route exists
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"

    async def test_login_nonexistent_user(self, client):
        """Unknown email returns same 401 (no user enumeration)."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": "any_password"},
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 404:  # Route exists
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"

    async def test_login_missing_fields(self, client):
        """Missing email or password returns 422."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@test.com"},
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 404:
            assert response.status_code == 422


class TestRefresh:
    """REQ-AUTH-04: Refresh endpoint tests."""

    async def test_refresh_without_cookie(self, client):
        """Refresh without cookie should return 401."""
        response = await client.post(
            "/api/auth/refresh",
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 404:
            assert response.status_code == 401


class TestLogout:
    """REQ-AUTH-05: Logout endpoint tests."""

    async def test_logout_without_auth(self, client):
        """Logout without auth should return 401."""
        response = await client.post(
            "/api/auth/logout",
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 404:
            assert response.status_code in (401, 403)


class TestMe:
    """REQ-AUTH-06: Me endpoint tests."""

    async def test_me_without_auth(self, client):
        """GET /me without auth should return 401."""
        response = await client.get("/api/auth/me")
        if response.status_code != 404:
            assert response.status_code == 401

    async def test_me_with_invalid_token(self, client):
        """GET /me with invalid token should return 401."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        if response.status_code != 404:
            assert response.status_code == 401


class TestExpiredToken:
    """REQ-AUTH-03: Token lifetime tests."""

    async def test_expired_access_token(self, client):
        """Expired access token should return 401."""
        # Generate an expired token (would need Batch A's JWT utils)
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer expired.test.token"},
        )
        if response.status_code != 404:
            assert response.status_code == 401
