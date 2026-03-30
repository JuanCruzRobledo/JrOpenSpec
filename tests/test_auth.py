"""Focused auth tests for foundation-auth verify readiness."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rest_api.app.main import create_app
from shared.infrastructure.db import get_db, safe_commit
from shared.infrastructure.redis import get_redis
from shared.models.core.branch import Branch
from shared.models.core.refresh_token import RefreshToken
from shared.models.core.tenant import Tenant
from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
from shared.security.jwt import decode_token
from shared.security.passwords import hash_password

from rest_api.app.services.auth_service import AuthenticationError, AuthService


class FakeRedisPipeline:
    def __init__(self, redis: "FakeRedis"):
        self.redis = redis
        self.operations: list[tuple[str, tuple, dict]] = []

    def _add(self, name: str, *args, **kwargs) -> "FakeRedisPipeline":
        self.operations.append((name, args, kwargs))
        return self

    def zadd(self, *args, **kwargs) -> "FakeRedisPipeline":
        return self._add("zadd", *args, **kwargs)

    def zremrangebyscore(self, *args, **kwargs) -> "FakeRedisPipeline":
        return self._add("zremrangebyscore", *args, **kwargs)

    def zcard(self, *args, **kwargs) -> "FakeRedisPipeline":
        return self._add("zcard", *args, **kwargs)

    def expire(self, *args, **kwargs) -> "FakeRedisPipeline":
        return self._add("expire", *args, **kwargs)

    def setex(self, *args, **kwargs) -> "FakeRedisPipeline":
        return self._add("setex", *args, **kwargs)

    def delete(self, *args, **kwargs) -> "FakeRedisPipeline":
        return self._add("delete", *args, **kwargs)

    async def execute(self) -> list[object]:
        results = []
        for name, args, kwargs in self.operations:
            method = getattr(self.redis, name)
            results.append(await method(*args, **kwargs))
        self.operations.clear()
        return results


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.zsets: dict[str, dict[str, int]] = {}
        self.expirations: dict[str, float] = {}
        self.fail_operations: set[str] = set()

    def pipeline(self) -> FakeRedisPipeline:
        return FakeRedisPipeline(self)

    def _maybe_fail(self, operation: str) -> None:
        if operation in self.fail_operations:
            raise RuntimeError(f"forced redis failure: {operation}")

    def _is_expired(self, key: str) -> bool:
        expires_at = self.expirations.get(key)
        return expires_at is not None and expires_at <= time.time()

    def _cleanup_key(self, key: str) -> None:
        if not self._is_expired(key):
            return
        self.expirations.pop(key, None)
        self.values.pop(key, None)
        self.zsets.pop(key, None)

    async def get(self, key: str):
        self._maybe_fail("get")
        self._cleanup_key(key)
        return self.values.get(key)

    async def setex(self, key: str, ttl_seconds: int, value: str):
        self._maybe_fail("setex")
        self.values[key] = value
        self.expirations[key] = time.time() + ttl_seconds
        return True

    async def delete(self, *keys: str):
        self._maybe_fail("delete")
        deleted = 0
        for key in keys:
            self._cleanup_key(key)
            if key in self.values or key in self.zsets or key in self.expirations:
                deleted += 1
            self.values.pop(key, None)
            self.zsets.pop(key, None)
            self.expirations.pop(key, None)
        return deleted

    async def incr(self, key: str):
        self._maybe_fail("incr")
        self._cleanup_key(key)
        value = int(self.values.get(key, "0")) + 1
        self.values[key] = str(value)
        return value

    async def expire(self, key: str, ttl_seconds: int):
        self._maybe_fail("expire")
        self._cleanup_key(key)
        self.expirations[key] = time.time() + ttl_seconds
        return True

    async def ttl(self, key: str):
        self._maybe_fail("ttl")
        self._cleanup_key(key)
        expires_at = self.expirations.get(key)
        if expires_at is None:
            return -1
        return max(int(expires_at - time.time()), 0)

    async def zadd(self, key: str, mapping: dict[str, int]):
        self._maybe_fail("zadd")
        self._cleanup_key(key)
        zset = self.zsets.setdefault(key, {})
        zset.update(mapping)
        return len(mapping)

    async def zremrangebyscore(self, key: str, min_score: int, max_score: int):
        self._maybe_fail("zremrangebyscore")
        self._cleanup_key(key)
        zset = self.zsets.get(key, {})
        to_delete = [member for member, score in zset.items() if min_score <= score <= max_score]
        for member in to_delete:
            del zset[member]
        if not zset:
            self.zsets.pop(key, None)
        return len(to_delete)

    async def zcard(self, key: str):
        self._maybe_fail("zcard")
        self._cleanup_key(key)
        return len(self.zsets.get(key, {}))


async def _seed_auth_user(db_session: AsyncSession) -> User:
    tenant = Tenant(id=1, name="Tenant Test", slug="tenant-test")
    branch = Branch(id=1, tenant_id=1, name="Casa Central", slug="casa-central")
    user = User(
        id=1,
        tenant_id=1,
        email="admin@test.com",
        hashed_password=hash_password("correct_password"),
        first_name="Ada",
        last_name="Lovelace",
        is_superadmin=False,
    )
    branch_role = UserBranchRole(id=1, user_id=1, branch_id=1, role="ADMIN")
    db_session.add_all([tenant, branch, user, branch_role])
    await safe_commit(db_session)
    return user


@asynccontextmanager
async def _build_auth_client(
    db_session: AsyncSession,
    redis_client: FakeRedis,
) -> AsyncGenerator[AsyncClient, None]:
    application = create_app()

    async def _override_get_db():
        yield db_session

    async def _override_get_redis():
        return redis_client

    application.dependency_overrides[get_db] = _override_get_db
    application.dependency_overrides[get_redis] = _override_get_redis

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest_asyncio.fixture
async def auth_service(db_session: AsyncSession, fake_redis: FakeRedis) -> AuthService:
    await _seed_auth_user(db_session)
    return AuthService(db=db_session, redis_client=fake_redis)


class TestRefreshRotation:
    async def test_refresh_rotation_persists_lineage_and_blacklists_prior_access(
        self,
        auth_service: AuthService,
        db_session: AsyncSession,
        fake_redis: FakeRedis,
    ):
        access_token, refresh_token = await auth_service.login(
            email="admin@test.com",
            password="correct_password",
            ip_address="127.0.0.1",
        )

        new_access_token, new_refresh_token = await auth_service.refresh(
            refresh_token,
            current_access_token=access_token,
        )

        refresh_tokens = (
            await db_session.execute(select(RefreshToken).order_by(RefreshToken.id.asc()))
        ).scalars().all()

        assert len(refresh_tokens) == 2
        assert refresh_tokens[0].revoked_at is not None
        assert refresh_tokens[0].replaced_by_id == refresh_tokens[1].id
        assert refresh_tokens[0].family_id == refresh_tokens[1].family_id
        assert refresh_tokens[1].revoked_at is None
        assert new_access_token != access_token
        assert new_refresh_token != refresh_token

        blacklisted_jti = decode_token(access_token)["jti"]
        assert await fake_redis.get(f"blacklist:{blacklisted_jti}") == "1"

    async def test_refresh_reuse_revokes_entire_family(
        self,
        auth_service: AuthService,
        db_session: AsyncSession,
    ):
        access_token, refresh_token = await auth_service.login(
            email="admin@test.com",
            password="correct_password",
            ip_address="127.0.0.1",
        )
        _, rotated_refresh = await auth_service.refresh(
            refresh_token,
            current_access_token=access_token,
        )

        with pytest.raises(AuthenticationError, match="Refresh token reuse detected"):
            await auth_service.refresh(refresh_token)

        refresh_tokens = (
            await db_session.execute(select(RefreshToken).order_by(RefreshToken.id.asc()))
        ).scalars().all()

        assert len(refresh_tokens) == 2
        assert all(token.revoked_at is not None for token in refresh_tokens)
        assert rotated_refresh


class TestLogoutAndRedisFailures:
    async def test_logout_blacklists_access_and_revokes_family(
        self,
        auth_service: AuthService,
        db_session: AsyncSession,
        fake_redis: FakeRedis,
    ):
        access_token, refresh_token = await auth_service.login(
            email="admin@test.com",
            password="correct_password",
            ip_address="127.0.0.1",
        )

        await auth_service.logout(access_token, refresh_token_str=refresh_token)

        blacklisted_jti = decode_token(access_token)["jti"]
        assert await fake_redis.get(f"blacklist:{blacklisted_jti}") == "1"

        refresh_tokens = (await db_session.execute(select(RefreshToken))).scalars().all()
        assert refresh_tokens
        assert all(token.revoked_at is not None for token in refresh_tokens)

    async def test_login_succeeds_when_redis_check_fails(
        self,
        auth_service: AuthService,
        fake_redis: FakeRedis,
    ):
        fake_redis.fail_operations.add("ttl")

        access_token, refresh_token = await auth_service.login(
            email="admin@test.com",
            password="correct_password",
            ip_address="127.0.0.1",
        )

        assert access_token
        assert refresh_token

    async def test_login_invalid_password_raises_authentication_error(
        self,
        auth_service: AuthService,
    ):
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            await auth_service.login(
                email="admin@test.com",
                password="wrong_password",
                ip_address="127.0.0.1",
            )


class TestLoginRateLimitRoute:
    async def test_login_route_returns_token_cookie_and_me_profile(
        self,
        db_session: AsyncSession,
    ):
        redis_client = FakeRedis()
        await _seed_auth_user(db_session)

        async with _build_auth_client(db_session, redis_client) as client:
            login_response = await client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "correct_password"},
            )

            assert login_response.status_code == 200
            body = login_response.json()
            assert body["access_token"]
            assert body["token_type"] == "bearer"

            set_cookie = login_response.headers.get("set-cookie", "")
            assert "refresh_token=" in set_cookie
            assert "HttpOnly" in set_cookie
            assert "Path=/api/auth" in set_cookie

            me_response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {body['access_token']}"},
            )

        assert me_response.status_code == 200
        assert me_response.json() == {
            "id": 1,
            "email": "admin@test.com",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["ADMIN"],
            "is_superadmin": False,
        }

    async def test_login_returns_stable_429_body_and_retry_after(
        self,
        db_session: AsyncSession,
    ):
        redis_client = FakeRedis()
        await _seed_auth_user(db_session)

        async with _build_auth_client(db_session, redis_client) as client:
            for _ in range(4):
                response = await client.post(
                    "/api/auth/login",
                    json={"email": "admin@test.com", "password": "wrong_password"},
                )
                assert response.status_code == 401

            response = await client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "wrong_password"},
            )

        assert response.status_code == 429
        assert response.headers["Retry-After"]
        assert response.json()["detail"] == "Too many login attempts"
        assert response.json()["code"] == "login_rate_limited"
        assert response.json()["retry_after"] >= 1

    async def test_me_fails_closed_when_blacklist_lookup_errors(
        self,
        db_session: AsyncSession,
    ):
        redis_client = FakeRedis()
        await _seed_auth_user(db_session)

        async with _build_auth_client(db_session, redis_client) as client:
            login_response = await client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "correct_password"},
            )
            access_token = login_response.json()["access_token"]
            redis_client.fail_operations.add("get")

            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        assert response.status_code == 401
        assert response.json() == {"detail": "Token has been revoked"}


class TestBlacklistedTokenDenied:
    async def test_blacklisted_token_rejected_by_me(
        self,
        db_session: AsyncSession,
    ):
        redis_client = FakeRedis()
        await _seed_auth_user(db_session)

        async with _build_auth_client(db_session, redis_client) as client:
            login_response = await client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "correct_password"},
            )
            access_token = login_response.json()["access_token"]
            refresh_cookie = login_response.cookies.get("refresh_token", "")

            await client.post(
                "/api/auth/logout",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                cookies={"refresh_token": refresh_cookie},
            )

            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Token has been revoked"


class TestTenantScopingExplicit:
    async def test_me_returns_only_own_tenant_data(
        self,
        db_session: AsyncSession,
    ):
        redis_client = FakeRedis()

        tenant1 = Tenant(id=1, name="Tenant One", slug="tenant-one")
        tenant2 = Tenant(id=2, name="Tenant Two", slug="tenant-two")
        branch1 = Branch(id=1, tenant_id=1, name="Branch T1", slug="branch-t1")
        branch2 = Branch(id=2, tenant_id=2, name="Branch T2", slug="branch-t2")
        user1 = User(
            id=1,
            tenant_id=1,
            email="user1@test.com",
            hashed_password=hash_password("pass1"),
            first_name="User",
            last_name="One",
            is_superadmin=False,
        )
        user2 = User(
            id=2,
            tenant_id=2,
            email="user2@test.com",
            hashed_password=hash_password("pass2"),
            first_name="User",
            last_name="Two",
            is_superadmin=False,
        )
        role1 = UserBranchRole(id=1, user_id=1, branch_id=1, role="ADMIN")
        role2 = UserBranchRole(id=2, user_id=2, branch_id=2, role="ADMIN")
        db_session.add_all([tenant1, tenant2, branch1, branch2, user1, user2, role1, role2])
        await safe_commit(db_session)

        async with _build_auth_client(db_session, redis_client) as client:
            login_response = await client.post(
                "/api/auth/login",
                json={"email": "user1@test.com", "password": "pass1"},
            )
            access_token = login_response.json()["access_token"]

            me_response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        assert me_response.status_code == 200
        body = me_response.json()
        assert body["tenant_id"] == 1
        assert body["branch_ids"] == [1]
        assert 2 not in body["branch_ids"]
