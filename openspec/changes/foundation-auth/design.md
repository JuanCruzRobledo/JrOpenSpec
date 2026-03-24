---
change: foundation-auth
phase: 2
artifact: design
source: sdd-otro/sprint-2-auth
date: 2026-03-23
status: approved
---

# SDD Design: Sprint 2 — Autenticación y Multi-tenancy

## 1. Auth Flow Sequence Diagrams

### 1.1 Login Flow

```
Client              FastAPI Router       AuthService         UserRepo        TokenService       Redis         DB
  |                      |                   |                  |                |               |             |
  |-- POST /login ------>|                   |                  |                |               |             |
  |                      |-- check_rate_limit(ip, email) -------|--------------->|               |             |
  |                      |-- check_lockout(email) --------------|--------------->|               |             |
  |                      |-- authenticate(email, password) ---->|                |               |             |
  |                      |                   |-- get_by_email ->|                |               |             |
  |                      |                   |-- verify_password (asyncio.to_thread(bcrypt.check)) |           |
  |                      |                   |-- [IF FAIL] increment_failures --|--------------->|             |
  |                      |-- create_tokens(user) ---------------|--------------->|               |             |
  |                      |                   |                  |                |-- gen JWT -----|             |
  |                      |                   |                  |                |-- gen refresh -|             |
  |                      |                   |                  |                |-- store hash --|------------>|
  |                      |                   |                  |                |-- reset fails->|             |
  |                      |<-- {access_token, refresh_cookie} ---|----------------|               |             |
  |<-- 200 + Set-Cookie--|                   |                  |                |               |             |
```

## 2. Token Lifecycle

```
LOGIN:
  access_token (JWT, 15min)  ──────────────── expires naturally
  refresh_token (DB, 7d)     ──────────────── used at refresh

REFRESH (at ~14min):
  old_access   -> BLACKLISTED in Redis (TTL = remaining ~1min)
  old_refresh  -> replaced_by_id set (soft invalidated)
  new_access   -> issued (15min)
  new_refresh  -> issued (7d), same family_id

LOGOUT:
  access_token  -> JTI blacklisted in Redis (TTL = remaining lifetime)
  refresh_token -> revoked_at set in DB
  cookie        -> cleared (Max-Age=0)

REUSE DETECTION:
  old_refresh (already replaced) -> presented again
  ALL tokens in family_id        -> revoked_at set
  User must re-login
```

### Token Family Tree Example
```
Login:     T1 (family=F1) ─────────────────────────────────
Refresh 1: T1.replaced_by=T2, T2 (family=F1) ─────────────
Refresh 2: T2.replaced_by=T3, T3 (family=F1) ─────────────
Reuse T1:  T1,T2,T3 ALL revoked (family=F1 compromised) ──
```

## 3. RBAC Strategy Pattern -- Class Hierarchy

```
class Role(StrEnum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    KITCHEN = "KITCHEN"
    WAITER = "WAITER"
    READONLY = "READONLY"

class PermissionStrategy(ABC):
    @abstractmethod
    def has_permission(self, permission: str) -> bool: ...

class AdminStrategy(PermissionStrategy):
    def has_permission(self, permission: str) -> bool:
        return True  # Wildcard

class ManagerStrategy(PermissionStrategy):
    PERMISSIONS = {
        "users:read", "menu:read", "menu:write", "menu:manage",
        "orders:read", "orders:write", "orders:manage",
        "kitchen:read", "kitchen:write", "reports:read",
        "settings:read", "tables:read", "tables:write",
        "table_sessions:create",
    }

class StrategyFactory:
    @classmethod
    def create(cls, role: Role) -> PermissionStrategy:
        ...

# FastAPI-idiomatic (PREFERRED):
class PermissionChecker:
    def __init__(self, *permissions: str):
        self.permissions = permissions

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        context = PermissionContext.from_user(current_user)
        for perm in self.permissions:
            if not context.check_permission(perm):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

# Usage in router:
@router.get("/orders")
async def list_orders(user: User = Depends(PermissionChecker("orders:read"))):
    ...
```

## 4. Multi-tenant Middleware Flow

```
Request
  |
  v
+──────────────────────────────+
|  TenantMiddleware            |
|  (Starlette BaseHTTPMiddleware) |
+──────────────────────────────+
| 1. Skip if path in PUBLIC_PATHS |
|    (/api/auth/login, /health)|
| 2. Extract JWT from header   |
| 3. Decode -> get tenant_id   |
| 4. Set contextvars:          |
|    tenant_context.set(tid)   |
| 5. call_next(request)        |
| 6. Reset context on exit     |
+──────────────┬───────────────+
               |
               v
+──────────────────────────────+
|  SQLAlchemy Event Listener   |
|  (do_orm_execute)            |
+──────────────────────────────+
| On SELECT/UPDATE/DELETE:     |
| 1. Get tenant_id from        |
|    contextvars               |
| 2. If model has tenant_id:   |
|    append WHERE tenant_id=X  |
+──────────────────────────────+
```

