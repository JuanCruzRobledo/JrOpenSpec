---
change: foundation-auth
phase: 2
artifact: spec
source: sdd-otro/sprint-2-auth
date: 2026-03-23
status: approved
---

# SDD Spec: Sprint 2 — Autenticación y Multi-tenancy

## 1. Requirements (RFC 2119)

### 1.1 Authentication

- **AUTH-001**: The system MUST provide a `POST /api/auth/login` endpoint that accepts `email` and `password` in the request body.
- **AUTH-002**: On successful login, the system MUST return an access token (JWT) in the response body with a 15-minute TTL.
- **AUTH-003**: On successful login, the system MUST set a refresh token as an HttpOnly, Secure, SameSite=Lax cookie with a 7-day TTL.
- **AUTH-004**: The access token MUST contain claims: `sub` (user_id), `tenant_id`, `role`, `jti` (unique token ID), `exp`, `iat`.
- **AUTH-005**: The refresh token MUST be stored in the database with columns: `id`, `user_id`, `token_hash` (SHA-256 of token), `family_id` (UUID), `expires_at`, `revoked_at`, `replaced_by_id`, `created_at`.
- **AUTH-006**: The system MUST hash passwords using bcrypt with a work factor of 12.
- **AUTH-007**: Login MUST return 401 with generic message "Invalid credentials" for both wrong email and wrong password (no enumeration).
- **AUTH-008**: The system MUST provide `POST /api/auth/refresh` that reads the refresh cookie and returns a new access token + new refresh cookie.
- **AUTH-009**: The system MUST provide `POST /api/auth/logout` that revokes the refresh token and blacklists the current access token.
- **AUTH-010**: The system MUST run bcrypt verification in a thread pool executor (`asyncio.to_thread`) to avoid blocking the event loop.

### 1.2 Token Blacklist

- **BL-001**: The system MUST maintain a token blacklist in Redis.
- **BL-002**: On logout, the access token's JTI MUST be added to Redis with TTL equal to the token's remaining lifetime.
- **BL-003**: On token refresh, the old access token's JTI MUST be blacklisted.
- **BL-004**: Every authenticated request MUST check the blacklist before processing.
- **BL-005**: If Redis is unreachable, the system MUST reject ALL token validations (fail-closed).
- **BL-006**: Redis key format MUST be `auth:blacklist:{jti}` with value `1`.
- **BL-007**: The blacklist check SHOULD complete within 5ms under normal conditions.

### 1.3 Token Rotation & Reuse Detection

- **ROT-001**: On refresh, the system MUST generate a new refresh token and invalidate the old one atomically.
- **ROT-002**: Each refresh token MUST belong to a `family_id` (UUID assigned at login).
- **ROT-003**: When a refresh token is used, its `replaced_by_id` MUST be set to the new token's ID.
- **ROT-004**: If a refresh token that has already been replaced is presented (reuse detection), the system MUST revoke ALL tokens in that family.
- **ROT-005**: Family revocation MUST set `revoked_at` on all tokens with the same `family_id`.
- **ROT-006**: After family revocation, the system MUST return 401 with body `{"detail": "Token reuse detected. All sessions revoked for security."}`.
- **ROT-007**: The refresh operation MUST use `SELECT ... FOR UPDATE` on the refresh token row to prevent race conditions.
- **ROT-008**: The system SHOULD allow a 5-second grace period for duplicate refresh requests with the same token (idempotency window).

### 1.4 RBAC

- **RBAC-001**: The system MUST implement RBAC using the Strategy Pattern.
- **RBAC-002**: The system MUST support these roles: `ADMIN`, `MANAGER`, `KITCHEN`, `WAITER`, `READONLY`.
- **RBAC-003**: Each role MUST map to a strategy class that implements `has_permission(permission: str) -> bool`.
- **RBAC-004**: The system MUST provide a `@require_role(*roles)` decorator for endpoint-level role checks.
- **RBAC-005**: The system MUST provide a `@require_permission(*permissions)` decorator for fine-grained permission checks.
- **RBAC-006**: `ADMIN` role MUST have all permissions (wildcard).
- **RBAC-007**: Permission denied MUST return 403 with body `{"detail": "Insufficient permissions"}`.
- **RBAC-008**: Missing/invalid token MUST return 401 with body `{"detail": "Not authenticated"}`.

#### Permission Matrix

| Permission | ADMIN | MANAGER | KITCHEN | WAITER | READONLY |
|-----------|-------|---------|---------|--------|----------|
| `users:read` | Y | Y | N | N | Y |
| `users:write` | Y | N | N | N | N |
| `users:manage` | Y | N | N | N | N |
| `menu:read` | Y | Y | Y | Y | Y |
| `menu:write` | Y | Y | N | N | N |
| `menu:manage` | Y | Y | N | N | N |
| `orders:read` | Y | Y | Y | Y | Y |
| `orders:write` | Y | Y | N | Y | N |
| `orders:manage` | Y | Y | N | N | N |
| `kitchen:read` | Y | Y | Y | N | Y |
| `kitchen:write` | Y | Y | Y | N | N |
| `reports:read` | Y | Y | N | N | Y |
| `reports:manage` | Y | N | N | N | N |
| `settings:read` | Y | Y | N | N | Y |
| `settings:write` | Y | N | N | N | N |
| `tenants:manage` | Y | N | N | N | N |
| `tables:read` | Y | Y | N | Y | Y |
| `tables:write` | Y | Y | N | N | N |
| `table_sessions:create` | Y | Y | N | Y | N |

