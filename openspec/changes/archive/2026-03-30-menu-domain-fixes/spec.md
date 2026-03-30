---
change: menu-domain-fixes
phase: 4-fixes
artifact: spec
status: complete
created_at: 2026-03-30
parent_spec: openspec/specs/menu-domain/spec.md
---

# SDD Spec — menu-domain-fixes

## Status: COMPLETE

This spec defines the requirements to resolve the 5 warnings from the Phase 4 (menu-domain) archive. W8 was confirmed resolved during exploration — it is documented here for completeness only.

---

## 1. W1 — Seed Data Migration Requirements

### 1.1 Migration File

- The system MUST provide Alembic migration `005_seed_system_data.py` that runs on `alembic upgrade head`.
- The migration MUST be idempotent — safe to run any number of times on any DB state (including DBs already partially seeded by `seed.py`).
- All inserts MUST use `INSERT ... ON CONFLICT DO NOTHING` semantics.
- The migration MUST include a `downgrade()` that removes only the rows it inserted (identified by `is_system=True` / `tenant_id IS NULL`). It MUST NOT touch tenant-created rows.

### 1.2 Allergens (14 rows)

- The migration MUST insert exactly 14 allergens with `is_system=True` and `tenant_id=NULL`.
- Codes MUST match the EU mandatory list exactly: `gluten`, `dairy`, `eggs`, `fish`, `crustaceans`, `tree_nuts`, `soy`, `celery`, `mustard`, `sesame`, `sulfites`, `lupins`, `mollusks`, `peanuts`.
- Each row MUST include: `code`, `name` (human-readable Spanish label), `is_system=True`, `tenant_id=NULL`.
- The `icon` field SHOULD be populated with a meaningful identifier string for each allergen.

### 1.3 Allergen Cross-Reactions (6 rows)

- The migration MUST insert exactly 6 `AllergenCrossReaction` rows representing known EU cross-sensitivities.
- Each row MUST satisfy the DB constraint `allergen_id < related_allergen_id` — allergen IDs MUST be resolved via subselect by `code`, not by hardcoded integer IDs.
- Each row MUST include `severity` (enum: `low` / `moderate` / `severe` / `life_threatening`) and a `description` explaining the cross-reaction.
- The 6 pairs MUST cover: `gluten`↔`celery`, `dairy`↔`soy`, `fish`↔`crustaceans`, `fish`↔`mollusks`, `crustaceans`↔`mollusks`, `tree_nuts`↔`peanuts`.

### 1.4 Dietary Profiles (7 rows)

- The migration MUST insert exactly 7 dietary profiles with `is_system=True` and `tenant_id=NULL`.
- Codes MUST be: `vegetarian`, `vegan`, `gluten_free`, `dairy_free`, `celiac_safe`, `keto`, `low_sodium`.
- Each row MUST include: `code`, `name` (Spanish label), `is_system=True`, `tenant_id=NULL`.

### 1.5 Cooking Methods (10 rows)

- The migration MUST insert exactly 10 cooking methods with `is_system=True` and `tenant_id=NULL`.
- Codes MUST be: `grill`, `oven`, `fryer`, `steam`, `raw`, `sous_vide`, `smoke`, `saute`, `boil`, `roast`.
- Each row MUST include: `code`, `name` (Spanish label), `is_system=True`, `tenant_id=NULL`.

### 1.6 Badges (4 rows)

- The migration MUST insert exactly 4 badges with `is_system=True` and `tenant_id=NULL`.
- The 4 badges MUST be:
  - `new` — "Nuevo", color `#22C55E`
  - `best_seller` — "Más vendido", color `#F59E0B`
  - `chef_recommends` — "Chef recomienda", color `#8B5CF6`
  - `on_sale` — "Oferta", color `#EF4444`

### 1.7 Seals (6 rows)

- The migration MUST insert exactly 6 seals with `is_system=True` and `tenant_id=NULL`.
- The 6 seals MUST be:
  - `organic` — "Orgánico", color `#16A34A`
  - `local` — "Producto local", color `#2563EB`
  - `preservative_free` — "Sin conservantes", color `#D97706`
  - `artisan` — "Artesanal", color `#9333EA`
  - `sustainable` — "Sustentable", color `#059669`
  - `fair_trade` — "Comercio justo", color `#0891B2`

---

## 2. W2 — Rate Limiting Requirements

### 2.1 Enforcement

- All public API endpoints MUST enforce a rate limit of 60 requests per minute per IP address.
- Requests exceeding the limit MUST return HTTP 429 Too Many Requests.
- The HTTP 429 response MUST include a `Retry-After` header indicating when the client may retry.

### 2.2 Affected Endpoints

The rate limit MUST be applied to all 4 public route handlers across 3 files:

| File | Handler | Endpoint |
|------|---------|----------|
| `rest_api/app/routers/public/menu.py` | `get_menu` | `GET /api/public/menu/{slug}` |
| `rest_api/app/routers/public/menu.py` | `get_product_detail` | `GET /api/public/menu/{slug}/product/{id}` |
| `rest_api/app/routers/public/allergens.py` | `get_allergens` | `GET /api/public/allergens` |
| `rest_api/app/routers/public/branches.py` | `get_branches` | `GET /api/public/branches` |

### 2.3 Implementation

- Each handler MUST receive a `request: Request` parameter (required by the SlowAPI limiter).
- Each handler MUST be decorated with `@limiter.limit("60/minute")`.
- The limiter MUST use the client IP address as the rate limit key.
- The existing `SlowAPI` limiter already configured in `rest_api/app/` MUST be reused — no new limiter instance.

### 2.4 Test Isolation

- Tests MUST be able to bypass or override the rate limiter. The test `conftest.py` MUST configure `app.state.limiter` to use a mock or reset strategy that prevents test-to-test interference.

---

## 3. W6 — Query Performance Requirements

### 3.1 N+1 Prohibition

- `PublicMenuService` MUST NOT issue per-product database queries for any of the following relationships: dietary profiles, cooking methods, badges, seals, allergen cross-reactions.
- The number of database queries for a full menu response MUST NOT grow linearly with the number of products.

### 3.2 Eager Loading — Menu Endpoint

- The query loading products for `GET /api/public/menu/{slug}` MUST eagerly load, via `selectinload` or `joinedload` chains:
  - `Product.allergens` → `ProductAllergen.allergen`
  - `Product.dietary_profiles` → `ProductDietaryProfile.dietary_profile`
  - `Product.cooking_methods` → `ProductCookingMethod.cooking_method`
  - `Product.badges` → `ProductBadge.badge`
  - `Product.seals` → `ProductSeal.seal`

### 3.3 Eager Loading — Product Detail Endpoint

- The query loading a single product for `GET /api/public/menu/{slug}/product/{id}` MUST eagerly load, via `selectinload` or `joinedload` chains:
  - All relationships listed in 3.2
  - `ProductAllergen.allergen` → `Allergen.cross_reactions` → `AllergenCrossReaction.related_allergen`
  - `Product.ingredients` (ordered by `sort_order`)

### 3.4 Allergen Catalog Endpoint

- The query loading allergens for `GET /api/public/allergens` MUST eagerly load `Allergen.cross_reactions` → `AllergenCrossReaction.related_allergen` in a single query.

### 3.5 No Logic Change

- The refactor MUST NOT change the response shape or business logic of any public endpoint.
- The JSON output before and after the fix MUST be identical for the same input data.

---

## 4. W8 — Dashboard Frontend

- RESOLVED: Exploration confirmed all dashboard pages (Allergens, Badges, CookingMethods, DietaryProfiles, Products, Seals), routes, and TypeScript service files are present and correctly registered. No code changes required for W8.

---

## 5. W9 — Test Coverage Requirements

### 5.1 Test Infrastructure

- `tests/conftest.py` MUST be extended with menu-domain fixtures:
  - `system_allergens` — fixture that confirms (or creates) the 14 seeded system allergens.
  - `product_with_allergens(branch, allergens)` — factory fixture for a published product with assigned allergens.
  - `branch_with_prices(tenant, products)` — factory fixture for a branch with BranchProduct records at specific prices.
- Rate limiter MUST be disabled or reset between tests to prevent cross-test failures (configure via `app.state.limiter`).

### 5.2 test_allergens.py — Covers S1, S2, S3

- MUST verify S1: after `alembic upgrade head`, exactly 14 allergens exist with `is_system=True` and `tenant_id=NULL`, codes match the EU list.
- MUST verify S2: a tenant admin can create a custom allergen (`is_system=False`, `tenant_id` set); system allergens remain unaffected.
- MUST verify that system allergens (`is_system=True`) cannot be edited or deleted — service layer MUST reject with an appropriate error.
- MUST verify S3: cross-reaction between "crustaceans" and a related allergen is bidirectional — querying either side returns the relation.
- MUST verify that the 6 seeded cross-reactions are present after migration.

### 5.3 test_products.py — Covers S4, S5, S9, S14, S15

- MUST verify S4: assigning allergen "gluten" with `presence_type="contains"` creates a `ProductAllergen` record and the public menu reflects it in `allergenSummary.contains`.
- MUST verify S5: assigning allergen with `presence_type="free_of"` and `risk_level` not `"low"` is rejected with a validation error.
- MUST verify S9: a product with `BranchProduct.is_active=False` for a given branch does NOT appear in that branch's public menu.
- MUST verify S14: assigning a badge to a product causes that badge to appear in `product.badges` in the public menu response.
- MUST verify S15: a tenant admin can create a custom seal (`is_system=False`, `tenant_id` set), and it can be assigned to a product.

