"""Test fixtures for the Integrador REST API integration tests.

Provides:
- Async test client (httpx.AsyncClient) with the FastAPI app
- Database session with schema reset per test (no persistent state)
- Redis mock/fixture
- Authenticated client factory with role-based tokens
- Test user creation helpers
- Menu-domain fixtures: seed_tenant, seed_branch, seed_allergens, seed_product
"""

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
from shared.models.catalog.allergen import Allergen
from shared.models.catalog.branch_product import BranchProduct
from shared.models.catalog.category import Category
from shared.models.catalog.product import Product
from shared.models.catalog.subcategory import Subcategory
from shared.models.core.branch import Branch
from shared.models.core.tenant import Tenant

from rest_api.app.main import create_app


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

# Use the same DB URL for tests — override with TEST_DATABASE_URL if needed
_TEST_DB_URL = getattr(settings, "TEST_DATABASE_URL", None) or settings.DATABASE_URL

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session with schema reset per test.

    Recreates the schema for every test so helpers that call `safe_commit()` do not
    leak state into later tests. Each test still gets its own engine/session to avoid
    event loop mismatch issues with longer-lived fixtures.
    """
    engine = create_async_engine(_TEST_DB_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


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
    """Create a test application with overridden dependencies.

    Rate limiting is disabled by default to prevent cross-test interference.
    Use the ``enable_rate_limit`` fixture in tests that need 429 behavior.
    """
    from rest_api.app.middleware.rate_limit import limiter

    application = create_app()

    # Disable rate limiting globally for all tests by default
    limiter.enabled = False

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
    limiter.enabled = False  # ensure limiter is disabled after each test


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


# ---------------------------------------------------------------------------
# Rate limit control
# ---------------------------------------------------------------------------


@pytest.fixture
def enable_rate_limit():
    """Re-enable the rate limiter for tests that verify 429 behavior.

    Usage: include this fixture in any test that asserts HTTP 429 responses.
    The limiter is restored to disabled after the test completes.
    """
    from rest_api.app.middleware.rate_limit import limiter

    limiter.enabled = True
    yield
    limiter.enabled = False


# ---------------------------------------------------------------------------
# Menu-domain seed fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def seed_tenant(db_session: AsyncSession) -> Tenant:
    """Create and commit a test Tenant."""
    tenant = Tenant(
        name="Test Restaurant",
        slug="test-restaurant",
    )
    db_session.add(tenant)
    await db_session.commit()
    return tenant


@pytest_asyncio.fixture
async def seed_branch(db_session: AsyncSession, seed_tenant: Tenant) -> Branch:
    """Create and commit a test Branch linked to seed_tenant."""
    branch = Branch(
        tenant_id=seed_tenant.id,
        name="Test Branch",
        slug="test-branch",
    )
    db_session.add(branch)
    await db_session.commit()
    return branch


@pytest_asyncio.fixture
async def seed_allergens(db_session: AsyncSession) -> list[Allergen]:
    """Create and commit 4 system allergens (gluten, dairy, peanuts, tree_nuts).

    These mirror the EU-14 system rows produced by migration 005.
    ``tenant_id=None`` and ``is_system=True`` match the system seed contract.
    """
    allergens = [
        Allergen(code="gluten", name="Gluten", is_system=True, tenant_id=None),
        Allergen(code="dairy", name="Lácteos", is_system=True, tenant_id=None),
        Allergen(code="peanuts", name="Maní", is_system=True, tenant_id=None),
        Allergen(code="tree_nuts", name="Frutos de cáscara", is_system=True, tenant_id=None),
    ]
    db_session.add_all(allergens)
    await db_session.commit()
    return allergens


@pytest_asyncio.fixture
async def seed_product(
    db_session: AsyncSession,
    seed_tenant: Tenant,
    seed_branch: Branch,
) -> Product:
    """Create and commit a Product with a BranchProduct entry for seed_branch.

    Creates the required Category → Subcategory → Product chain.
    The BranchProduct has ``is_available=True`` and ``base_price_cents=1000``.
    Returns the ``Product`` ORM object.
    """
    # Category is required by Subcategory FK
    category = Category(
        tenant_id=seed_tenant.id,
        name="Test Category",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.flush()

    subcategory = Subcategory(
        category_id=category.id,
        name="Test Subcategory",
        slug="test-subcategory",
    )
    db_session.add(subcategory)
    await db_session.flush()

    product = Product(
        tenant_id=seed_tenant.id,
        subcategory_id=subcategory.id,
        name="Test Product",
        slug="test-product",
        base_price_cents=1000,
        is_available=True,
        is_visible_in_menu=True,
    )
    db_session.add(product)
    await db_session.flush()

    branch_product = BranchProduct(
        branch_id=seed_branch.id,
        product_id=product.id,
        is_available=True,
        price_cents=None,  # use base_price_cents by default; override per test
    )
    db_session.add(branch_product)
    await db_session.commit()

    return product
