---
change: foundation-auth
phase: 2
artifact: tasks
source: sdd-otro/sprint-2-auth
date: 2026-03-23
status: ready-for-implementation
---

# SDD Tasks: Sprint 2 — Autenticación y Multi-tenancy

## Phase 1: Foundation (Models, DB, Redis)

### Task 1.1: Database Models & Migration
**Files:**
- `shared/models/user.py` -- User model with AuditMixin + TenantScopedMixin
- `shared/models/refresh_token.py` -- RefreshToken model
- `shared/models/__init__.py` -- Export new models
- `alembic/versions/xxxx_add_auth_models.py` -- Alembic migration

**Acceptance Criteria:**
- [ ] User model has: id, tenant_id (FK), email, password_hash, full_name, role (enum), is_active, last_login_at, AuditMixin fields
- [ ] UniqueConstraint on (tenant_id, email) with partial index (WHERE deleted_at IS NULL)
- [ ] RefreshToken model has: id, user_id (FK CASCADE), token_hash (unique), family_id (UUID), expires_at, revoked_at, replaced_by_id (self-FK), ip_address, user_agent, created_at
- [ ] Indexes on token_hash (partial: revoked_at IS NULL), family_id, user_id (partial)
- [ ] Role enum: ADMIN, MANAGER, KITCHEN, WAITER, READONLY as StrEnum
- [ ] Alembic migration applies cleanly with `upgrade()` and `downgrade()`

### Task 1.2: Redis Client & Health Check
**Files:**
- `shared/redis/client.py` -- AsyncRedis connection pool, health check, fail-closed wrapper
- `shared/redis/__init__.py` -- Exports

**Acceptance Criteria:**
- [ ] Async Redis client using `redis.asyncio` with connection pooling
- [ ] `get_redis()` dependency that returns client from pool
- [ ] `health_check()` method that pings Redis
- [ ] `RedisUnavailableError` custom exception
- [ ] All Redis operations wrapped: on ConnectionError/TimeoutError -> raise RedisUnavailableError
- [ ] Connection timeout: 500ms. Operation timeout: 200ms.

### Task 1.3: Password Hashing Utilities
**Files:**
- `shared/security/password.py` -- hash_password, verify_password (async-safe)

**Acceptance Criteria:**
- [ ] `hash_password(plain: str) -> str` using bcrypt with work factor from settings (default 12)
- [ ] `verify_password(plain: str, hashed: str) -> bool` using bcrypt
- [ ] Both functions run in `asyncio.to_thread()` to avoid blocking event loop
- [ ] `dummy_verify()` function that runs bcrypt on a dummy hash (timing attack prevention)

### Task 1.4: Settings / Config
**Files:**
- `shared/config/settings.py` -- Add auth-related settings (or update existing)

**Acceptance Criteria:**
- [ ] All env vars from Design doc section 8.4 are defined as Pydantic Settings fields
- [ ] JWT settings: secret, algorithm, access TTL, refresh TTL
- [ ] HMAC settings: separate secret, TTL
- [ ] Rate limit settings: per-minute limit, lockout thresholds
- [ ] AUTH_ENABLED feature flag (default True)
- [ ] Validation: JWT_SECRET_KEY min length 32 chars

---

## Phase 2: Token Infrastructure

### Task 2.1: JWT Encode/Decode
**Files:**
- `shared/security/jwt.py` -- create_access_token, decode_access_token, JWT claims model

**Acceptance Criteria:**
- [ ] `create_access_token(user_id, tenant_id, role, jti=None) -> str`
- [ ] Claims: sub, tenant_id, role, jti, exp, iat, iss="buensabor", aud="buensabor-api"
- [ ] Signs with HS256 using JWT_SECRET_KEY
- [ ] `decode_access_token(token: str) -> JWTClaims` with explicit `algorithms=["HS256"]`
- [ ] Raises `TokenExpiredError`, `InvalidTokenError` custom exceptions
- [ ] NEVER accepts algorithm "none"

### Task 2.2: Token Blacklist (Redis)
**Files:**
- `shared/redis/blacklist.py` -- add_to_blacklist, is_blacklisted

**Acceptance Criteria:**
- [ ] `add_to_blacklist(jti: str, expires_at: datetime) -> None` -- SET with TTL
- [ ] `is_blacklisted(jti: str) -> bool` -- EXISTS check
- [ ] Key format: `auth:blacklist:{jti}`
- [ ] On Redis error -> raise RedisUnavailableError (fail-closed in caller)

