---
change: menu-domain-fixes
phase: 4-fixes
artifact: design
status: complete
created_at: 2026-03-30
---

# SDD Design -- menu-domain-fixes

## D1 -- Seed Migration

### File

`alembic/versions/005_seed_system_data.py`

### Strategy

Use `op.execute()` with raw SQL. Every insert uses `ON CONFLICT DO NOTHING` for full idempotency -- safe to run on databases that already have partial seed data from manual scripts.

### Allergens (14 EU standard)

The `allergens` table has a `UNIQUE(code, tenant_id)` constraint. System allergens have `tenant_id IS NULL`, and PostgreSQL treats `NULL != NULL` in unique indexes, so the standard `ON CONFLICT (code, tenant_id)` will NOT work for system rows. We need a workaround.

**Approach**: Use a `WHERE NOT EXISTS` guard instead of `ON CONFLICT`:

```sql
INSERT INTO allergens (code, name, description, icon, is_system, tenant_id)
SELECT 'gluten', 'Gluten', 'Cereales con gluten: trigo, centeno, cebada, avena, espelta, kamut', 'wheat', TRUE, NULL
WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'gluten' AND is_system = TRUE);
```

One statement per allergen. This is more verbose but handles the NULL tenant_id correctly.

Full list of 14 EU allergens (from Phase 4 design):

| code | name | icon |
|------|------|------|
| `gluten` | Gluten | wheat |
| `dairy` | Lacteos | milk |
| `eggs` | Huevos | egg |
| `fish` | Pescado | fish |
| `crustaceans` | Crustaceos | shrimp |
| `tree_nuts` | Frutos secos | nut |
| `soy` | Soja | soybean |
| `celery` | Apio | celery |
| `mustard` | Mostaza | mustard |
| `sesame` | Sesamo | sesame |
| `sulfites` | Sulfitos | sulfite |
| `lupins` | Altramuces | lupin |
| `mollusks` | Moluscos | shell |
| `peanuts` | Cacahuetes | peanut |

### Cross-reactions (6 known pairs)

The `allergen_cross_reactions` table has `CHECK (allergen_id < related_allergen_id)`. We use `LEAST`/`GREATEST` with subselects to guarantee canonical ordering, plus `ON CONFLICT DO NOTHING` on the unique pair:

```sql
INSERT INTO allergen_cross_reactions (allergen_id, related_allergen_id, description, severity)
SELECT
    LEAST(a1.id, a2.id),
    GREATEST(a1.id, a2.id),
    'Profilin cross-reactivity between gluten-containing cereals and celery',
    'moderate'
FROM allergens a1, allergens a2
WHERE a1.code = 'gluten' AND a1.is_system = TRUE
  AND a2.code = 'celery' AND a2.is_system = TRUE
ON CONFLICT DO NOTHING;
```

Full list of 6 pairs (from Phase 4 design):

| allergen_a | allergen_b | severity | description |
|------------|------------|----------|-------------|
| `gluten` | `celery` | moderate | Profilin cross-reactivity |
| `dairy` | `soy` | moderate | Casein cross-reactivity |
| `peanuts` | `tree_nuts` | severe | Shared protein epitopes |
| `peanuts` | `soy` | moderate | Legume family cross-reactivity |
| `peanuts` | `lupins` | severe | Legume family cross-reactivity |
| `fish` | `crustaceans` | moderate | Parvalbumin cross-reactivity |

### Dietary Profiles (7 system)

Same `WHERE NOT EXISTS` pattern as allergens (identical schema with NULL tenant_id):

```sql
INSERT INTO dietary_profiles (code, name, icon, is_system, tenant_id)
SELECT 'vegetarian', 'Vegetariano', 'leaf', TRUE, NULL
WHERE NOT EXISTS (SELECT 1 FROM dietary_profiles WHERE code = 'vegetarian' AND is_system = TRUE);
```

Codes: `vegetarian`, `vegan`, `gluten_free`, `dairy_free`, `celiac_safe`, `keto`, `low_sodium`.

### Cooking Methods (10 system)

Same `WHERE NOT EXISTS` pattern:

```sql
INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id)
SELECT 'grill', 'Parrilla', 'flame', TRUE, NULL
WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'grill' AND is_system = TRUE);
```

Codes: `grill`, `oven`, `fryer`, `steam`, `raw`, `sous_vide`, `smoke`, `saute`, `boil`, `roast`.

### Badges (4 system)

```sql
INSERT INTO badges (code, name, color, icon, is_system, tenant_id)
SELECT 'new', 'Nuevo', '#22C55E', 'sparkle', TRUE, NULL
WHERE NOT EXISTS (SELECT 1 FROM badges WHERE code = 'new' AND is_system = TRUE);
```

Codes and colors: `new` (#22C55E), `best_seller` (#F59E0B), `chef_recommends` (#8B5CF6), `on_sale` (#EF4444).

### Seals (6 system)

```sql
INSERT INTO seals (code, name, color, icon, is_system, tenant_id)
SELECT 'organic', 'Organico', '#16A34A', 'leaf', TRUE, NULL
WHERE NOT EXISTS (SELECT 1 FROM seals WHERE code = 'organic' AND is_system = TRUE);
```

Codes and colors: `organic` (#16A34A), `local` (#2563EB), `preservative_free` (#D97706), `artisan` (#9333EA), `sustainable` (#059669), `fair_trade` (#0891B2).

### Downgrade

```sql
DELETE FROM allergen_cross_reactions
WHERE allergen_id IN (SELECT id FROM allergens WHERE is_system = TRUE);

DELETE FROM allergens WHERE is_system = TRUE;
DELETE FROM dietary_profiles WHERE is_system = TRUE;
DELETE FROM cooking_methods WHERE is_system = TRUE;
DELETE FROM badges WHERE is_system = TRUE;
DELETE FROM seals WHERE is_system = TRUE;
```

Order matters: cross-reactions first (FK dependency on allergens).

---

## D2 -- Rate Limiting

### Current State

- `limiter` is a global `Limiter` instance in `rest_api/app/middleware/rate_limit.py`
- Default limit: `100/minute` per IP
- Already used in `rest_api/app/routers/public/session_router.py` as a working example
- Import path: `from rest_api.app.middleware.rate_limit import limiter`
- slowapi reads the `request: Request` parameter BY NAME from the function signature

### Pattern (verified from session_router.py)

```python
from rest_api.app.middleware.rate_limit import limiter
from starlette.requests import Request

@router.get("/{slug}")
@limiter.limit("60/minute")
async def get_menu(
    request: Request,  # <-- MUST be named "request" — slowapi reads it by name
    slug: str,
    ...
) -> JSONResponse:
```

### Files to modify (4 handlers across 3 files)

| File | Handler | Current `request` param? |
|------|---------|--------------------------|
| `rest_api/app/routers/public/menu.py` | `get_menu` | No -- add it |
| `rest_api/app/routers/public/menu.py` | `get_product_detail` | No -- add it |
| `rest_api/app/routers/public/allergens.py` | `get_allergens` | No -- add it |
| `rest_api/app/routers/public/branches.py` | `get_branches` | No -- add it |

### Changes per file

1. Add import: `from rest_api.app.middleware.rate_limit import limiter` and `from starlette.requests import Request`
2. Add `@limiter.limit("60/minute")` decorator AFTER `@router.get(...)` (slowapi requires the limiter decorator to be closer to the function)
3. Add `request: Request` as the FIRST parameter in the function signature

### Rate limit choice

60/minute per IP (stricter than the default 100/minute) because these are public endpoints hit by QR-scanning customers. This matches the session_router pattern.

---

## D3 -- N+1 Query Fix

### Problem Analysis

In `PublicMenuService`, the `_build_menu` and `_build_product_detail` methods use `selectinload` for junction tables (`product_dietary_profiles`, `product_cooking_methods`, `product_badges`, `product_seals`) but do NOT eagerly load the related entity through the junction. This causes individual SELECT queries inside the serialization loops:

```python
# Current: N+1 — one query per product per profile
for pdp in product.product_dietary_profiles:
    dp_result = await self._db.execute(
        select(DietaryProfile).where(DietaryProfile.id == pdp.dietary_profile_id)
    )
```

Same pattern repeated for: cooking methods, badges, seals, and cross-reactions.

### Root Cause

The junction models (`ProductDietaryProfile`, `ProductCookingMethod`, `ProductBadge`, `ProductSeal`) lack a `relationship()` back to their parent entity. Without these relationships, `joinedload` through the junction is impossible.

### Fix: Two-part approach

#### Part 1 -- Add missing relationships to junction models

**`shared/shared/models/catalog/product_dietary_profile.py`**:
```python
from sqlalchemy.orm import relationship
# Add TYPE_CHECKING import for DietaryProfile

dietary_profile: Mapped[DietaryProfile] = relationship("DietaryProfile")
```

**`shared/shared/models/catalog/product_cooking_method.py`**:
```python
cooking_method: Mapped[CookingMethod] = relationship("CookingMethod")
```

**`shared/shared/models/catalog/product_badge.py`**:
```python
badge: Mapped[Badge] = relationship("Badge")
```

**`shared/shared/models/catalog/product_seal.py`**:
```python
seal: Mapped[Seal] = relationship("Seal")
```

These are read-only navigational relationships -- no `back_populates` needed since they point TO the parent catalog entity and we never navigate the reverse direction.

#### Part 2 -- Extend `.options()` in queries

**`_build_menu` query** (line ~82):
```python
.options(
    joinedload(Product.subcategory).joinedload(Subcategory.category),
    selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
    selectinload(Product.product_dietary_profiles).joinedload(ProductDietaryProfile.dietary_profile),  # NEW
    selectinload(Product.product_cooking_methods).joinedload(ProductCookingMethod.cooking_method),      # NEW
    selectinload(Product.product_badges).joinedload(ProductBadge.badge),                                # NEW
    selectinload(Product.product_seals).joinedload(ProductSeal.seal),                                   # NEW
    selectinload(Product.branch_products),
)
```

**`_build_product_detail` query** (line ~303):
```python
.options(
    joinedload(Product.subcategory).joinedload(Subcategory.category),
    selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
    selectinload(Product.product_dietary_profiles).joinedload(ProductDietaryProfile.dietary_profile),
    selectinload(Product.product_cooking_methods).joinedload(ProductCookingMethod.cooking_method),
    selectinload(Product.product_badges).joinedload(ProductBadge.badge),
    selectinload(Product.product_seals).joinedload(ProductSeal.seal),
    selectinload(Product.ingredients),
    selectinload(Product.branch_products),
)
```

**`_build_allergens` query** -- eager load cross-reactions in a SINGLE query:
```python
result = await self._db.execute(
    select(Allergen).where(
        or_(Allergen.tenant_id.is_(None), Allergen.tenant_id == tenant.id),
        Allergen.deleted_at.is_(None),
    )
    .options(
        selectinload(Allergen.cross_reactions_as_source).joinedload(AllergenCrossReaction.related_allergen),
        selectinload(Allergen.cross_reactions_as_related).joinedload(AllergenCrossReaction.allergen),
    )
    .order_by(Allergen.is_system.desc(), Allergen.name)
)
```

Then use `a.all_cross_reactions` property (already defined on the model) in the serialization loop instead of executing separate queries.

**`_build_product_detail` allergen cross-reactions** -- same approach:
```python
# In the product detail query, extend allergen loading to include cross-reactions:
selectinload(Product.product_allergens)
    .joinedload(ProductAllergen.allergen)
    .selectinload(Allergen.cross_reactions_as_source)
    .joinedload(AllergenCrossReaction.related_allergen),
selectinload(Product.product_allergens)
    .joinedload(ProductAllergen.allergen)
    .selectinload(Allergen.cross_reactions_as_related)
    .joinedload(AllergenCrossReaction.allergen),
```

#### Part 3 -- Update serialization loops

Replace all `await self._db.execute(select(...))` loops with direct attribute access:

```python
# BEFORE (N+1):
for pdp in product.product_dietary_profiles:
    dp_result = await self._db.execute(
        select(DietaryProfile).where(DietaryProfile.id == pdp.dietary_profile_id)
    )
    dp = dp_result.scalar_one_or_none()
    if dp:
        dietary_codes.append(dp.code)

# AFTER (zero queries):
for pdp in product.product_dietary_profiles:
    if pdp.dietary_profile:
        dietary_codes.append(pdp.dietary_profile.code)
```

Same refactor for: cooking methods (`pcm.cooking_method`), badges (`pb.badge`), seals (`ps.seal`), and cross-reactions (`a.all_cross_reactions`).

Remove all inline `from shared.models.X import X` imports inside the loops -- move them to the top of the file.

### Query count reduction

| Method | Before | After |
|--------|--------|-------|
| `_build_menu` (10 products) | ~1 + 10*4 = 41 queries | 1 query (8 selectinloads) |
| `_build_product_detail` | ~1 + N(allergens)*1 + 4 = ~8 queries | 1 query |
| `_build_allergens` (14 allergens) | ~1 + 14*1 = 15 queries | 1 query (2 selectinloads) |

---

## D4 -- Dashboard Route Audit

### Current State (verified)

All routes, pages, and services already exist:

**Routes** (`dashboard/src/router/routes.ts`): All 10 menu-domain routes defined -- `ALLERGENS`, `DIETARY_PROFILES`, `COOKING_METHODS`, `BADGES`, `SEALS`, `PRODUCTS`, etc.

**Router** (`dashboard/src/router/index.tsx`): All pages are lazy-imported and registered with correct paths. Allergens, DietaryProfiles, CookingMethods, Badges, Seals are tenant-scoped (no BranchGuard). Products, Categories, Subcategories are branch-scoped (under BranchGuard).

**Pages** (`dashboard/src/pages/`): All 12 page files exist -- `AllergensPage.tsx`, `BadgesPage.tsx`, `CookingMethodsPage.tsx`, `DietaryProfilesPage.tsx`, `SealsPage.tsx`, `ProductsPage.tsx`, etc.

**Services** (`dashboard/src/services/`): All service files exist -- `allergen.service.ts`, `badge.service.ts`, `cooking-method.service.ts`, `dietary-profile.service.ts`, `seal.service.ts`, `product.service.ts`, `batch-price.service.ts`.

### Verdict

**No changes needed.** W8 is already resolved. The implementation task should verify this is still true at apply time (files could drift), but as of now, all dashboard routes, pages, and services are in place.

If during apply any file is found missing, the pattern to follow is:
- Pages: Copy structure from an existing page (e.g., `AllergensPage.tsx`) and adapt
- Services: Follow the pattern in `allergen.service.ts` (TanStack-Query-style hooks wrapping `apiClient`)
- Routes: Add to `routes.ts` constants AND `index.tsx` router tree

---

## D5 -- Test Architecture

### Test Framework (from conftest.py)

- `pytest-asyncio` with `asyncio_mode = "auto"` (implicit async)
- Real PostgreSQL via `TEST_DATABASE_URL` (env var or falls back to `DATABASE_URL`)
- Schema is dropped/recreated per test (via `db_session` fixture)
- Redis mocked via `mock_redis` fixture (AsyncMock with pipeline support)
- HTTP client: `httpx.AsyncClient` with `ASGITransport` wrapping the FastAPI app
- Auth: `auth_headers(role)` generates real JWTs; `authenticated_client` fixture pre-sets ADMIN headers

### Rate Limiter Handling in Tests

The global `limiter` uses in-memory storage. For most tests, this is fine. For the rate-limit-specific test, we need to:
1. Reset the limiter state between tests (or use a fresh app instance, which `app` fixture already does)
2. Fire 61 requests in a loop and assert the 61st returns HTTP 429

For tests that are NOT testing rate limiting but hit rate-limited endpoints repeatedly, we should disable the limiter in the `app` fixture by adding:

```python
from rest_api.app.middleware.rate_limit import limiter
application.state.limiter = limiter  # already done in main.py
limiter.enabled = False  # disable for non-rate-limit tests
```

Then in the rate limit test file, re-enable it explicitly:

```python
@pytest.fixture
def enable_rate_limit(app):
    from rest_api.app.middleware.rate_limit import limiter
    limiter.enabled = True
    yield
    limiter.enabled = False
```

### New Test Files

#### `tests/test_allergens.py` (S1-S3)

Covers: allergen CRUD, system allergen protection, cross-reactions.

Fixtures needed in conftest:
```python
@pytest_asyncio.fixture
async def seed_tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant."""

@pytest_asyncio.fixture
async def seed_branch(db_session: AsyncSession, seed_tenant: Tenant) -> Branch:
    """Create a test branch."""

@pytest_asyncio.fixture
async def seed_allergens(db_session: AsyncSession) -> list[Allergen]:
    """Create system allergens (at least gluten, dairy, peanuts, tree_nuts)."""
```

Test cases:
- `test_create_allergen` -- POST allergen as ADMIN, verify 201
- `test_system_allergen_cannot_be_deleted` -- DELETE system allergen returns 403/400
- `test_cross_reactions_bidirectional` -- Create cross-reaction, query from both sides

#### `tests/test_products.py` (S4-S5, S9, S14-S15)

Covers: product creation, allergen assignment, free_of validation, branch exclusion, badges.

Fixtures:
```python
@pytest_asyncio.fixture
async def seed_product(db_session, seed_tenant, seed_branch) -> Product:
    """Create a product linked to the test branch."""
```

Test cases:
- `test_create_product_with_allergens` -- POST product with allergen assignments
- `test_free_of_requires_low_risk` -- POST with `presence_type=free_of` + `risk_level=severe` returns 400/422
- `test_product_branch_exclusion` -- Product not in branch_products is excluded from menu
- `test_assign_badges_to_product` -- POST badge assignment, verify in product detail
- `test_assign_seals_to_product` -- POST seal assignment, verify in product detail

#### `tests/test_public_menu.py` (S6-S8, S13)

Covers: dietary filtering, allergen-free filtering, per-branch pricing, rate limiting.

Fixtures: Reuse `seed_tenant`, `seed_branch`, `seed_product`, `seed_allergens`.

Test cases:
- `test_menu_dietary_filter` -- GET menu with `?dietary=vegan`, verify only vegan products returned
- `test_menu_allergen_free_filter` -- GET menu with `?allergen_free=gluten`, verify gluten products excluded
- `test_menu_branch_pricing` -- Product with branch-specific price shows that price, not base_price
- `test_public_menu_rate_limit` (uses `enable_rate_limit` fixture) -- Fire 61 GET requests to `/api/public/menu/{slug}`, assert request 61 returns 429

#### `tests/test_batch_price.py` (S10-S11)

Covers: batch price preview, apply, negative price clamping.

Test cases:
- `test_batch_price_preview` -- POST preview with percentage adjustment, verify calculated prices without DB change
- `test_batch_price_apply` -- POST apply, verify branch_products updated
- `test_batch_price_negative_clamp` -- Apply large negative adjustment, verify prices clamped to 0 (not negative)

#### `tests/test_cache_invalidation.py` (S12)

Covers: cache key patterns, invalidation on data change.

Test cases:
- `test_cache_key_pattern` -- GET menu twice, verify second call uses cache (mock_redis.get returns cached data)
- `test_cache_invalidated_on_product_update` -- Update product, verify relevant cache keys deleted
- `test_cache_invalidated_on_allergen_update` -- Update allergen, verify allergen cache key deleted

### Async Pattern

All test functions are plain `async def` (no `@pytest.mark.asyncio` needed due to `asyncio_mode = "auto"`). All fixtures use `@pytest_asyncio.fixture`.

### Fixture Dependency Chain

```
db_session
  |-- mock_redis
  |     |
  |-- app(db_session, mock_redis)
  |     |-- client(app)
  |     |     |-- authenticated_client(client)
  |
  |-- seed_tenant(db_session)
  |     |-- seed_branch(db_session, seed_tenant)
  |     |     |-- seed_product(db_session, seed_tenant, seed_branch)
  |     |-- seed_allergens(db_session)
```

All `seed_*` fixtures create real DB rows via the session, then `safe_commit`. They are available to both direct DB tests and HTTP client tests (since `app` overrides `get_db` to return the same session).
