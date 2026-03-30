---
change: foundation-auth
phase: 2
artifact: proposal
source: g1-reconciliation
date: 2026-03-30
status: approved
---

# Proposal: Foundation Auth

## Intent

Reconcile Phase 2 around the auth model actually chosen: branch-scoped staff access, role-strategy authorization, and explicit tenant isolation without stale claims about global role-only RBAC or automatic query rewriting.

## Scope

### In Scope
- JWT login/refresh/logout with 15m access + 7d refresh rotation.
- Branch-scoped identity via `branch_ids`, `roles[]`, and `UserBranchRole`.
- Authorization through `PermissionContext` + role strategies.
- Explicit tenant/branch scoping in services and repositories.
- Public table-session join using table-token primitives.
- Login abuse protection and refresh reuse detection.

### Out of Scope
- MFA, invitations, password recovery, OAuth.
- WebSocket auth hardening and frontend implementation details beyond auth/profile contract.

## Approach

Login stays lightweight: authenticate credentials, issue tokens/cookie, and return only the session/auth payload needed to bootstrap the client. Staff profile, branch context, and derived permissions are fetched separately from a protected profile endpoint.

JWT claims must support branch-aware authorization instead of a single global role narrative. `PermissionContext` resolves the effective strategy from the authenticated user plus selected branch context, while services/repos MUST apply explicit tenant filters rather than relying on transparent ORM interception.

Public diner access is a separate primitive: table tokens/session join enable anonymous table-scoped entry, but do not imply staff auth or legacy HMAC-only session claims beyond that boundary.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend auth domain` | Modified | Claims, refresh flow, profile contract |
| `authorization layer` | Modified | `PermissionContext` and strategies |
| `services/repos` | Modified | Explicit tenant/branch scoping |
| `public table access` | Modified | Session join + table token boundary |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Branch leakage from weak scoping | High | Enforce branch filters in every service/repo path and test cross-branch denial |
| Refresh replay/family compromise | Medium | Rotation, reuse detection, family revocation, audit trail |
| Login abuse / credential stuffing | High | Rate limiting, lockouts, monitoring |

## Rollback Plan

Revert claim/profile contract changes, restore prior proposal language, and disable any branch-context enforcement introduced after validation if cross-branch regressions appear.

## Dependencies

- Phase 1 infra, Redis, JWT, auth persistence.
- Governance level: **CRITICO**.

## Success Criteria

- [ ] Proposal matches reconciled Phase 2 architecture and removes stale auth claims.
- [ ] Branch-scoped auth, `PermissionContext`, explicit scoping, and table-token boundary are stated clearly.
- [ ] Security posture for refresh rotation/reuse detection and login abuse protection remains explicit.
