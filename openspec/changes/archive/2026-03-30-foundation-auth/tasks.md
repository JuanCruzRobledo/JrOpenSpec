---
change: foundation-auth
phase: 2
artifact: tasks
source: reconciliation-g2-2026-03-30
date: 2026-03-30
status: ready-for-verify
---

# Tasks: foundation-auth

## Phase 1: Baseline already implemented

- [x] 1.1 Backend auth surface exists in `rest_api/app/routers/auth/routes.py`, `rest_api/app/services/auth_service.py`, `shared/shared/security/jwt.py`, and `shared/shared/models/core/refresh_token.py`.
- [x] 1.2 Branch-scoped JWT/RBAC contract is already adopted in `rest_api/app/services/permissions/{context.py,strategies.py}`, `rest_api/app/dependencies/__init__.py`, and `dashboard/src/{types/auth.ts,services/auth.service.ts,stores/auth.store.ts}`.
- [x] 1.3 Table-session HMAC flow exists in `shared/shared/security/table_tokens.py`, `rest_api/app/routers/public/session_router.py`, and related schemas/tests.

## Phase 2: Security-critical backend gaps before verify

- [x] 2.1 Harden refresh rotation in `rest_api/app/services/auth_service.py`, `shared/shared/models/core/refresh_token.py`, and `alembic/versions/002_add_refresh_tokens.py`: use row locking, persist `replaced_by_id`, preserve family lineage, and return the spec’d reuse-detection error.
- [x] 2.2 Align blacklist/revocation semantics across `shared/shared/security/blacklist.py`, `shared/shared/security/jwt.py`, `rest_api/app/services/auth_service.py`, and `rest_api/app/routers/auth/routes.py`: blacklist prior access token on refresh, keep logout deterministic, and document fail-closed behavior.
- [x] 2.3 Replace the current split brute-force/rate-limit behavior in `rest_api/app/middleware/rate_limit.py`, `shared/shared/security/brute_force.py`, `rest_api/app/services/auth_service.py`, and `rest_api/app/routers/auth/routes.py` with one explicit contract: Redis sliding window per IP+email, progressive lockout, `Retry-After`, and stable 429 bodies.

## Phase 3: Reconciliation and artifact/code alignment

- [x] 3.1 `openspec/changes/foundation-auth/proposal.md` now matches the reconciled model: JWT claims use `tenant_id` + `branch_ids` + `roles[]`, auth centers on `PermissionContext`, and tenant scoping is explicit rather than magical middleware/query interception.
- [x] 3.2 `openspec/changes/foundation-auth/spec.md` and `design.md` already reflect the reconciled branch-scoped auth contract; keep them as the current source of truth.
- [x] 3.3 Table-token artifact wording is already aligned in `openspec/changes/foundation-auth/{spec.md,design.md}` with `shared/shared/security/table_tokens.py` and `rest_api/app/routers/public/session_router.py`.

## Phase 4: Verify-readiness tests and evidence

- [x] 4.1 Rewrite `tests/test_auth.py` around real Phase 2 behavior: login success/failure, refresh rotation lineage, replay detection, logout blacklist, and Redis-failure handling.
- [x] 4.2 Update `tests/test_rbac.py` to assert the real branch-scoped `PermissionContext` contract and remove placeholders that still assume the older Sprint 2 permission matrix.
- [x] 4.3 Update `tests/test_table_tokens.py` and any auth-adjacent coverage to match the reconciled payload/error contracts, then add an explicit regression for the rate-limit/brute-force rules.
- [x] 4.4 Run the reconciled auth test slice in a reproducible backend env (`pytest` + app deps installed) and capture passing evidence in `verify-report.md` so verify/archive can proceed on executed, not only structural, proof.

## Implementation Order

- Critical path: `4.1/4.2/4.3 -> 4.4`
- Focused auth verify evidence is now executable; broader verify can proceed from the captured report.
