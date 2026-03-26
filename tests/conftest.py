"""Test fixtures for the Integrador REST API integration tests.

Provides:
- Async test client (httpx.AsyncClient) with the FastAPI app
- Database session with transaction rollback (no persistent state)
- Redis mock/fixture
- Authenticated client factory with role-based tokens
- Test user creation helpers
"""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config import settings
from shared.infrastructure.db import get_db
from shared.infrastructure.redis import get_redis
from shared.models.base import Base

from rest_api.app.main import create_app


# ---------------------------------------------------------------------------
# Event loop
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

# Use the same DB URL for tests — override with TEST_DATABASE_URL if needed
_TEST_DB_URL = getattr(settings, "TEST_DATABASE_URL", None) or settings.DATABASE_URL

_test_engine = create_async_engine(_TEST_DB_URL, echo=False)
_test_session_factory = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create all tables at session start, drop at session end."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session that rolls back after each test."""
    async with _test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


# ---------------------------------------------------------------------------
# Redis fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_redis() -> AsyncMock:
    """Provide a mock Redis client for tests that don't need real Redis."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.incr = AsyncMock(return_value=1)
    redis_mock.expire = AsyncMock(return_value=True)
    redis_mock.ttl = AsyncMock(return_value=-1)
    redis_mock.ping = AsyncMock(return_value=True)
    redis_mock.pipeline = MagicMock(return_value=_make_pipeline_mock())
    return redis_mock


def _make_pipeline_mock():
    """Create a pipeline mock that supports chained calls."""
    pipe = AsyncMock()
    pipe.incr = MagicMock(return_value=pipe)
    pipe.expire = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(return_value=[1, True])
    return pipe


# ---------------------------------------------------------------------------
# Application / HTTP client fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def app(db_session: AsyncSession, mock_redis: AsyncMock):
    """Create a test application with overridden dependencies."""
    application = create_app()

    # Override database dependency
    async def _override_get_db():
        yield db_session

    # Override Redis dependency
    async def _override_get_redis():
        return mock_redis

    application.dependency_overrides[get_db] = _override_get_db
    application.dependency_overrides[get_redis] = _override_get_redis

    yield application

    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

# Sample user data for tests
TEST_USERS = {
    "ADMIN": {
        "sub": "1",
        "email": "admin@test.com",
        "tenant_id": 1,
        "branch_ids": [1, 2],
        "roles": ["ADMIN"],
        "first_name": "Test",
        "last_name": "Admin",
        "is_superadmin": False,
    },
    "MANAGER": {
        "sub": "2",
        "email": "manager@test.com",
        "tenant_id": 1,
        "branch_ids": [1],
        "roles": ["MANAGER"],
        "first_name": "Test",
        "last_name": "Manager",
        "is_superadmin": False,
    },
    "WAITER": {
        "sub": "3",
        "email": "waiter@test.com",
        "tenant_id": 1,
        "branch_ids": [1],
        "roles": ["WAITER"],
        "first_name": "Test",
        "last_name": "Waiter",
        "is_superadmin": False,
    },
    "KITCHEN": {
        "sub": "4",
        "email": "kitchen@test.com",
        "tenant_id": 1,
        "branch_ids": [1],
        "roles": ["KITCHEN"],
        "first_name": "Test",
        "last_name": "Kitchen",
        "is_superadmin": False,
    },
}


def auth_headers(role: str = "ADMIN") -> dict[str, str]:
    """Generate Authorization headers with a test JWT for the given role.

    This creates a real JWT token using the application's JWT_SECRET.
    Requires shared.security.jwt to be available (Batch A dependency).

    For tests that run BEFORE Batch A is merged, use `mock_auth_headers` instead.
    """
    try:
        from shared.security.jwt import create_access_token

        user_data = TEST_USERS[role]
        token, _jti = create_access_token(
            user_id=int(user_data["sub"]),
            tenant_id=user_data["tenant_id"],
            branch_ids=user_data["branch_ids"],
            roles=user_data["roles"],
        )
        return {"Authorization": f"Bearer {token}"}
    except ImportError:
        # Batch A not yet merged — return a placeholder header
        return {"Authorization": "Bearer test-token-placeholder"}


def mock_auth_headers() -> dict[str, str]:
    """Return mock auth headers for tests that don't need real JWT validation."""
    return {"Authorization": "Bearer mock-test-token"}


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    """Provide an async client with ADMIN auth headers pre-set."""
    headers = auth_headers("ADMIN")
    client.headers.update(headers)
    return client
