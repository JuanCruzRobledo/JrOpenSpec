---
change: foundation-auth
phase: 2
artifact: spec
source: reconciliation-approved
date: 2026-03-30
status: approved
---

# SDD Spec: Foundation Auth — Reconciled Source of Truth

## Purpose

Define the canonical auth contract for verification. This spec reconciles the approved architecture with current implementation reality while keeping unresolved security controls as REQUIRED future behavior.

## Requirements

### Requirement: Branch-scoped authentication context

The system MUST authenticate staff with JWT access tokens and refresh tokens. Access tokens MUST carry `sub`, `tenant_id`, `branch_ids`, `roles`, `jti`, `exp`, and `iat`. A single `user.role` claim MUST NOT be the authoritative source for authorization.

#### Scenario: Login builds branch-scoped claims
- GIVEN an active user has active `UserBranchRole` assignments in one or more branches
- WHEN login succeeds
- THEN the JWT contains that user's `branch_ids` and `roles[]`
- AND the refresh token is delivered via HttpOnly auth cookie

### Requirement: Roles derive from UserBranchRole

The system MUST model staff authorization through active `UserBranchRole` assignments. Branch scope is a first-class concern: permissions and branch access MUST be evaluated against assigned branches, not only tenant membership.

#### Scenario: Branch access is denied outside assignments
- GIVEN a valid JWT with `branch_ids=[1,2]`
- WHEN the user requests access to branch `3`
- THEN authorization is denied even if `tenant_id` matches

### Requirement: Login and profile contract

`POST /api/auth/login` MUST accept `email` and `password`. On success it MUST return at least `access_token` and `token_type`, and MUST set the refresh token cookie. Implementations MAY also return expiry metadata or user profile fields, but branch-scoped user context MUST be available through the auth surface, including `/api/auth/me`.

#### Scenario: Minimal login response remains valid
- GIVEN valid credentials
- WHEN login succeeds
- THEN the response body includes `access_token` and `token_type`
- AND the authenticated user context exposes `tenant_id`, `branch_ids`, and `roles[]`

### Requirement: Refresh rotation and reuse detection

Refresh tokens MUST support rotation, token families, and reuse detection. Reusing a rotated or revoked refresh token MUST revoke the entire family and deny the request. Verification for this change MUST continue to treat this requirement as security-critical even if implementation gaps remain.

#### Scenario: Reuse revokes the family
- GIVEN refresh token `T1` was exchanged for `T2` in the same family
- WHEN `T1` is presented again
- THEN the request is rejected
- AND all active tokens in that family are revoked

### Requirement: Login abuse protection

The login flow MUST enforce both request rate limiting and brute-force protection. At minimum, repeated failed attempts MUST trigger temporary denial before password verification can be abused indefinitely. Verification for this change MUST continue to treat this requirement as security-critical even if implementation gaps remain.

#### Scenario: Repeated failures trigger denial
- GIVEN repeated login attempts exceed configured thresholds
- WHEN another login attempt arrives
- THEN the request is denied with 429 semantics
- AND the denial includes enough retry information for clients or operators

### Requirement: RBAC uses PermissionContext with action-resource checks

The system MUST expose a `PermissionContext`-style authorization façade derived from JWT claims. Action-resource checks (`create/read/edit/delete/manage` over named resources) MUST be the canonical RBAC model. Simpler role guards MAY coexist, but they MUST remain compatible with the same branch-scoped auth context.

#### Scenario: Highest-privilege assigned role is used
- GIVEN a user JWT contains multiple roles
- WHEN authorization is evaluated through `PermissionContext`
- THEN the effective strategy is selected from those assigned roles
- AND branch restrictions still apply

### Requirement: Tenant scoping is explicit

Tenant isolation MUST be enforced explicitly in services and repositories using request auth context (`tenant_id`, and when relevant `branch_id`/`branch_ids`). Magical global query interception MAY exist as defense in depth, but it MUST NOT be the only isolation mechanism relied upon by verification.

#### Scenario: Service query stays tenant-scoped
- GIVEN a request authenticated for tenant `A`
- WHEN a service or repository loads tenant-owned data
- THEN the query explicitly constrains results to tenant `A`

### Requirement: Redis-backed auth state semantics

Blacklist and login-protection state MUST live in Redis with stable namespaces and TTL semantics. Implementations MAY use compact keys such as `blacklist:{jti}` / `login_attempts:{email}` or auth-prefixed keys such as `auth:blacklist:{jti}` / `auth:lockout:{email_hash}`, but the meaning of each keyspace MUST remain unambiguous.

#### Scenario: Revoked access token is denied
- GIVEN an access token JTI is recorded in the blacklist namespace with remaining TTL
- WHEN that token is used again
- THEN the request is denied
- AND if Redis is unavailable, validation fails closed

### Requirement: Table session credentials

The auth domain MUST define an HMAC-signed table session credential limited to table-scoped operations. The payload MUST at least identify `branch_id`, `table_id`, `session_id`, and expiration metadata. Issuance MAY happen through a staff-only generation endpoint or through a public session-join flow, as long as the resulting credential is constrained to the same scope.

#### Scenario: Public join can issue the canonical table credential
- GIVEN a diner joins a valid branch/table session
- WHEN the public join flow succeeds
- THEN the response may issue the HMAC table credential
- AND that credential does not grant staff JWT permissions
