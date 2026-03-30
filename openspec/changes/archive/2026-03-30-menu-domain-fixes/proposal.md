---
change: menu-domain-fixes
phase: 4-fixes
artifact: proposal
status: draft
created_at: 2026-03-30
parent_change: menu-domain
---

# Proposal — menu-domain-fixes

## Intent

Phase 4 (menu-domain) was archived with PASS_WITH_WARNINGS (5 warnings). This change addresses all 5 warnings so Phase 4 can be re-archived with a clean PASS — zero warnings, zero tech debt carried forward.

## Scope

### In scope

| Warning | Severity | Fix |
|---------|----------|-----|
| **W1 — Seed data not in migrations** | MEDIUM | New migration `005_seed_system_data.py` with idempotent `INSERT ... ON CONFLICT DO NOTHING` for all 14 EU allergens, 6 cross-reactions, 7 dietary profiles, 10 cooking methods, 4 badges, 6 seals |
| **W2 — Rate limiting on public endpoints** | LOW | Add `@limiter.limit("60/minute")` decorator + `request: Request` param to 4 public route handlers in `routers/public/` |
| **W6 — N+1 queries in PublicMenuService** | MEDIUM | Extend `selectinload`/`joinedload` chains to eagerly load dietary profiles, cooking methods, badges, seals, and cross-reactions — eliminate per-product DB loops |
| **W8 — Dashboard menu-domain pages** | LOW | Audit and fix route registration, service files, and TypeScript types for existing Allergens, Badges, CookingMethods, DietaryProfiles, Products, Seals pages |
| **W9 — Missing tests** | HIGH | 5 new test files covering all 15 spec scenarios (allergens, products, public menu, batch pricing, cache invalidation) |

### Out of scope

- No new features or API changes
- No schema migrations (tables already exist from `004`)
- No changes to pwa_menu or ws_gateway
- No refactoring beyond what's needed to fix the 5 warnings
- No changes to auth, billing, or other domain boundaries

## Approach

### Group A — Quick wins (W2, W8)

Low-risk, isolated changes that can be done independently.

- **W2**: Add rate limit decorators to `rest_api/app/routers/public/menu.py`, `allergens.py`, `branches.py`. Mechanical — one decorator + one param per handler.
- **W8**: Verify route registration in `dashboard/src/router/`, confirm service files exist and types are correct. Fix any missing registrations.

### Group B — Backend integrity (W1, W6)

Changes that touch data layer — higher risk, need careful review.

- **W1**: New Alembic migration `005_seed_system_data.py`. All inserts use `ON CONFLICT DO NOTHING` for idempotency. Cross-reactions resolve allergen IDs via subselect by code (respects `allergen_id < related_allergen_id` constraint). Downgrade truncates only system-seeded rows.
- **W6**: Refactor `PublicMenuService._build_product_detail()` and `_build_allergens()` to use eager loading instead of per-product loops. Add `selectinload(Product.dietary_profiles).joinedload(ProductDietaryProfile.dietary_profile)` and equivalent chains for cooking methods, badges, seals, and cross-reactions.

### Group C — Tests (W9)

Depends on Group A + B being complete (tests validate the fixes).

- `tests/test_allergens.py` — CRUD, system allergen protection, cross-reactions (S1-S3)
- `tests/test_products.py` — creation, allergen assignment, free_of validation, branch exclusion, badges (S4-S5, S9, S14-S15)
- `tests/test_public_menu.py` — dietary filtering, allergen-free filtering, per-branch pricing, rate limiting (S6-S8, S13)
- `tests/test_batch_price.py` — preview, apply, negative price clamping (S10-S11)
- `tests/test_cache_invalidation.py` — cache key patterns, invalidation triggers (S12)
- Expand `tests/conftest.py` with menu-domain fixtures (allergens, products, branches with prices)

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Migration `005` runs on DB with partial seed data from `seed.py` | Medium | Low | `ON CONFLICT DO NOTHING` makes it idempotent — safe to run on any state |
| N+1 fix changes query shape, breaks serialization | Low | Medium | Test with existing public menu endpoint assertions; verify JSON output matches current shape |
| Cross-reaction subselects rely on allergen codes being stable | Low | Low | Codes are EU standard (EN-1 through EN-14) — immutable by design |
| Rate limit decorators interfere with test client | Low | Low | Test client can use `TestClient` with rate limiter disabled or overridden in conftest |

## Success Criteria

1. `sdd-verify menu-domain-fixes` returns **PASS** with 0 warnings
2. All 5 new test files pass (`pytest tests/test_allergens.py tests/test_products.py tests/test_public_menu.py tests/test_batch_price.py tests/test_cache_invalidation.py`)
3. Phase 4 (menu-domain) re-archived with **PASS** status
4. No regressions in existing Phase 1-3 tests
