---
change: foundation-auth
phase: 2
artifact: verify-report
date: 2026-03-30
status: completed
verdict: PASS
mode: Standard
---

# Verification Report: foundation-auth

**Change**: foundation-auth
**Phase**: 2
**Mode**: Standard (TDD strict: false)
**Date**: 2026-03-30

---

## Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 12 |
| Tasks complete | 12 |
| Tasks incomplete | 0 |

All 4 phases (Baseline, Security-critical gaps, Reconciliation, Verify-readiness) fully checked.

---

## Build & Tests Execution

**Build**: ➖ Not configured (`build_command: ""` in openspec/config.yaml)

**Tests**: ✅ 41 passed / ❌ 0 failed / ⚠️ 0 skipped

```
============================= test session results =============================
platform win32 -- Python 3.13.12, pytest-8.4.2, pluggy-1.6.0
rootdir: G:\Proyectos\JrOpenSpec
configfile: pytest.ini
plugins: anyio-4.13.0, asyncio-1.3.0
collected 41 items

tests\test_auth.py ..........                                            [ 24%]
tests\test_rbac.py ..............                                        [ 58%]
tests\test_table_tokens.py ..............                                [ 92%]
tests\test_session_service.py ...                                        [100%]

============================= 41 passed in 16.01s =============================
```

**Slice**: `tests/test_auth.py`, `tests/test_rbac.py`, `tests/test_table_tokens.py`, `tests/test_session_service.py`
**Environment**: Python 3.13.12 · pytest 8.4.2 · Docker PostgreSQL (`pgvector/pgvector:0.8.0-pg16`) · Redis mocked via FakeRedis

**Coverage**: ➖ Not available (no coverage tool configured)

---

## Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| REQ-1: Branch-scoped authentication | Login builds branch-scoped claims | `test_auth.py > test_login_route_returns_token_cookie_and_me_profile` | ✅ COMPLIANT |
| REQ-2: Roles derive from UserBranchRole | Branch access denied outside assignments | `test_rbac.py > test_branch_access_denied` | ✅ COMPLIANT |
| REQ-3: Login and profile contract | Minimal login response remains valid | `test_auth.py > test_login_route_returns_token_cookie_and_me_profile` | ✅ COMPLIANT |
| REQ-4: Refresh rotation + reuse detection | Reuse revokes entire family | `test_auth.py > test_refresh_reuse_revokes_entire_family` | ✅ COMPLIANT |
| REQ-5: Login abuse protection | Repeated failures trigger 429 | `test_auth.py > test_login_returns_stable_429_body_and_retry_after` | ✅ COMPLIANT |
| REQ-6: RBAC via PermissionContext | Highest-privilege role selected | `test_rbac.py > test_highest_privilege_strategy_selected` | ✅ COMPLIANT |
| REQ-7: Tenant scoping is explicit | Service query stays tenant-scoped | `test_auth.py > TestTenantScopingExplicit::test_me_returns_only_own_tenant_data` | ✅ COMPLIANT |
| REQ-8: Redis-backed auth state | Revoked token denied | `test_auth.py > TestBlacklistedTokenDenied::test_blacklisted_token_rejected_by_me` | ✅ COMPLIANT |
| REQ-9: Table session credentials | Public join issues canonical credential | `test_session_service.py > TestSessionJoinHTTP::test_join_issues_table_token_with_correct_shape` | ✅ COMPLIANT |

**Compliance summary**: 9/9 scenarios compliant · 0 partial · 0 untested · 0 failing

---

## Correctness (Static — Structural Evidence)

| Requirement | Status | Notes |
|-------------|--------|-------|
| JWT claim shape: `sub`, `tenant_id`, `branch_ids`, `roles`, `jti`, `iat`, `exp` | ✅ Implemented | Confirmed in `auth_service.py:create_access_token` calls and `/me` response in test |
| Refresh token persisted with `replaced_by_id`, `family_id` | ✅ Implemented | `test_refresh_rotation_persists_lineage_and_blacklists_prior_access` proves DB state |
| `PermissionContext` + strategy pattern + `can()` | ✅ Implemented | `permissions/context.py` + `strategies.py` confirmed via test_rbac.py |
| HttpOnly cookie at `Path=/api/auth` | ✅ Implemented | `routes.py:_set_refresh_cookie` + test asserts both `HttpOnly` and `Path=/api/auth` |
| Rate limiting: sliding window, progressive lockout, `Retry-After` | ✅ Implemented | `test_login_returns_stable_429_body_and_retry_after` proves full contract |
| HMAC table token payload: `branch_id`, `table_id`, `session_id`, `exp`, `iat` | ✅ Implemented | `test_payload_contains_required_fields` proves exact key set |
| Table token scope isolation from staff JWT | ✅ Implemented | `test_join_issues_table_token_with_correct_shape` + `test_payload_does_not_include_staff_jwt_claims` |
| Tenant scoping explicit in services | ✅ Implemented | `test_me_returns_only_own_tenant_data` proves no cross-tenant leakage via /me |

---

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| JWT claim model: `tenant_id` + `branch_ids` + `roles[]` | ✅ Yes | `auth_service.py:login` passes all claims to `create_access_token` |
| Authorization via `PermissionContext` strategy pattern | ✅ Yes | `context.py` + strategies fully implemented and tested |
| Login/profile split: `login` → tokens, `me` → enriched profile | ✅ Yes | Routes exactly match design; `/me` fetches `UserBranchRole` dynamically |
| Tenant isolation via explicit service-level filtering | ✅ Yes | `test_me_returns_only_own_tenant_data` confirms cross-tenant isolation |
| Diner session: HMAC table token via `SessionService.join_session` | ✅ Yes | `test_join_issues_table_token_with_correct_shape` confirms full HTTP flow |
| Router thin: `Depends` + service call only | ✅ Yes | `routes.py` contains zero business logic inline |

---

## Issues Found

**CRITICAL** (must fix before archive):
None

**WARNING** (should fix):
None

**SUGGESTION** (nice to have):
- Resolve open design question: should `roles[]` remain raw strings from `UserBranchRole` or be normalized to the canonical role enum during token issuance?

---

## Verdict

**PASS**

Foundation-auth fully verified. 41/41 tests pass on real PostgreSQL. All 12 tasks complete. All 9 spec scenarios compliant with executed evidence. All design decisions followed. Ready for archive.