### Task 2.3: Refresh Token Repository
**Files:**
- `shared/repositories/token_repository.py` -- RefreshTokenRepository

**Acceptance Criteria:**
- [ ] `get_by_hash(token_hash: str) -> RefreshToken | None` -- SELECT ... FOR UPDATE
- [ ] `revoke_family(family_id: UUID) -> int` -- UPDATE all in family
- [ ] `set_replaced_by(token_id: int, replaced_by_id: int) -> None`

### Task 2.4: Token Service
**Files:**
- `shared/services/token_service.py` -- TokenService

**Acceptance Criteria:**
- [ ] `create_token_pair(user, ip, user_agent) -> TokenPair`
- [ ] `refresh_tokens(refresh_token_raw, ip, user_agent) -> TokenPair`
- [ ] Implements reuse detection: if token already replaced -> revoke_family -> raise TokenReuseError
- [ ] Idempotency: 5s grace window for duplicate refresh requests
- [ ] `revoke_tokens(access_jti, refresh_token_raw) -> None` -- logout

---

## Phase 3: RBAC

### Task 3.1: Permission Strategies
**Files:**
- `shared/security/rbac/roles.py` -- Role enum
- `shared/security/rbac/strategy.py` -- ABC + 5 strategy implementations
- `shared/security/rbac/factory.py` -- StrategyFactory

**Acceptance Criteria:**
- [ ] `PermissionStrategy` ABC with: `has_permission(p) -> bool`, `get_permissions() -> set[str]`, `get_role() -> Role`
- [ ] `AdminStrategy`: `has_permission()` always returns True
- [ ] All permission sets match the Permission Matrix in the Spec exactly
- [ ] Factory raises ValueError for unknown role

### Task 3.2: Permission Context & Decorators
**Files:**
- `shared/security/rbac/context.py` -- PermissionContext
- `shared/security/rbac/decorators.py` -- @require_role, @require_permission, PermissionChecker

**Acceptance Criteria:**
- [ ] `PermissionContext(strategy, user, tenant_id)` with `.check_permission(p) -> bool`
- [ ] `PermissionChecker(*perms)` -- FastAPI Depends-compatible class (preferred for endpoints)
- [ ] `RoleChecker(*roles)` -- FastAPI Depends-compatible class
- [ ] 403 body: `{"detail": "Insufficient permissions"}`
- [ ] 401 body: `{"detail": "Not authenticated"}`

---

## Phase 4: Middleware & Dependencies

### Task 4.1: Auth Middleware & Dependencies
**Files:**
- `rest_api/dependencies/auth.py` -- get_current_user, get_optional_user

**Acceptance Criteria:**
- [ ] `get_current_user(token: str = Depends(oauth2_scheme)) -> User` dependency
- [ ] Decodes JWT, checks blacklist (Redis), loads user from DB
- [ ] If blacklisted -> 401
- [ ] If Redis unavailable -> 503
- [ ] If user not found / inactive -> 401

### Task 4.2: Tenant Middleware
**Files:**
- `shared/middleware/tenant.py` -- TenantMiddleware, tenant_context, get_current_tenant_id
- `shared/db/tenant_filter.py` -- SQLAlchemy do_orm_execute event listener

**Acceptance Criteria:**
- [ ] `tenant_context = ContextVar("tenant_context", default=None)`
- [ ] TenantMiddleware sets tenant_context from JWT claims on every request
- [ ] Skips tenant extraction for PUBLIC_PATHS
- [ ] SQLAlchemy `do_orm_execute` listener: auto-filters SELECT/UPDATE/DELETE on TenantScopedMixin models
- [ ] `TenantScopedMixin` base mixin with `tenant_id: Mapped[int]`

### Task 4.3: Rate Limiter & Brute Force Protection
**Files:**
- `shared/redis/rate_limiter.py` -- RateLimiter, BruteForceProtection

**Acceptance Criteria:**
- [ ] `RateLimiter.check(ip, email) -> RateLimitResult` -- sliding window in Redis
- [ ] `BruteForceProtection.check_lockout(email) -> LockoutStatus`
- [ ] `BruteForceProtection.record_failure(email) -> LockoutStatus`
- [ ] `BruteForceProtection.reset(email) -> None`
- [ ] Thresholds: `[(5, 60), (10, 300), (15, 900)]`

---

## Phase 5: Auth Endpoints

### Task 5.1: Auth Schemas (Pydantic)
**Files:**
- `rest_api/schemas/auth.py`