### 5.4 test_public_menu.py — Covers S6, S7, S8, S13

- MUST verify S6: requesting `?dietary=vegetarian` returns only products with the `vegetarian` dietary profile; products without it are excluded.
- MUST verify S6 multi-filter: requesting `?dietary=vegan,vegetarian` returns only products matching ALL specified profiles.
- MUST verify S7: requesting `?allergen_free=gluten` excludes products with `contains` gluten AND products with `may_contain` gluten; products with `free_of` gluten remain in the response.
- MUST verify S8: effective price for a branch is `BranchProduct.price_cents` when set; falls back to `Product.base_price_cents` when `BranchProduct.price_cents` is NULL.
- MUST verify S13: after 60 requests from the same IP to any public endpoint within one minute, request #61 returns HTTP 429 with a `Retry-After` header.

### 5.5 test_batch_price.py — Covers S10, S11

- MUST verify S10: `POST /api/dashboard/products/batch-price/preview` returns old and new prices for ALL branches for all selected products; new prices are rounded to the nearest integer.
- MUST verify S10 rounding: `round(old_price * (1 + pct/100))` is used for percentage increases and `round(old_price * (1 - pct/100))` for decreases.
- MUST verify S11: when a `fixed_subtract` operation would result in a negative price, the preview shows `new_price_cents=0` (clamped, not negative).
- MUST verify the two-step flow: the preview endpoint MUST NOT modify any price; only the apply endpoint (with `confirmed=True`) MUST persist changes.
- MUST verify that applying a batch price update creates audit log entries with `old_value` and `new_value` for each changed `BranchProduct`.

### 5.6 test_cache_invalidation.py — Covers S12

- MUST verify S12: after a public menu response is cached under `cache:public:menu:{branch_slug}`, updating a product in that branch causes the cache key to be deleted.
- MUST verify that the next public menu request after invalidation issues a real database query and re-caches the result.
- MUST verify cache key patterns: product update invalidates `cache:public:menu:{branch_slug}*` and `cache:public:product:*:{product_id}`; allergen update invalidates `cache:public:allergens:{tenant_slug}` and all branch menu keys for that tenant.
- MUST verify TTL: freshly cached keys have a TTL of 300 seconds (within a 5-second tolerance window).
- MUST verify the `Cache-Control: public, max-age=300` header is present on all public endpoint responses.

---

## 6. Acceptance Scenarios

| Scenario | Spec Ref | Test File | Expected |
|----------|----------|-----------|----------|
| Fresh DB after `alembic upgrade head` has exactly 14 system allergens | S1 | test_allergens.py | 14 rows with `is_system=True`, `tenant_id=NULL`, codes match EU list |
| Fresh DB after migration has 6 cross-reactions | S1 | test_allergens.py | 6 `AllergenCrossReaction` rows with correct pairs and severity |
| Fresh DB after migration has 7 dietary profiles | S1 | test_allergens.py | 7 rows with `is_system=True` |
| Fresh DB after migration has 10 cooking methods | S1 | test_allergens.py | 10 rows with `is_system=True` |
| Fresh DB after migration has 4 badges | S1 | test_allergens.py | 4 rows with correct codes, colors |
| Fresh DB after migration has 6 seals | S1 | test_allergens.py | 6 rows with correct codes, colors |
| Running migration twice leaves exactly the same seed count | W1 | test_allergens.py | No duplicate rows (idempotency) |
| Public endpoint returns 429 after 60 requests/minute | S13 | test_public_menu.py | HTTP 429 + `Retry-After` header |
| Product with `free_of` + non-`low` risk_level is rejected | S5 | test_products.py | HTTP 422 with validation message |
| Dietary filter returns only matching products | S6 | test_public_menu.py | Products without profile are absent |
| Allergen-free filter excludes `contains` and `may_contain` | S7 | test_public_menu.py | Only `free_of` products remain |
| Branch-specific price overrides base price | S8 | test_public_menu.py | `priceCents` equals branch override |
| Base price used when BranchProduct.price_cents is NULL | S8 | test_public_menu.py | `priceCents` equals product base price |
| is_active=False product excluded from public menu | S9 | test_products.py | Product absent from response |
| Batch preview does not persist changes | S10 | test_batch_price.py | DB prices unchanged after preview |
| Negative batch result clamped to 0 | S11 | test_batch_price.py | `new_price_cents=0` |
| Cache invalidated on product update | S12 | test_cache_invalidation.py | Key deleted; next request re-caches |
| Public menu response has no N+1 queries | W6 | test_public_menu.py | Query count constant regardless of product count |
| `Cache-Control: public, max-age=300` present on all public responses | §1.11 | test_public_menu.py | Header present on 200 responses |