### Context Variable Setup

```python
# shared/middleware/tenant.py
import contextvars

tenant_context: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "tenant_context", default=None
)

def get_current_tenant_id() -> int:
    tid = tenant_context.get()
    if tid is None:
        raise RuntimeError("Tenant context not set")
    return tid
```

## 5. Redis Key Structure

### 5.1 Token Blacklist
```
Key:    auth:blacklist:{jti}
Value:  "1"
TTL:    remaining token lifetime (max 900s for access tokens)
Type:   STRING
```

### 5.2 Rate Limiting (Sliding Window)
```
Key:    auth:ratelimit:{ip}:{sha256(email)[:16]}
Value:  sorted set of timestamps (ZSET)
TTL:    60s (auto-cleanup)
```

### 5.3 Brute Force Lockout
```
Key:    auth:lockout:{sha256(email)[:16]}
Value:  JSON: { "count": 7, "locked_until": "2026-03-19T15:30:00Z" }
TTL:    max lockout duration + buffer = 20min
```

## 6. Database Schema

### 6.1 Refresh Tokens Table
```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hex
    family_id UUID NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    replaced_by_id INTEGER REFERENCES refresh_tokens(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash) WHERE revoked_at IS NULL;
CREATE INDEX idx_refresh_tokens_family ON refresh_tokens(family_id);
```

## 7. File Structure

```
shared/
+-- security/
|   +-- password.py                # bcrypt hash/verify (async-safe)
|   +-- jwt.py                     # JWT encode/decode
|   +-- hmac_token.py              # HMAC table token sign/verify
|   +-- rbac/
|       +-- roles.py               # Role enum
|       +-- strategy.py            # ABC + all 5 strategies
|       +-- context.py             # PermissionContext
|       +-- factory.py             # StrategyFactory
|       +-- decorators.py          # @require_role, @require_permission, PermissionChecker
+-- services/
|   +-- auth_service.py            # Login, refresh, logout orchestration
|   +-- token_service.py           # Token creation, validation, blacklist, rotation
+-- repositories/
|   +-- user_repository.py         # UserRepository
|   +-- token_repository.py        # RefreshTokenRepository
+-- middleware/
|   +-- auth.py                    # Auth middleware (JWT validation + blacklist check)
|   +-- tenant.py                  # Tenant middleware (contextvars)
+-- redis/
|   +-- client.py                  # Redis connection pool + health check
|   +-- blacklist.py               # Token blacklist operations
|   +-- rate_limiter.py            # Sliding window rate limit + lockout

rest_api/
+-- routers/
|   +-- auth.py                    # /api/auth/* endpoints
|   +-- sessions.py                # /api/sessions/table-token
+-- dependencies/
|   +-- auth.py                    # get_current_user, get_current_tenant
+-- schemas/
    +-- auth.py                    # LoginRequest, TokenResponse, etc.
```

## 8. Security Considerations

### 8.1 Timing Attack Prevention
- Login with non-existent email MUST still run a dummy bcrypt hash to normalize response time
- Use `secrets.compare_digest()` for all token comparisons

### 8.2 JWT Best Practices
- Algorithm explicitly set to `HS256` in both encode and decode (prevent algorithm confusion)
- `algorithms` parameter in decode is a LIST containing ONLY `HS256`
- Never accept `alg: none`
- Include `iss` (issuer) claim: `"buensabor"`
- Include `aud` (audience) claim: `"buensabor-api"`

### 8.3 Cookie Security
- `HttpOnly=True` (no JS access)
- `Secure=True` (HTTPS only -- in production)
- `SameSite=Lax` (CSRF protection while allowing top-level navigation)
- `Path=/api/auth` (only sent to auth endpoints)

### 8.4 Environment Variables Required

```env
# JWT
JWT_SECRET_KEY=<min 256-bit random>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# HMAC Table Tokens
TABLE_TOKEN_SECRET_KEY=<separate 256-bit random>
TABLE_TOKEN_EXPIRE_HOURS=3

# Bcrypt
BCRYPT_WORK_FACTOR=12

# Rate Limiting
LOGIN_RATE_LIMIT_PER_MINUTE=5
LOGIN_LOCKOUT_THRESHOLDS=5:60,10:300,15:900

# Auth Feature Flag
AUTH_ENABLED=true
```
