"""Tests for security middlewares: headers, content-type, CORS, correlation ID.

Covers REQ-SEC-01, REQ-SEC-02, REQ-SEC-03, REQ-SEC-04.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from rest_api.app.main import create_app


@pytest.fixture
def test_app():
    """Create a fresh test app for middleware tests."""
    return create_app()


@pytest.fixture
async def middleware_client(test_app):
    """Client that hits the real middleware stack (no dependency overrides)."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# REQ-SEC-01: Security Headers
# ---------------------------------------------------------------------------


class TestSecurityHeaders:
    """Verify security headers are present on all responses."""

    async def test_x_content_type_options(self, middleware_client):
        response = await middleware_client.get("/api/health/live")
        assert response.headers.get("x-content-type-options") == "nosniff"

    async def test_x_frame_options(self, middleware_client):
        response = await middleware_client.get("/api/health/live")
        assert response.headers.get("x-frame-options") == "DENY"

    async def test_x_xss_protection(self, middleware_client):
        response = await middleware_client.get("/api/health/live")
        assert response.headers.get("x-xss-protection") == "1; mode=block"

    async def test_referrer_policy(self, middleware_client):
        response = await middleware_client.get("/api/health/live")
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    async def test_permissions_policy(self, middleware_client):
        response = await middleware_client.get("/api/health/live")
        assert "camera=()" in response.headers.get("permissions-policy", "")

    async def test_content_security_policy(self, middleware_client):
        response = await middleware_client.get("/api/health/live")
        assert "default-src 'self'" in response.headers.get("content-security-policy", "")

    async def test_no_hsts_in_development(self, middleware_client):
        """HSTS should NOT be present in non-production environments."""
        response = await middleware_client.get("/api/health/live")
        assert "strict-transport-security" not in response.headers

    async def test_server_header_removed(self, middleware_client):
        """Server header should be removed to prevent fingerprinting."""
        response = await middleware_client.get("/api/health/live")
        assert "server" not in response.headers


# ---------------------------------------------------------------------------
# REQ-SEC-02: Content-Type Validation
# ---------------------------------------------------------------------------


class TestContentTypeValidation:
    """Verify content-type validation on mutating requests."""

    async def test_post_with_json_allowed(self, middleware_client):
        """POST with application/json should pass through."""
        response = await middleware_client.post(
            "/api/health/live",
            headers={"Content-Type": "application/json"},
            content="{}",
        )
        # Should not be 415 — may be 404/405 depending on route, but not 415
        assert response.status_code != 415

    async def test_post_with_form_urlencoded_allowed(self, middleware_client):
        """POST with form-urlencoded should pass through."""
        response = await middleware_client.post(
            "/api/health/live",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            content="key=value",
        )
        assert response.status_code != 415

    async def test_post_with_text_plain_rejected(self, middleware_client):
        """POST with text/plain should return 415."""
        response = await middleware_client.post(
            "/api/admin/categories",
            headers={"Content-Type": "text/plain"},
            content="hello",
        )
        assert response.status_code == 415
        assert response.json()["detail"] == "Unsupported Media Type"

    async def test_post_with_no_content_type_rejected(self, middleware_client):
        """POST without Content-Type should return 415."""
        response = await middleware_client.post(
            "/api/admin/categories",
            content=b"data",
        )
        assert response.status_code == 415

    async def test_get_with_any_content_type_allowed(self, middleware_client):
        """GET requests should not be subject to content-type validation."""
        response = await middleware_client.get(
            "/api/health/live",
            headers={"Content-Type": "text/plain"},
        )
        assert response.status_code != 415

    async def test_exempt_path_billing_webhook(self, middleware_client):
        """Billing webhook path should be exempt from content-type validation."""
        response = await middleware_client.post(
            "/api/billing/webhook",
            headers={"Content-Type": "text/plain"},
            content="webhook_data",
        )
        # Should not be 415 — may be 404, but the middleware should let it through
        assert response.status_code != 415

    async def test_exempt_path_health(self, middleware_client):
        """Health endpoint should be exempt from content-type validation."""
        response = await middleware_client.post(
            "/api/health/live",
            headers={"Content-Type": "application/json"},
            content="{}",
        )
        assert response.status_code != 415

    async def test_put_with_xml_rejected(self, middleware_client):
        """PUT with application/xml should return 415."""
        response = await middleware_client.put(
            "/api/admin/categories/1",
            headers={"Content-Type": "application/xml"},
            content="<root/>",
        )
        assert response.status_code == 415

    async def test_patch_with_text_plain_rejected(self, middleware_client):
        """PATCH with text/plain should return 415."""
        response = await middleware_client.patch(
            "/api/admin/categories/1",
            headers={"Content-Type": "text/plain"},
            content="data",
        )
        assert response.status_code == 415


# ---------------------------------------------------------------------------
# REQ-SEC-03: CORS
# ---------------------------------------------------------------------------


class TestCORS:
    """Verify CORS configuration for preflight and actual requests."""

    async def test_preflight_allowed_origin(self, middleware_client):
        """OPTIONS request from allowed origin should return CORS headers."""
        response = await middleware_client.options(
            "/api/health/live",
            headers={
                "Origin": "http://localhost:5177",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5177"
        assert "authorization" in response.headers.get("access-control-allow-headers", "").lower()

    async def test_preflight_disallowed_origin(self, middleware_client):
        """OPTIONS request from disallowed origin should not have CORS headers."""
        response = await middleware_client.options(
            "/api/health/live",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in response.headers

    async def test_credentials_allowed(self, middleware_client):
        """CORS should allow credentials (HttpOnly cookies)."""
        response = await middleware_client.options(
            "/api/health/live",
            headers={
                "Origin": "http://localhost:5176",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.headers.get("access-control-allow-credentials") == "true"

    async def test_x_request_id_exposed(self, middleware_client):
        """X-Request-ID should be in the expose-headers list on actual responses."""
        response = await middleware_client.get(
            "/api/health/live",
            headers={
                "Origin": "http://localhost:5178",
            },
        )
        exposed = response.headers.get("access-control-expose-headers", "")
        assert "x-request-id" in exposed.lower()

    async def test_all_dev_ports_allowed(self, middleware_client):
        """All localhost dev ports (5173-5180) should be allowed."""
        for port in range(5173, 5181):
            response = await middleware_client.options(
                "/api/health/live",
                headers={
                    "Origin": f"http://localhost:{port}",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert response.headers.get("access-control-allow-origin") == f"http://localhost:{port}", (
                f"Port {port} should be allowed"
            )


# ---------------------------------------------------------------------------
# REQ-SEC-04: Correlation ID
# ---------------------------------------------------------------------------


class TestCorrelationId:
    """Verify X-Request-ID generation and forwarding."""

    async def test_request_id_generated(self, middleware_client):
        """Every response should include an X-Request-ID header."""
        response = await middleware_client.get("/api/health/live")
        request_id = response.headers.get("x-request-id")
        assert request_id is not None
        assert len(request_id) > 0

    async def test_request_id_forwarded(self, middleware_client):
        """If client sends X-Request-ID, it should be forwarded."""
        custom_id = "test-correlation-123"
        response = await middleware_client.get(
            "/api/health/live",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers.get("x-request-id") == custom_id

    async def test_request_id_is_uuid_when_generated(self, middleware_client):
        """Generated X-Request-ID should be a valid UUID4 format."""
        response = await middleware_client.get("/api/health/live")
        request_id = response.headers.get("x-request-id")
        # UUID4 format: 8-4-4-4-12 hex chars
        parts = request_id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
