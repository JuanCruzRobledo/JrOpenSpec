"""Tests for Redis cache behavior: TTL, Cache-Control header, and key invalidation.

Scenario S12: Cache Invalidation
- Public menu is cached on first request (cache miss → setex with TTL=300)
- Second request with a primed cache is served from cache (no DB hit)
- Product update should invalidate menu and product-detail cache keys
- Allergen update should invalidate allergen and menu cache keys

Redis approach: Mock Redis
  The conftest already provides `mock_redis` (AsyncMock) injected into the app via
  dependency_overrides[get_redis]. All tests assert on that mock's call_args_list.
  With asyncio_mode=auto in pytest.ini, no @pytest.mark.asyncio decorator is needed.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from rest_api.app.services.cache_service import CacheService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _async_return(value):
    return value


# ---------------------------------------------------------------------------
# CacheService unit tests — get_or_set contract: cache miss
# ---------------------------------------------------------------------------


async def test_menu_cached_on_first_request(mock_redis: AsyncMock) -> None:
    """Cache miss path: redis.get returns None → factory called → setex stores result.

    Asserts:
    - redis.get is called with the exact menu cache key
    - redis.setex is called with TTL=300
    - Factory result is returned unchanged
    """
    mock_redis.get.return_value = None  # force cache miss

    cache = CacheService(mock_redis, default_ttl=300)

    async def factory():
        return {"categories": [], "branch": {"slug": "test-branch"}, "generatedAt": "2026-01-01"}

    result = await cache.get_or_set("cache:public:menu:test-branch", factory, ttl=300)

    # redis.get was called with the exact key
    mock_redis.get.assert_called_once_with("cache:public:menu:test-branch")

    # redis.setex was called — TTL must be 300
    mock_redis.setex.assert_called_once()
    key_arg, ttl_arg, _payload = mock_redis.setex.call_args.args
    assert key_arg == "cache:public:menu:test-branch"
    assert ttl_arg == 300

    # factory result is returned as-is
    assert result["branch"]["slug"] == "test-branch"


# ---------------------------------------------------------------------------
# CacheService unit tests — get_or_set contract: cache hit
# ---------------------------------------------------------------------------


async def test_menu_served_from_cache(mock_redis: AsyncMock) -> None:
    """Cache hit path: redis.get returns serialized JSON → factory is NOT called.

    Asserts:
    - Factory is never executed
    - Cached value is returned
    - setex is NOT called (no re-store on hit)
    """
    cached_payload = {
        "categories": [],
        "branch": {"slug": "cached-branch"},
        "generatedAt": "2026-01-01",
    }
    mock_redis.get.return_value = json.dumps(cached_payload).encode()

    cache = CacheService(mock_redis, default_ttl=300)

    factory_called = False

    async def factory():
        nonlocal factory_called
        factory_called = True
        return {"branch": {"slug": "db-branch"}}

    result = await cache.get_or_set("cache:public:menu:cached-branch", factory, ttl=300)

    assert not factory_called, "Factory must NOT be called on a cache hit"
    assert result["branch"]["slug"] == "cached-branch"
    mock_redis.setex.assert_not_called()


# ---------------------------------------------------------------------------
# CacheService unit tests — TTL contract
# ---------------------------------------------------------------------------


async def test_cache_ttl_is_300(mock_redis: AsyncMock) -> None:
    """After a cache miss, setex is always called with ttl=300 (the public menu contract)."""
    mock_redis.get.return_value = None

    cache = CacheService(mock_redis, default_ttl=300)

    await cache.get_or_set(
        "cache:public:menu:buen-sabor-centro",
        lambda: _async_return({"ok": True}),
        ttl=300,
    )

    _, ttl_arg, _ = mock_redis.setex.call_args.args
    assert ttl_arg == 300, f"Expected TTL=300, got {ttl_arg}"


# ---------------------------------------------------------------------------
# CacheService unit tests — invalidation: product update key patterns
# ---------------------------------------------------------------------------


async def test_product_update_invalidates_menu_cache(mock_redis: AsyncMock) -> None:
    """invalidate_pattern with menu key glob triggers scan_iter then delete per key.

    Simulates what happens when a product is updated:
      pattern = "cache:public:menu:{branch_slug}*"
    The cache layer must scan for matching keys and delete each one.
    """
    branch_slug = "buen-sabor-centro"
    expected_pattern = f"cache:public:menu:{branch_slug}*"
    cached_key = f"cache:public:menu:{branch_slug}".encode()

    async def fake_scan_iter(match: str, count: int):
        if match == expected_pattern:
            yield cached_key

    mock_redis.scan_iter = fake_scan_iter

    cache = CacheService(mock_redis)
    deleted = await cache.invalidate_pattern(expected_pattern)

    mock_redis.delete.assert_called_once_with(cached_key)
    assert deleted == 1


async def test_product_update_invalidates_product_cache(mock_redis: AsyncMock) -> None:
    """invalidate_pattern with product key glob deletes product-detail cache keys.

    Simulates: cache:public:product:*:{product_id}
    """
    product_id = 42
    expected_pattern = f"cache:public:product:*:{product_id}"
    cached_key = f"cache:public:product:centro:{product_id}".encode()

    async def fake_scan_iter(match: str, count: int):
        if match == expected_pattern:
            yield cached_key

    mock_redis.scan_iter = fake_scan_iter

    cache = CacheService(mock_redis)
    deleted = await cache.invalidate_pattern(expected_pattern)

    mock_redis.delete.assert_called_once_with(cached_key)
    assert deleted == 1


# ---------------------------------------------------------------------------
# CacheService unit tests — invalidation: allergen update key patterns
# ---------------------------------------------------------------------------


async def test_allergen_update_invalidates_allergen_cache(mock_redis: AsyncMock) -> None:
    """invalidate_pattern with allergen key deletes the allergen catalog cache.

    Pattern: cache:public:allergens:{tenant_slug}
    """
    tenant_slug = "buen-sabor"
    expected_pattern = f"cache:public:allergens:{tenant_slug}"
    cached_key = expected_pattern.encode()

    async def fake_scan_iter(match: str, count: int):
        if match == expected_pattern:
            yield cached_key

    mock_redis.scan_iter = fake_scan_iter

    cache = CacheService(mock_redis)
    deleted = await cache.invalidate_pattern(expected_pattern)

    mock_redis.delete.assert_called_once_with(cached_key)
    assert deleted == 1


async def test_allergen_update_invalidates_menu_cache(mock_redis: AsyncMock) -> None:
    """invalidate_pattern with branch menu glob deletes all cached menu variants.

    When an allergen changes, all menu cache keys for that branch must be swept.
    This covers both the base key and any filtered-query variants.
    Pattern: cache:public:menu:{branch_slug}*
    """
    branch_slug = "buen-sabor-centro"
    pattern = f"cache:public:menu:{branch_slug}*"

    base_key = f"cache:public:menu:{branch_slug}".encode()
    filtered_key = f"cache:public:menu:{branch_slug}:q:abc123".encode()

    deleted_keys: list[bytes] = []

    async def fake_scan_iter(match: str, count: int):
        yield base_key
        yield filtered_key

    async def fake_delete(key):
        deleted_keys.append(key)
        return 1

    mock_redis.scan_iter = fake_scan_iter
    mock_redis.delete = AsyncMock(side_effect=fake_delete)

    cache = CacheService(mock_redis)
    deleted = await cache.invalidate_pattern(pattern)

    assert deleted == 2
    assert base_key in deleted_keys
    assert filtered_key in deleted_keys


# ---------------------------------------------------------------------------
# HTTP integration tests — Cache-Control header on public endpoints
# ---------------------------------------------------------------------------


async def test_cache_control_header_present(
    client: AsyncClient,
    seed_tenant,
    seed_branch,
) -> None:
    """All public endpoints return Cache-Control: public, max-age=300.

    Uses the real HTTP client with mock Redis injected by the app fixture.
    A 404 body is fine — the Cache-Control header must still be present.
    """
    branch_slug = seed_branch.slug
    tenant_slug = seed_tenant.slug

    # Menu endpoint
    resp = await client.get(f"/api/public/menu/{branch_slug}")
    assert resp.headers.get("cache-control") == "public, max-age=300", (
        f"Menu endpoint missing Cache-Control header, got: {resp.headers.get('cache-control')!r}"
    )

    # Allergens endpoint
    resp = await client.get(f"/api/public/allergens/?tenant={tenant_slug}")
    assert resp.headers.get("cache-control") == "public, max-age=300", (
        f"Allergens endpoint missing Cache-Control header, got: {resp.headers.get('cache-control')!r}"
    )

    # Branches endpoint
    resp = await client.get(f"/api/public/branches/?tenant={tenant_slug}")
    assert resp.headers.get("cache-control") == "public, max-age=300", (
        f"Branches endpoint missing Cache-Control header, got: {resp.headers.get('cache-control')!r}"
    )