### 1.5 Multi-tenant Isolation

- **MT-001**: The system MUST extract `tenant_id` from the JWT on every authenticated request.
- **MT-002**: The `tenant_id` MUST be stored in a Python `contextvars.ContextVar` for the duration of the request.
- **MT-003**: All tenant-scoped SQLAlchemy models MUST include a `tenant_id` column (FK to tenants table).
- **MT-004**: The system MUST auto-filter queries on tenant-scoped models by `tenant_id` using a SQLAlchemy event listener on `do_orm_execute`.
- **MT-005**: The repository layer MUST also explicitly filter by `tenant_id` as defense in depth.
- **MT-006**: A request with a JWT containing `tenant_id=X` MUST NEVER be able to read, write, or modify data belonging to `tenant_id=Y`.
- **MT-007**: The `ADMIN` role MAY access cross-tenant data only through explicitly designated super-admin endpoints (not in Sprint 2 scope).
- **MT-008**: The tenant context MUST be set BEFORE any DB operation in the request lifecycle.

### 1.6 Rate Limiting & Brute Force

- **RL-001**: The login endpoint MUST enforce a rate limit of 5 requests per minute per (IP + email) combination.
- **RL-002**: Rate limiting MUST use a Redis sliding window counter.
- **RL-003**: Rate-limited requests MUST return 429 with `Retry-After` header (seconds).
- **RL-004**: Redis key format: `auth:ratelimit:{ip}:{email_hash}` with 60s TTL.
- **BF-001**: The system MUST track consecutive failed login attempts per email.
- **BF-002**: After 5 consecutive failures: lock account for 1 minute.
- **BF-003**: After 10 consecutive failures: lock account for 5 minutes.
- **BF-004**: After 15 consecutive failures: lock account for 15 minutes.
- **BF-005**: Successful login MUST reset the failure counter to 0.
- **BF-006**: Lockout status MUST be checked BEFORE password verification (avoid CPU waste on bcrypt).
- **BF-007**: Redis key format: `auth:lockout:{email_hash}` (JSON: `{count, locked_until}`).
- **BF-008**: Locked account login attempt MUST return 429 with body `{"detail": "Account temporarily locked", "retry_after": <seconds>}`.

### 1.7 Table Tokens (HMAC)

- **TT-001**: The system MUST provide `POST /api/sessions/table-token` to generate table session tokens.
- **TT-002**: Only users with `table_sessions:create` permission MAY generate table tokens.
- **TT-003**: Table tokens MUST be HMAC-SHA256 signed with a server secret.
- **TT-004**: Token payload MUST include: `table_id`, `tenant_id`, `session_id` (UUID), `exp` (3h from creation).
- **TT-005**: Table tokens MUST be validated by signature verification only (no DB lookup).
- **TT-006**: Expired table tokens MUST be rejected with 401.
- **TT-007**: Table tokens MUST NOT grant access to any endpoint outside the table session scope.
- **TT-008**: The system SHOULD support multiple active HMAC secrets for rotation (verify against all, sign with newest).

## 2. Scenarios (Given/When/Then)

### 2.1 Login Scenarios

```
SCENARIO: Successful login
  GIVEN a user with email "chef@buensabor.com" and valid password exists
  AND the user belongs to tenant_id=1 with role=KITCHEN
  AND the account is not locked
  WHEN POST /api/auth/login with {"email": "chef@buensabor.com", "password": "ValidPass123!"}
  THEN response status is 200
  AND response body contains {"access_token": "<jwt>", "token_type": "bearer", "expires_in": 900}
  AND response sets cookie "refresh_token" with HttpOnly, Secure, SameSite=Lax, Path=/api/auth, Max-Age=604800
  AND the JWT contains claims {sub: <user_id>, tenant_id: 1, role: "KITCHEN", jti: <uuid>}
  AND a refresh token is stored in DB with family_id=<new_uuid>
  AND failed login counter for this email is reset to 0

SCENARIO: Login with invalid password
  GIVEN a user with email "chef@buensabor.com" exists
  WHEN POST /api/auth/login with {"email": "chef@buensabor.com", "password": "WrongPass"}
  THEN response status is 401
  AND response body is {"detail": "Invalid credentials"}
  AND failed login counter is incremented by 1
  AND NO tokens are issued

SCENARIO: Login with locked account
  GIVEN user "chef@buensabor.com" has 5 consecutive failed attempts
  AND lockout is active (locked_until > now)
  WHEN POST /api/auth/login with correct credentials
  THEN response status is 429
  AND response body contains {"detail": "Account temporarily locked", "retry_after": <seconds>}
  AND password is NOT checked (save CPU)
```

