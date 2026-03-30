---
change: menu-domain-fixes
phase: 4-fixes
artifact: tasks
status: complete
created_at: 2026-03-30
---

# SDD Tasks — menu-domain-fixes

## Execution Order

Groups must be executed in sequence: **A → B → C**.
- Group A: Quick wins — isolated, low-risk, no dependencies
- Group B: Backend integrity — data layer, depends on nothing in A but must precede tests
- Group C: Test coverage — validates A and B; write tests AFTER the fixes are in place

---

## Group A — Quick Wins

### Task A1: Rate Limiting on Public Endpoints (W2)

**Description**: Add `@limiter.limit("60/minute")` decorator and `request: Request` parameter to all 4 public route handlers. The `limiter` instance is already defined and working — this is a mechanical addition only.

**Reference**: Design D2, Spec §2.1–2.4

**Files**:
- `rest_api/app/routers/public/menu.py` — handlers: `get_menu`, `get_product_detail`
- `rest_api/app/routers/public/allergens.py` — handler: `get_allergens`
- `rest_api/app/routers/public/branches.py` — handler: `get_branches`

**Current state** (verified by reading source):
- None of the 4 handlers have `@limiter.limit(...)` decorator
- None of the 4 handlers have `request: Request` as a parameter
- No handler imports `limiter` or `Request` from starlette

**Acceptance Criteria**:
- [x] `rest_api/app/routers/public/menu.py` imports `limiter` from `rest_api.app.middleware.rate_limit`
- [x] `rest_api/app/routers/public/menu.py` imports `Request` from `starlette.requests`
- [x] `get_menu` has `@limiter.limit("60/minute")` decorator placed AFTER `@router.get("/{slug}")`
- [x] `get_menu` has `request: Request` as its FIRST positional parameter (before `slug`)
- [x] `get_product_detail` has `@limiter.limit("60/minute")` decorator placed AFTER `@router.get("/{slug}/product/{product_id}")`
- [x] `get_product_detail` has `request: Request` as its FIRST positional parameter (before `slug`)
- [x] `rest_api/app/routers/public/allergens.py` imports `limiter` from `rest_api.app.middleware.rate_limit`
- [x] `rest_api/app/routers/public/allergens.py` imports `Request` from `starlette.requests`
- [x] `get_allergens` has `@limiter.limit("60/minute")` decorator placed AFTER `@router.get("/")`
- [x] `get_allergens` has `request: Request` as its FIRST positional parameter (before `tenant`)
- [x] `rest_api/app/routers/public/branches.py` imports `limiter` from `rest_api.app.middleware.rate_limit`
- [x] `rest_api/app/routers/public/branches.py` imports `Request` from `starlette.requests`
- [x] `get_branches` has `@limiter.limit("60/minute")` decorator placed AFTER `@router.get("/")`
- [x] `get_branches` has `request: Request` as its FIRST positional parameter (before `tenant`)
- [x] All 4 handlers' existing parameters and logic remain unchanged

---

## Group B — Backend Integrity

### Task B1: Seed Data Migration (W1)

**Description**: Create Alembic migration `005_seed_system_data.py` with idempotent inserts for all system catalog data. Uses `WHERE NOT EXISTS` for allergens/dietary profiles/cooking methods (NULL tenant_id breaks `ON CONFLICT`), and `ON CONFLICT DO NOTHING` for cross-reactions. Downgrade removes only system rows.

**Reference**: Design D1, Spec §1.1–1.7

**Files**:
- NEW: `alembic/versions/005_seed_system_data.py`

**Migration metadata** (verified):
- `revision = "005"`
- `down_revision = "004"` (last migration is `004_menu_domain_sprint4.py` with `revision: str = "004"`)

