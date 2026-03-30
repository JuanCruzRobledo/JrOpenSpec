from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.main import create_app
from rest_api.app.services.domain.session_service import SessionService
from shared.config import settings
from shared.infrastructure.db import get_db, safe_commit
from shared.models.core.branch import Branch
from shared.models.core.tenant import Tenant
from shared.models.room.sector import Sector
from shared.models.room.table import Table
from shared.security.table_tokens import verify_table_token


@pytest.mark.asyncio
async def test_join_session_returns_public_uuid_without_changing_token_session_id(monkeypatch):
    service = SessionService(db=AsyncMock(), secret="test-secret")

    branch = SimpleNamespace(id=10, name="Buen Sabor Centro", slug="buen-sabor-centro")
    table = SimpleNamespace(id=25, number="mesa-12", status="available")

    monkeypatch.setattr(service, "_get_branch_by_slug", AsyncMock(return_value=branch))
    monkeypatch.setattr(
        service,
        "_get_table_by_branch_and_identifier",
        AsyncMock(return_value=table),
    )

    captured = {}

    def fake_generate_table_token(*, secret, branch_id, table_id, session_id, ttl):
        captured.update(
            {
                "secret": secret,
                "branch_id": branch_id,
                "table_id": table_id,
                "session_id": session_id,
                "ttl": ttl,
            }
        )
        return "signed-token"

    monkeypatch.setattr(
        "rest_api.app.services.domain.session_service.generate_table_token",
        fake_generate_table_token,
    )

    result = await service.join_session(
        branch_slug="buen-sabor-centro",
        table_identifier="mesa-12",
        display_name="Juani",
        avatar_color="#F97316",
        locale="es",
    )

    assert result["token"] == "signed-token"
    assert UUID(result["sessionId"]).version == 4
    assert captured == {
        "secret": "test-secret",
        "branch_id": 10,
        "table_id": 25,
        "session_id": 25,
        "ttl": 3 * 60 * 60,
    }


@pytest.mark.asyncio
async def test_join_session_formats_table_display_name(monkeypatch):
    service = SessionService(db=AsyncMock(), secret="test-secret")

    branch = SimpleNamespace(id=10, name="Buen Sabor Centro", slug="buen-sabor-centro")
    table = SimpleNamespace(id=25, number="mesa-12", status="available")

    monkeypatch.setattr(service, "_get_branch_by_slug", AsyncMock(return_value=branch))
    monkeypatch.setattr(
        service,
        "_get_table_by_branch_and_identifier",
        AsyncMock(return_value=table),
    )
    monkeypatch.setattr(
        "rest_api.app.services.domain.session_service.generate_table_token",
        lambda **_: "signed-token",
    )

    result = await service.join_session(
        branch_slug="buen-sabor-centro",
        table_identifier="mesa-12",
        display_name="Juani",
        avatar_color="#F97316",
        locale="es",
    )

    assert result["table"] == {
        "identifier": "mesa-12",
        "displayName": "Mesa 12",
    }


class TestSessionJoinHTTP:
    """REQ-TABLE-01: HTTP-level integration test for POST /api/sessions/join."""

    @pytest_asyncio.fixture
    async def seeded_db(self, db_session: AsyncSession) -> AsyncSession:
        tenant = Tenant(id=1, name="Tenant Test", slug="tenant-test")
        branch = Branch(id=1, tenant_id=1, name="Casa Central", slug="casa-central")
        sector = Sector(id=1, branch_id=1, name="Salon")
        table = Table(id=1, sector_id=1, number="5", status="available")
        db_session.add_all([tenant, branch, sector, table])
        await safe_commit(db_session)
        return db_session

    async def test_join_issues_table_token_with_correct_shape(
        self,
        seeded_db: AsyncSession,
    ):
        application = create_app()

        async def _override_db():
            yield seeded_db

        application.dependency_overrides[get_db] = _override_db

        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/sessions/join",
                json={
                    "branchSlug": "casa-central",
                    "tableIdentifier": "5",
                },
            )

        application.dependency_overrides.clear()

        assert response.status_code == 200
        body = response.json()
        assert body["token"]
        assert body["sessionId"]
        assert body["expiresAt"]
        assert body["branch"]["slug"] == "casa-central"
        assert body["table"]["identifier"] == "5"

        # Token must be a valid HMAC table credential, not a staff JWT
        payload = verify_table_token(settings.TABLE_TOKEN_SECRET, body["token"])
        assert payload["branch_id"] == 1
        assert payload["table_id"] == 1
        assert "roles" not in payload
        assert "tenant_id" not in payload
        assert "sub" not in payload