### 2.2 Token Refresh Scenarios

```
SCENARIO: Successful token refresh
  GIVEN user has a valid refresh token in cookie
  AND the refresh token exists in DB and is not revoked
  WHEN POST /api/auth/refresh
  THEN response status is 200
  AND response body contains new access_token
  AND response sets new refresh_token cookie
  AND old refresh token's replaced_by_id is set to new token's ID
  AND old access token's JTI is blacklisted in Redis
  AND new refresh token has same family_id as old one

SCENARIO: Refresh with revoked token (reuse detection)
  GIVEN refresh token T1 was already used to get T2 (T1.replaced_by_id = T2.id)
  WHEN POST /api/auth/refresh with T1 (reuse attempt)
  THEN response status is 401
  AND response body is {"detail": "Token reuse detected. All sessions revoked for security."}
  AND ALL tokens in the same family_id are revoked (T1, T2, and any descendants)
```

### 2.3 RBAC Scenarios

```
SCENARIO: Kitchen user tries to manage menu
  GIVEN user with role=KITCHEN is authenticated
  WHEN accessing an endpoint decorated with @require_permission("menu:write")
  THEN response status is 403
  AND response body is {"detail": "Insufficient permissions"}

SCENARIO: Admin accesses any endpoint
  GIVEN user with role=ADMIN is authenticated
  WHEN accessing any @require_permission decorated endpoint
  THEN access is granted (ADMIN has wildcard permissions)
```

### 2.4 Multi-tenant Scenarios

```
SCENARIO: Tenant isolation on read
  GIVEN tenant 1 has 5 orders and tenant 2 has 3 orders
  AND user belongs to tenant 1
  WHEN GET /api/orders
  THEN only tenant 1's 5 orders are returned
  AND tenant 2's orders are NEVER visible
```

### 2.5 Redis Failure Scenarios

```
SCENARIO: Redis down during token validation
  GIVEN Redis is unreachable
  WHEN any authenticated request arrives
  THEN blacklist check fails
  AND request is REJECTED (fail-closed)
  AND response status is 503
  AND response body is {"detail": "Authentication service temporarily unavailable"}
```

## 3. API Contracts

### 3.1 POST /api/auth/login

**Request Schema (Pydantic):**
```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Juan Perez",
    "role": "MANAGER",
    "tenant_id": 1
  }
}
```
**Headers Set:** `Set-Cookie: refresh_token=<token>; HttpOnly; Secure; SameSite=Lax; Path=/api/auth; Max-Age=604800`

**Error Responses:**
- `401`: `{"detail": "Invalid credentials"}`
- `422`: Pydantic validation error
- `429`: `{"detail": "Account temporarily locked", "retry_after": 60}` or `{"detail": "Too many login attempts"}` with `Retry-After` header
- `503`: `{"detail": "Authentication service temporarily unavailable"}` (Redis down)

### 3.2 POST /api/auth/refresh

**Success Response (200):** New access token + new refresh cookie.
**Error Responses:** 401 (expired, revoked, or missing), 503 (Redis down)

### 3.3 POST /api/auth/logout

**Success Response (200):** `{"detail": "Logged out successfully"}`
**Headers Set:** `Set-Cookie: refresh_token=; HttpOnly; Secure; SameSite=Lax; Path=/api/auth; Max-Age=0`

### 3.4 POST /api/sessions/table-token

**Request Schema:**
```python
class TableTokenRequest(BaseModel):
    table_id: int = Field(gt=0)
```

**Success Response (201):**
```json
{
  "token": "<hmac_signed_token>",
  "table_id": 5,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "expires_in": 10800,
  "expires_at": "2026-03-19T23:00:00Z"
}
```

## 4. Security Requirements

- **SEC-001**: All passwords MUST be hashed with bcrypt (work factor 12). Plaintext passwords MUST NEVER be stored or logged.
- **SEC-002**: JWT signing key MUST be at least 256 bits, loaded from environment variable `JWT_SECRET_KEY`.
- **SEC-003**: HMAC signing key MUST be separate from JWT key, loaded from `TABLE_TOKEN_SECRET_KEY`.
- **SEC-004**: Refresh tokens stored in DB MUST be hashed (SHA-256). The raw token is only in the cookie.
- **SEC-005**: Login endpoint MUST NOT reveal whether an email exists (constant-time comparison, similar response times).
- **SEC-009**: All security events (login, logout, failed login, token reuse, lockout) MUST be logged with structured logging (JSON) including IP, email, tenant_id, timestamp.

## 5. Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| Access token used after logout | Rejected (JTI in blacklist) |
| Refresh token used after logout | Rejected (revoked_at set in DB) |
| User deleted while token active | Next request fails at user lookup (401) |
| User role changed while token active | Old token keeps old role until expiry (15min max). New role reflected on next login/refresh. |
| Clock skew between servers | JWT `exp` validation SHOULD allow 30s leeway |
| Concurrent logins from different devices | Each creates separate token family. All families valid simultaneously. |
| JWT algorithm confusion attack | Explicitly set `algorithms=["HS256"]` in decode. Never accept `none`. |