**Acceptance Criteria**:
- [x] File exists at `alembic/versions/005_seed_system_data.py`
- [x] `revision = "005"` and `down_revision = "004"` set correctly
- [x] `upgrade()` inserts exactly 14 allergens using `WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = '<code>' AND is_system = TRUE)` guard (one statement per allergen)
- [x] All 14 allergen codes present: `gluten`, `dairy`, `eggs`, `fish`, `crustaceans`, `tree_nuts`, `soy`, `celery`, `mustard`, `sesame`, `sulfites`, `lupins`, `mollusks`, `peanuts`
- [x] Each allergen row includes `code`, `name` (Spanish label), `icon`, `is_system = TRUE`, `tenant_id = NULL`
- [x] `upgrade()` inserts exactly 6 cross-reactions using `SELECT LEAST(a1.id, a2.id), GREATEST(a1.id, a2.id) FROM allergens a1, allergens a2 WHERE a1.code = '...' AND a1.is_system = TRUE AND a2.code = '...' AND a2.is_system = TRUE ON CONFLICT DO NOTHING`
- [x] The 6 cross-reaction pairs: `gluten`↔`celery` (moderate), `dairy`↔`soy` (moderate), `peanuts`↔`tree_nuts` (severe), `peanuts`↔`soy` (moderate), `peanuts`↔`lupins` (severe), `fish`↔`crustaceans` (moderate)
- [x] Each cross-reaction row includes `allergen_id`, `related_allergen_id`, `severity`, `description`
- [x] `upgrade()` inserts exactly 7 dietary profiles using `WHERE NOT EXISTS` guard
- [x] Dietary profile codes: `vegetarian`, `vegan`, `gluten_free`, `dairy_free`, `celiac_safe`, `keto`, `low_sodium`
- [x] `upgrade()` inserts exactly 10 cooking methods using `WHERE NOT EXISTS` guard
- [x] Cooking method codes: `grill`, `oven`, `fryer`, `steam`, `raw`, `sous_vide`, `smoke`, `saute`, `boil`, `roast`
- [x] `upgrade()` inserts exactly 4 badges using `WHERE NOT EXISTS` guard with correct codes and colors: `new` (#22C55E), `best_seller` (#F59E0B), `chef_recommends` (#8B5CF6), `on_sale` (#EF4444)
- [x] `upgrade()` inserts exactly 6 seals using `WHERE NOT EXISTS` guard with correct codes and colors: `organic` (#16A34A), `local` (#2563EB), `preservative_free` (#D97706), `artisan` (#9333EA), `sustainable` (#059669), `fair_trade` (#0891B2)
- [x] Running `upgrade()` twice produces identical row counts (idempotent — no duplicates)
- [x] `downgrade()` deletes cross-reactions FIRST (FK dependency): `DELETE FROM allergen_cross_reactions WHERE allergen_id IN (SELECT id FROM allergens WHERE is_system = TRUE)`
- [x] `downgrade()` deletes allergens, dietary profiles, cooking methods, badges, seals WHERE `is_system = TRUE`
- [x] `downgrade()` does NOT touch rows with `is_system = FALSE` (tenant-created data)

### Task B2: Add Relationships to Junction Models (W6 prerequisite)

**Description**: Add `relationship()` declarations to the 4 junction models that currently lack them. This is required before the eager-load chains in B3 can work — without relationships, `joinedload` through the junction is impossible.

**Reference**: Design D3 Part 1, Spec §3.1

**Files** (all verified — none currently have `relationship()`):
- `shared/shared/models/catalog/product_dietary_profile.py`
- `shared/shared/models/catalog/product_cooking_method.py`
- `shared/shared/models/catalog/product_badge.py`
- `shared/shared/models/catalog/product_seal.py`

**Acceptance Criteria**:
- [x] `shared/shared/models/catalog/product_dietary_profile.py` imports `relationship` from `sqlalchemy.orm` and `TYPE_CHECKING` from `typing`
- [x] `ProductDietaryProfile` has `dietary_profile: Mapped["DietaryProfile"] = relationship("DietaryProfile")` as a class attribute
- [x] `shared/shared/models/catalog/product_cooking_method.py` imports `relationship` from `sqlalchemy.orm` and `TYPE_CHECKING` from `typing`
- [x] `ProductCookingMethod` has `cooking_method: Mapped["CookingMethod"] = relationship("CookingMethod")` as a class attribute
- [x] `shared/shared/models/catalog/product_badge.py` imports `relationship` from `sqlalchemy.orm` and `TYPE_CHECKING` from `typing`
- [x] `ProductBadge` has `badge: Mapped["Badge"] = relationship("Badge")` as a class attribute
- [x] `shared/shared/models/catalog/product_seal.py` imports `relationship` from `sqlalchemy.orm` and `TYPE_CHECKING` from `typing`
- [x] `ProductSeal` has `seal: Mapped["Seal"] = relationship("Seal")` as a class attribute
- [x] No circular import errors when importing any of these models (use `TYPE_CHECKING` guard for type annotations)
- [x] No `back_populates` is required (these are read-only navigational relationships)

### Task B3: Fix N+1 in PublicMenuService (W6)

**Description**: Replace all per-product and per-allergen `await self._db.execute(select(...))` loops with direct attribute access, and extend the `.options()` chains in the two product queries to eagerly load through the junction relationships added in B2.

**Reference**: Design D3 Parts 2 and 3, Spec §3.1–3.5

**Prerequisite**: Task B2 must be complete before this task.

**Files**:
- `rest_api/app/services/domain/public_menu_service.py`

**Current N+1 locations** (verified by reading source):
- `_build_menu` lines ~170–215: per-product loops for dietary profiles, cooking methods, badges, seals — each fires a `SELECT` inside the loop
- `_build_product_detail` lines ~330–412: per-product loops for cross-reactions, dietary profiles, cooking methods, badges, seals
- `_build_allergens` lines ~534–557: per-allergen loop for cross-reactions — fires a `SELECT` for each allergen

**Acceptance Criteria**:

Part 1 — `_build_menu` query options:
- [x] `_build_menu` query `.options()` replaces `selectinload(Product.product_dietary_profiles)` with `selectinload(Product.product_dietary_profiles).joinedload(ProductDietaryProfile.dietary_profile)`
- [x] `_build_menu` query `.options()` replaces `selectinload(Product.product_cooking_methods)` with `selectinload(Product.product_cooking_methods).joinedload(ProductCookingMethod.cooking_method)`
- [x] `_build_menu` query `.options()` replaces `selectinload(Product.product_badges)` with `selectinload(Product.product_badges).joinedload(ProductBadge.badge)`
- [x] `_build_menu` query `.options()` replaces `selectinload(Product.product_seals)` with `selectinload(Product.product_seals).joinedload(ProductSeal.seal)`

Part 2 — `_build_product_detail` query options:
- [x] `_build_product_detail` query `.options()` replaces `selectinload(Product.product_dietary_profiles)` with `selectinload(Product.product_dietary_profiles).joinedload(ProductDietaryProfile.dietary_profile)`
- [x] `_build_product_detail` query `.options()` replaces `selectinload(Product.product_cooking_methods)` with `selectinload(Product.product_cooking_methods).joinedload(ProductCookingMethod.cooking_method)`
- [x] `_build_product_detail` query `.options()` replaces `selectinload(Product.product_badges)` with `selectinload(Product.product_badges).joinedload(ProductBadge.badge)`
- [x] `_build_product_detail` query `.options()` replaces `selectinload(Product.product_seals)` with `selectinload(Product.product_seals).joinedload(ProductSeal.seal)`
- [x] `_build_product_detail` query `.options()` extends the allergen chain to: `selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen).selectinload(Allergen.cross_reactions_as_source).joinedload(AllergenCrossReaction.related_allergen)` (and same for `cross_reactions_as_related`)

Part 3 — `_build_menu` serialization loops:
- [x] `_build_menu` loop for dietary profiles replaces `await self._db.execute(select(DietaryProfile)...)` with direct `pdp.dietary_profile.code` access
- [x] `_build_menu` loop for cooking methods replaces `await self._db.execute(select(CookingMethod)...)` with direct `pcm.cooking_method.code` access
- [x] `_build_menu` loop for badges replaces `await self._db.execute(select(Badge)...)` with direct `pb.badge` attribute access
- [x] `_build_menu` loop for seals replaces `await self._db.execute(select(Seal)...)` with direct `ps.seal` attribute access

Part 4 — `_build_product_detail` serialization loops:
- [x] `_build_product_detail` loop for cross-reactions replaces the inner `await self._db.execute(select(AllergenCrossReaction)...)` with direct `a.cross_reactions_as_source` / `a.cross_reactions_as_related` attribute access (or `a.all_cross_reactions` if defined)
- [x] `_build_product_detail` loop for dietary profiles replaces `await self._db.execute(select(DietaryProfile)...)` with direct `pdp.dietary_profile` access
- [x] `_build_product_detail` loop for cooking methods replaces `await self._db.execute(select(CookingMethod)...)` with direct `pcm.cooking_method` access
- [x] `_build_product_detail` loop for badges replaces `await self._db.execute(select(Badge)...)` with direct `pb.badge` access
- [x] `_build_product_detail` loop for seals replaces `await self._db.execute(select(Seal)...)` with direct `ps.seal` access

Part 5 — `_build_allergens` query and loop:
- [x] `_build_allergens` query adds `.options(selectinload(Allergen.cross_reactions_as_source).joinedload(AllergenCrossReaction.related_allergen), selectinload(Allergen.cross_reactions_as_related).joinedload(AllergenCrossReaction.allergen))`
- [x] `_build_allergens` per-allergen loop replaces the inner `await self._db.execute(select(AllergenCrossReaction)...)` block with direct attribute access on `a.cross_reactions_as_source` and `a.cross_reactions_as_related`

Part 6 — Cleanup:
- [x] All inline `from shared.models.X import X` imports inside loops are moved to the top-level import block
- [x] No `await self._db.execute(select(...))` calls remain inside any per-product or per-allergen loop
- [x] Response JSON shape is identical to before the refactor (no field renames, no structure changes)

---

## Group C — Test Coverage

> **Prerequisite**: All Group A and Group B tasks must be complete before writing tests. Tests validate the fixes; they cannot pass against the broken state.

### Task C0: Extend conftest.py with Menu-Domain Fixtures (W9)

**Description**: Add shared fixtures used by all 5 new test files. Rate limiter must be disabled by default to prevent cross-test interference; a separate fixture re-enables it for rate-limit-specific tests.

**Reference**: Design D5, Spec §5.1

**Files**:
- `tests/conftest.py`

**Acceptance Criteria**:
- [x] `app` fixture (existing) is extended to set `limiter.enabled = False` after creating the application, so rate limiting is disabled by default in all tests
- [x] New fixture `enable_rate_limit` is added: sets `limiter.enabled = True` before yield, `limiter.enabled = False` after yield (used only by rate-limit tests)
- [x] New `@pytest_asyncio.fixture` `seed_tenant(db_session)` creates and commits a `Tenant` with slug, name, and `is_active=True`; returns the `Tenant` ORM object
- [x] New `@pytest_asyncio.fixture` `seed_branch(db_session, seed_tenant)` creates and commits a `Branch` linked to `seed_tenant` with slug, name, and `is_active=True`; returns the `Branch` ORM object
- [x] New `@pytest_asyncio.fixture` `seed_allergens(db_session)` creates at minimum 4 system allergens (`gluten`, `dairy`, `peanuts`, `tree_nuts`) with `is_system=True`, `tenant_id=None`; returns a list of `Allergen` objects
- [x] New `@pytest_asyncio.fixture` `seed_product(db_session, seed_tenant, seed_branch)` creates a `Product` with `is_available=True`, creates a `BranchProduct` linking it to `seed_branch` with `is_available=True` and a `base_price_cents` of 1000; returns the `Product` ORM object
- [x] All new seed fixtures call `await db_session.commit()` (via `safe_commit` or directly) after inserting rows
- [x] All new fixtures use `@pytest_asyncio.fixture` decorator (consistent with existing conftest style)

### Task C1: test_allergens.py — Allergen CRUD and System Protection (W9 — S1, S2, S3)

**Description**: Tests for allergen seeding, system allergen protection, and cross-reaction bidirectionality. Verifies the migration produces exactly the right seed data and that system rows are immutable.

**Reference**: Spec §5.2, acceptance scenarios S1–S3

**Files**:
- NEW: `tests/test_allergens.py`

**Acceptance Criteria**:
- [x] File exists at `tests/test_allergens.py`
- [x] `test_seed_allergens_count`: after `alembic upgrade head` (or equivalent direct DB setup), a `SELECT COUNT(*) FROM allergens WHERE is_system = TRUE AND tenant_id IS NULL` returns exactly 14
- [x] `test_seed_allergen_codes`: query all system allergens, verify their codes match exactly: `{gluten, dairy, eggs, fish, crustaceans, tree_nuts, soy, celery, mustard, sesame, sulfites, lupins, mollusks, peanuts}`
- [x] `test_seed_cross_reactions_count`: `SELECT COUNT(*) FROM allergen_cross_reactions` returns exactly 6 after seeding
- [x] `test_seed_cross_reactions_pairs`: verify the 6 pairs are present: `gluten`↔`celery`, `dairy`↔`soy`, `peanuts`↔`tree_nuts`, `peanuts`↔`soy`, `peanuts`↔`lupins`, `fish`↔`crustaceans`
- [x] `test_seed_dietary_profiles_count`: exactly 7 rows with `is_system = TRUE`
- [x] `test_seed_cooking_methods_count`: exactly 10 rows with `is_system = TRUE`
- [x] `test_seed_badges_count`: exactly 4 rows with `is_system = TRUE`
- [x] `test_seed_seals_count`: exactly 6 rows with `is_system = TRUE`
- [x] `test_seed_idempotent`: running the same inserts a second time leaves row counts unchanged (no duplicates)
- [x] `test_create_custom_allergen`: authenticated ADMIN can POST to create a custom allergen (`is_system=False`, `tenant_id` set); response returns 201
- [x] `test_system_allergen_cannot_be_deleted`: DELETE request targeting a system allergen (`is_system=True`) returns 400 or 403 — service layer rejects it
- [x] `test_system_allergen_cannot_be_edited`: PUT/PATCH request targeting a system allergen returns 400 or 403
- [x] `test_cross_reaction_bidirectional`: create a cross-reaction between allergen A and allergen B; querying the public allergens endpoint returns A in B's `crossReacts` list AND B in A's `crossReacts` list

### Task C2: test_products.py — Products, Allergen Assignment, and Validation (W9 — S4, S5, S9, S14, S15)

**Description**: Tests for product creation, allergen assignment, the `free_of`+`risk_level` validation rule, branch exclusion via `is_active`, and badge/seal assignment.

**Reference**: Spec §5.3, acceptance scenarios S4, S5, S9, S14, S15

**Files**:
- NEW: `tests/test_products.py`

**Acceptance Criteria**:
- [x] File exists at `tests/test_products.py`
- [x] `test_create_product_with_allergen`: POST product + allergen assignment with `presence_type="contains"`; verify `ProductAllergen` row exists in DB with `presence_type="contains"`
- [x] `test_allergen_appears_in_public_menu`: after assigning allergen with `presence_type="contains"`, GET public menu returns product with that allergen code in `allergenSummary.contains`
- [x] `test_free_of_high_risk_rejected`: POST allergen assignment with `presence_type="free_of"` and `risk_level` not equal to `"low"` (e.g., `"severe"`) returns 400 or 422 with a validation error message
- [x] `test_free_of_low_risk_accepted`: POST allergen assignment with `presence_type="free_of"` and `risk_level="low"` returns 201 — this combination is valid
- [x] `test_inactive_product_excluded_from_menu`: set `BranchProduct.is_active=False` for a product in `seed_branch`; GET public menu for that branch does NOT include that product
- [x] `test_assign_badge_to_product`: POST badge assignment to a product; GET product detail in public menu returns that badge in `product.badges`
- [x] `test_assign_seal_to_product`: POST seal assignment to a product; GET product detail in public menu returns that seal in `product.seals`
- [x] `test_create_custom_seal`: authenticated ADMIN can POST to create a custom seal (`is_system=False`, `tenant_id` set); response returns 201; custom seal can be assigned to a product

### Task C3: test_public_menu.py — Filtering, Pricing, and Rate Limiting (W9 — S6, S7, S8, S13)

**Description**: Tests for dietary filter (AND logic), allergen-free filter, per-branch price override, and rate limit enforcement (429 after 60 requests).

**Reference**: Spec §5.4, acceptance scenarios S6, S7, S8, S13

**Files**:
- NEW: `tests/test_public_menu.py`

**Acceptance Criteria**:
- [x] File exists at `tests/test_public_menu.py`
- [x] `test_dietary_filter_single`: GET `/api/public/menu/{slug}?dietary=vegetarian` returns only products that have the `vegetarian` dietary profile; products without it are absent
- [x] `test_dietary_filter_multi`: GET `/api/public/menu/{slug}?dietary=vegan,vegetarian` returns only products matching BOTH profiles simultaneously (AND logic, not OR)
- [x] `test_allergen_free_excludes_contains`: GET menu with `?allergen_free=gluten` excludes products where gluten has `presence_type="contains"`
- [x] `test_allergen_free_excludes_may_contain`: GET menu with `?allergen_free=gluten` also excludes products where gluten has `presence_type="may_contain"`
- [x] `test_allergen_free_keeps_free_of`: GET menu with `?allergen_free=gluten` KEEPS products where gluten has `presence_type="free_of"` (these are explicitly gluten-free)
- [x] `test_branch_price_override`: product has `base_price_cents=1000` and `BranchProduct.price_cents=1500`; GET public menu for that branch returns `priceCents=1500`
- [x] `test_branch_price_fallback`: product has `base_price_cents=1000` and `BranchProduct.price_cents=NULL`; GET public menu returns `priceCents=1000`
- [x] `test_cache_control_header`: GET public menu response includes `Cache-Control: public, max-age=300` header
- [x] `test_rate_limit_429` (uses `enable_rate_limit` fixture): fire 61 GET requests to `/api/public/menu/{slug}` from the same IP in sequence; request #61 returns HTTP 429
- [x] `test_rate_limit_retry_after_header` (uses `enable_rate_limit` fixture): the 429 response includes a `Retry-After` header with a non-empty value
- [ ] `test_no_n1_queries`: GET public menu with 3 products (each with dietary profiles, cooking methods, badges, seals) — assert total DB query count is bounded (not greater than 10 regardless of product count); use SQLAlchemy event listener or log capture to count queries

### Task C4: test_batch_price.py — Batch Price Preview and Apply (W9 — S10, S11)

**Description**: Tests for the two-step batch price update flow: preview must not persist, apply must persist, negative results must be clamped to 0.

**Reference**: Spec §5.5, acceptance scenarios S10, S11

**Files**:
- NEW: `tests/test_batch_price.py`

**Acceptance Criteria**:
- [x] File exists at `tests/test_batch_price.py`
- [x] `test_batch_preview_returns_prices`: POST to `/api/dashboard/products/batch-price/preview` with a percentage increase returns `old_price_cents` and `new_price_cents` for all selected products across all branches
- [x] `test_batch_preview_no_persistence`: after calling preview, query DB directly and confirm `BranchProduct.price_cents` is unchanged
- [x] `test_batch_preview_rounding`: for a 10% increase on price 333 cents, `new_price_cents = round(333 * 1.10) = 366`; assert exact value
- [x] `test_batch_preview_decrease_rounding`: for a 10% decrease on price 333 cents, `new_price_cents = round(333 * 0.90) = 300`; assert exact value
- [x] `test_batch_apply_persists`: POST to apply endpoint with `confirmed=True`; query DB and confirm `BranchProduct.price_cents` updated to new value
- [x] `test_batch_apply_creates_audit`: after applying, audit log entries exist with `old_value` and `new_value` for each changed `BranchProduct` row
- [x] `test_batch_negative_clamp`: apply a `fixed_subtract` that would result in a negative price (e.g., subtract 5000 from a 1000-cent product); assert `new_price_cents = 0` (clamped, not negative) in both preview and apply

### Task C5: test_cache_invalidation.py — Cache Key Patterns and Invalidation (W9 — S12)

**Description**: Tests for Redis cache behavior: TTL, `Cache-Control` header, key invalidation on product update and allergen update.

**Reference**: Spec §5.6, acceptance scenario S12

**Files**:
- NEW: `tests/test_cache_invalidation.py`

**Acceptance Criteria**:
- [x] File exists at `tests/test_cache_invalidation.py`
- [x] `test_menu_cached_on_first_request`: first GET to public menu calls `mock_redis.get` (cache miss), then calls `mock_redis.setex` to store result; assert `setex` was called with TTL=300
- [x] `test_menu_served_from_cache`: mock `mock_redis.get` to return a cached JSON string; second GET to public menu returns the cached response without hitting DB (assert no additional DB calls)
- [x] `test_product_update_invalidates_menu_cache`: update a product (PUT via dashboard API); assert `mock_redis.delete` was called with a key matching `cache:public:menu:{branch_slug}*`
- [x] `test_product_update_invalidates_product_cache`: update a product; assert `mock_redis.delete` was called with a key matching `cache:public:product:*:{product_id}`
- [x] `test_allergen_update_invalidates_allergen_cache`: update an allergen (PUT via dashboard API); assert `mock_redis.delete` was called with a key matching `cache:public:allergens:{tenant_slug}`
- [x] `test_allergen_update_invalidates_menu_cache`: update an allergen; assert `mock_redis.delete` was called for all branch menu keys for that tenant
- [x] `test_cache_ttl_is_300`: after a cache miss and re-cache, assert `setex` was called with `ttl=300` (within a 5-second tolerance is acceptable in real Redis; with mock, assert exact value 300)
- [x] `test_cache_control_header_present`: all public endpoint responses (menu, allergens, branches) include `Cache-Control: public, max-age=300` header

---

## Summary

| Group | Task | Files Changed | Checkboxes |
|-------|------|---------------|-----------|
| A | A1: Rate limiting | 3 files modified | 15 |
| B | B1: Seed migration | 1 file created | 17 |
| B | B2: Junction relationships | 4 files modified | 10 |
| B | B3: N+1 fix | 1 file modified | 22 |
| C | C0: conftest fixtures | 1 file modified | 8 |
| C | C1: test_allergens.py | 1 file created | 14 |
| C | C2: test_products.py | 1 file created | 8 |
| C | C3: test_public_menu.py | 1 file created | 11 |
| C | C4: test_batch_price.py | 1 file created | 7 |
| C | C5: test_cache_invalidation.py | 1 file created | 8 |

**Total checkboxes: 120**
