---
change: foundation-auth
phase: 2
artifact: proposal
source: sdd-otro/sprint-2-auth
date: 2026-03-23
status: approved
---

# SDD Proposal: Sprint 2 — Autenticación y Multi-tenancy

## 1. Intent

Implement a production-grade authentication and authorization system for Buen Sabor that supports:
- Secure JWT-based login with refresh token rotation
- Role-Based Access Control (RBAC) via Strategy Pattern
- Multi-tenant isolation at the middleware/query level
- Brute-force and rate-limiting protections
- HMAC-based table session tokens for anonymous client ordering

This is the SECURITY FOUNDATION of the entire system. Every subsequent sprint (orders, payments, kitchen, WebSocket) depends on auth + tenant isolation being correct and battle-tested.

## 2. Scope

### In Scope
- Auth endpoints: login, refresh, logout
- JWT access tokens (15min) + refresh tokens (7d, HttpOnly cookie)
- Token blacklist in Redis with TTL-based expiry
- Refresh token rotation with reuse detection (family revocation)
- RBAC: Strategy Pattern with 5 strategies (Admin, Manager, Kitchen, Waiter, ReadOnly)
- Decorators: `@require_role`, `@require_permission`
- Multi-tenant middleware: extract `tenant_id` from JWT, inject into all DB queries
- Rate limiting: 5 req/min per IP+email on login
- Brute-force protection: progressive lockout (1min -> 5min -> 15min)
- Table tokens: HMAC-signed, 3h TTL, for anonymous PWA menu sessions
- Comprehensive test suite for all auth flows

### Out of Scope
- OAuth2 / social login (future sprint)
- 2FA / MFA (future sprint)
- User registration / invitation flow (Sprint 3)
- Password reset / recovery (Sprint 3)
- Frontend auth integration (Sprint 3 -- frontend sprints)
- WebSocket authentication (Sprint 4 -- WS Gateway)

## 3. Affected Modules

| Module | Impact | Description |
|--------|--------|-------------|
| `rest_api/` | **Heavy** | New auth router, middleware, decorators, dependencies |
| `shared/` | **Heavy** | User model, token models, Redis client, RBAC strategies |
| `shared/models/` | **New** | User, RefreshToken, LoginAttempt models |
| `shared/services/` | **New** | AuthService, TokenService, RBACService |
| `shared/repositories/` | **New** | UserRepository, TokenRepository |
| `shared/middleware/` | **New** | TenantMiddleware, AuthMiddleware |
| `shared/security/` | **New** | Password hashing, JWT encode/decode, HMAC utils |
| `shared/redis/` | **New** | Redis client, blacklist manager, rate limiter |

## 4. Approach

### 4.1 Authentication Flow
- Stateless access tokens (JWT, 15min TTL, signed with HS256)
- Stateful refresh tokens (stored in DB + HttpOnly cookie, 7d TTL)
- Token rotation on refresh: old token invalidated, new one issued
- Reuse detection: if a rotated-out refresh token is reused, ALL tokens in the family are revoked (compromise signal)

### 4.2 Token Blacklist (Redis)
- On logout: access token JTI added to Redis SET with TTL = remaining token lifetime
- On refresh: old access token blacklisted
- **Fail-closed**: if Redis is unreachable, ALL token validations fail (deny by default)
- Key pattern: `blacklist:{jti}` with TTL

### 4.3 RBAC via Strategy Pattern
- `PermissionContext` holds the current strategy
- Each strategy (AdminStrategy, ManagerStrategy, etc.) implements `has_permission(permission: str) -> bool` and `get_allowed_resources() -> set[str]`
- Decorators resolve the strategy from the JWT role claim and check permissions
- Permissions are granular strings: `orders:read`, `orders:write`, `menu:manage`, `reports:view`, etc.

### 4.4 Multi-tenant Isolation
- `tenant_id` is a claim in the JWT
- Middleware extracts it and sets it in a context variable (Python contextvars)
- SQLAlchemy query interceptor (event listener on `before_compile`) auto-appends `WHERE tenant_id = :tenant_id` to all queries on tenant-scoped models
- Defense in depth: repository layer ALSO filters by tenant_id explicitly

### 4.5 Rate Limiting & Brute Force
- Redis sliding window for rate limiting (5 req/min per IP+email combo)
- Login attempt counter per email with progressive lockout thresholds
- Lockout durations: attempt 5 -> 1min, attempt 10 -> 5min, attempt 15 -> 15min
- Stored in Redis with auto-expiring keys

### 4.6 Table Tokens (HMAC)
- Signed with HMAC-SHA256 using a server secret
- Payload: `{table_id, tenant_id, session_id, exp}`
- 3-hour TTL, non-renewable
- Used by PWA Menu for anonymous ordering at a specific table
- Validated via signature verification (no DB lookup needed)

## 5. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Redis downtime blocks ALL auth | HIGH | Fail-closed is intentional for security. Add Redis Sentinel/Cluster in prod. Health check endpoint to detect quickly. Circuit breaker with short timeout (500ms). |
| Token rotation race condition | MEDIUM | Use DB-level locking (SELECT FOR UPDATE) on refresh token row. Idempotency window of 5s for duplicate refresh requests with same token. |
| Tenant data leakage | CRITICAL | Defense in depth: middleware + repository + DB-level RLS (future). Comprehensive integration tests with cross-tenant assertions. |
| HMAC secret rotation | LOW | Support multiple active secrets (verify against all, sign with latest). |
| Bcrypt CPU cost on login spike | LOW | Bcrypt work factor 12 (standard). Rate limiting prevents abuse. Async executor for bcrypt to avoid blocking event loop. |
| Progressive lockout DoS | MEDIUM | Lockout is per-email, not per-IP. Legitimate user can contact admin to unlock. CAPTCHA integration point left open for future. |

## 6. Rollback Plan

- **Database**: All new tables (users, refresh_tokens, login_attempts) created via Alembic migration with `downgrade()` that drops them
- **Redis**: Keys are ephemeral with TTL; clearing the blacklist namespace is safe (worst case: already-logged-out tokens work until expiry)
- **Code**: Auth middleware has a feature flag `AUTH_ENABLED` (env var). Set to `false` to bypass all auth checks (dev/emergency only)
- **RBAC**: Decorators are additive; removing them from endpoints restores open access
- **Rollback order**: (1) disable auth flag, (2) downgrade migration, (3) revert code

## 7. Dependencies

- **Sprint 1** (assumed complete): Base project structure, DB connection, base models with AuditMixin, Redis connection setup
- **External**: Redis 7 must be available in Docker Compose
- **Libraries**: python-jose[cryptography], bcrypt, redis[hiredis]

## 8. Success Criteria

- All auth endpoints return correct status codes and tokens
- Expired/blacklisted tokens are rejected within 1 second
- Refresh token reuse triggers full family revocation
- Cross-tenant data access is impossible (proven by tests)
- Rate limiting kicks in after 5 login attempts/min
- Progressive lockout activates correctly at thresholds
- Table tokens validate without DB access
- Redis failure causes auth denial (fail-closed verified)
- Test coverage >= 90% on auth module