**Acceptance Criteria:**
- [ ] `LoginRequest`: email (EmailStr), password (str, min_length=8, max_length=128)
- [ ] `TokenResponse`: access_token, token_type, expires_in, user (UserPublic)
- [ ] `UserPublic`: id, email, full_name, role, tenant_id

### Task 5.2: Auth Service
**Files:**
- `shared/services/auth_service.py`

**Acceptance Criteria:**
- [ ] `login(email, password, ip, user_agent) -> TokenPair`
  1. Rate limit check -> 429 if exceeded
  2. Lockout check -> 429 if locked
  3. User lookup by email
  4. If user not found -> run `dummy_verify()` -> 401
  5. Password verify -> if fail: record_failure -> 401
  6. Create token pair -> update last_login_at -> reset lockout -> return
- [ ] `refresh(refresh_token_raw, ip, user_agent) -> TokenPair`
- [ ] `logout(access_jti, refresh_token_raw) -> None`

### Task 5.3: Auth Router
**Files:**
- `rest_api/routers/auth.py`

**Acceptance Criteria:**
- [ ] `POST /api/auth/login` -- returns TokenResponse (200), sets refresh cookie
- [ ] `POST /api/auth/refresh` -- reads refresh_token from cookie, returns new tokens
- [ ] `POST /api/auth/logout` -- requires Bearer auth, clears cookie
- [ ] Cookie settings: HttpOnly=True, Secure=True, SameSite="lax", Path="/api/auth"

### Task 5.4: Table Token Endpoint
**Files:**
- `rest_api/routers/sessions.py`
- `shared/security/hmac_token.py` -- HMAC token create/verify

**Acceptance Criteria:**
- [ ] `create_table_token(payload: dict) -> str` -- HMAC-SHA256 sign
- [ ] `verify_table_token(token: str) -> TableTokenPayload | None`
- [ ] `POST /api/sessions/table-token` -- requires `table_sessions:create` permission
- [ ] Returns 201 with token, table_id, session_id, expires_in, expires_at

---

## Phase 6: App Wiring

### Task 6.1: FastAPI App Integration
**Files:**
- `rest_api/main.py`

**Acceptance Criteria:**
- [ ] TenantMiddleware registered in middleware stack
- [ ] Auth router mounted at `/api/auth`
- [ ] Sessions router mounted at `/api/sessions`
- [ ] Global exception handlers for RedisUnavailableError, TokenExpiredError, InvalidTokenError
- [ ] AUTH_ENABLED feature flag: if False, bypass auth middleware

---

## Phase 7: Tests

### Task 7.1: Unit Tests -- Security Utilities
- test_hash_password, test_verify_password, test_dummy_verify timing
- test_create_access_token_contains_claims, test_decode_valid_token
- test_decode_expired_token_raises, test_decode_rejects_none_algorithm
- test_create_table_token, test_verify_tampered_table_token

### Task 7.2: Unit Tests -- RBAC
- test_admin_has_all_permissions, test_manager_permissions_match_matrix
- test_permission_context, test_permission_checker (allows/rejects)

### Task 7.3: Integration Tests -- Auth Flow
- test_login_success, test_login_invalid_password (401), test_login_inactive_user
- test_access_protected_endpoint, test_logout_blacklists_token

### Task 7.4: Integration Tests -- Token Rotation
- test_refresh_returns_new_tokens, test_reuse_detection_revokes_entire_family
- test_concurrent_refresh_no_corruption

### Task 7.5: Integration Tests -- Multi-tenant Isolation
- test_tenant_1_cannot_read_tenant_2_data
- test_auto_filter_applies_to_select/update/delete

---

## Implementation Order

```
Phase 1 (Foundation):     1.1 -> 1.2 -> 1.3 -> 1.4 (sequential)
Phase 2 (Tokens):         2.1 -> 2.2 -> 2.3 -> 2.4 (sequential)
Phase 3 (RBAC):           3.1 -> 3.2 (parallel to Phase 2)
Phase 4 (Middleware):      4.1 + 4.2 (parallel) -> 4.3
Phase 5 (Endpoints):      5.1 -> 5.2 -> 5.3 + 5.4 (parallel)
Phase 6 (Wiring):         6.1 (after all phases 1-5)
Phase 7 (Tests):          7.1-7.5
```

**Critical path**: 1.1 -> 1.2 -> 2.1 -> 2.2 -> 2.3 -> 2.4 -> 5.2 -> 5.3 -> 6.1

**Estimated tasks**: 23 tasks across 7 phases
**Estimated files**: ~40 new files (implementation + tests)
