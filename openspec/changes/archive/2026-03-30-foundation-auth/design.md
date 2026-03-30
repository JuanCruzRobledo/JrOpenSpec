---
change: foundation-auth
phase: 2
artifact: design
source: reconciled-architecture
date: 2026-03-30
status: approved
---

# Design: Foundation Auth

## Technical Approach

Converge auth onto the current backend shape (`rest_api/app/*`, `shared/shared/*`) instead of the older proposal structure. Staff auth uses JWT access tokens plus DB-backed refresh rotation; diner auth uses the existing HMAC table token primitive. Authorization is centered on `PermissionContext` + role strategies + branch-scoped checks, with repositories/services enforcing tenant boundaries explicitly. Login may stay lightweight (`POST /auth/login` returns tokens), while `GET /auth/me` remains the canonical profile fetch.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| JWT claim model | Access JWT keeps `sub`, `tenant_id`, `branch_ids`, `roles`, `jti`, `iat`, `exp` | Legacy singular `role`; permission-string-only JWT | Matches current code (`jwt.py`, `auth_service.py`) and supports multi-branch staff without re-login. |
| Authorization model | `PermissionContext` + strategy objects + `require_branch_access()` are primary; decorators are thin adapters only | Primary `@require_permission("x:y")` model | Aligns with knowledge docs and thin-router pattern; branch scope stays explicit instead of hidden in opaque strings. |
| Tenant isolation | Enforce `tenant_id` in services/repositories and branch-scoped queries; no global ORM auto-filter as primary control | SQLAlchemy global interceptor/contextvar magic | Defense in depth is auditable and easier to verify with tests; avoids invisible query mutation. |
| Login/profile split | `login` issues tokens; `me` returns enriched profile | Heavy login returning full branch/role profile always | Keeps auth path fast and lets frontends refresh profile intentionally. |
| Diner session primitive | Public `/api/sessions/join` remains the source of HMAC table tokens; later flows reuse the same token contract | Separate staff-generated diner token format | Preserves one diner auth primitive across REST and WebSocket. |

## Data Flow

### Staff login / profile

```text
Client -> /api/auth/login -> AuthService
  -> User + UserBranchRole lookup
  -> bcrypt verify + rate-limit/lockout checks
  -> access JWT(sub, tenant_id, branch_ids, roles[])
  -> refresh token family persisted
Client -> /api/auth/me -> PermissionContext-ready profile
```

### Refresh rotation / reuse detection

```text
Client -> /api/auth/refresh(cookie)
  -> lock refresh row
  -> if replaced/revoked: revoke whole family, deny
  -> create successor token, set replaced_by_id, revoke current
  -> issue new access JWT + refresh cookie
```

### Public diner entry

```text
Client -> /api/sessions/join(branch_slug, table_identifier)
  -> SessionService resolves branch + table
  -> HMAC table token(branch_id, table_id, session_id, exp)
  -> token reused by pwaMenu and later ws diner flows
```

## File Changes

| File | Action | Description |
|---|---|---|
| `openspec/changes/foundation-auth/design.md` | Modify | Reconciled design source of truth. |
| `shared/shared/security/jwt.py` | Modify | Remove legacy singular-role assumptions; keep canonical claims and validation rules. |
| `rest_api/app/services/auth_service.py` | Modify | Converge login/profile split, strict refresh rotation, reuse detection, and rate-limit behavior. |
| `shared/shared/models/core/refresh_token.py` | Modify | Add/confirm `replaced_by_id` chain support for family rotation. |
| `rest_api/app/routers/auth/routes.py` | Modify | Keep routers thin; use dependencies/context, not inline token logic. |
| `rest_api/app/services/permissions/*` | Create/Modify | Centralize `PermissionContext`, role strategies, and branch-scoped authorization adapters. |
| `shared/shared/repositories/*` | Modify | Make tenant/branch filters explicit in auth-adjacent reads and writes. |

## Interfaces / Contracts

```python
AccessTokenClaims = {
  "sub": str,
  "tenant_id": int,
  "branch_ids": list[int],
  "roles": list[str],
  "jti": str,
  "iat": int,
  "exp": int,
}

PermissionContext(user).require_branch_access(branch_id)
PermissionContext(user).can(action, resource, branch_id=branch_id)
```

Refresh persistence contract:

```text
refresh_token(id, user_id, family_id, token_hash, expires_at, revoked_at, replaced_by_id)
```

Table-token contract stays:

```text
{ branch_id, table_id, session_id, exp, iat } + HMAC-SHA256 signature
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | JWT claims, strategy checks, HMAC validation, lockout thresholds | Deterministic service/security tests. |
| Integration | Login, `/me`, refresh rotation, reuse detection, logout blacklist, cross-tenant denial | FastAPI + DB + Redis tests with real persistence behavior. |
| E2E | Dashboard/pwaWaiter login bootstrap; diner join-session -> token -> public access | Verify contracts used by later phases. |

## Migration / Rollout

Schema convergence is required for `refresh_tokens.replaced_by_id` and any missing audit/index support. Rollout order: schema first, service convergence second, router/dependency cleanup third. No feature flag is preferred; verification should prove parity before archive.

## Open Questions

- [ ] Should `roles[]` remain raw strings from `UserBranchRole` or be normalized to the canonical role enum during token issuance?
- [ ] Do we need a dedicated authenticated dependency returning `PermissionContext` so `/auth/logout` and `/auth/me` stop parsing JWT inline?
