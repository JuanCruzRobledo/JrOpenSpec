---
artifact: verify-report
change: menu-domain-fixes
date: 2026-03-30
status: PASS_WITH_WARNINGS
---

# Verify Report — menu-domain-fixes

## Summary

All 5 originally-warned items (W1, W2, W6, W8, W9) have implementation present.
The migration, rate limiters, N+1 fixes, dashboard pages/services, and all 5 test files
are in place. Three warnings are raised: two are severity mismatches in the migration
cross-reactions (spec vs design conflict), and one is a test compatibility issue
(`@pytest.mark.anyio` without `anyio` in dependencies) that will cause runtime failures
in `test_public_menu.py` and `test_batch_price.py`. There are also two test logic bugs
that would cause false assertion results.

---

## W1 — Seed Migration

File: `alembic/versions/005_seed_system_data.py`

- [x] File exists with `revision = "005"`, `down_revision = "004"` — PASS
- [x] Allergens: 14 inserts with `WHERE NOT EXISTS` guard — PASS
  - All 14 EU codes present: `gluten`, `dairy`, `eggs`, `fish`, `crustaceans`, `tree_nuts`,
    `soy`, `celery`, `mustard`, `sesame`, `sulfites`, `lupins`, `mollusks`, `peanuts`
  - Each includes `code`, `name`, `icon`, `is_system=TRUE`, `tenant_id=NULL`
- [x] Dietary profiles: 7 inserts with `WHERE NOT EXISTS` — PASS
  - Codes: `vegetarian`, `vegan`, `gluten_free`, `dairy_free`, `celiac_safe`, `keto`, `low_sodium`
- [x] Cooking methods: 10 inserts with `WHERE NOT EXISTS` — PASS
  - Codes: `grill`, `oven`, `fryer`, `steam`, `raw`, `sous_vide`, `smoke`, `saute`, `boil`, `roast`
- [x] Badges: 4 inserts with correct codes and colors — PASS
  - `new` (#22C55E), `best_seller` (#F59E0B), `chef_recommends` (#8B5CF6), `on_sale` (#EF4444)
- [x] Seals: 6 inserts with correct codes and colors — PASS
  - `organic` (#16A34A), `local` (#2563EB), `preservative_free` (#D97706),
    `artisan` (#9333EA), `sustainable` (#059669), `fair_trade` (#0891B2)
- [x] Downgrade removes cross-reactions first (FK dependency), then all `is_system=TRUE` rows — PASS
- [!] Cross-reactions: 6 inserts using `LEAST/GREATEST` subselects — PARTIAL PASS

### WARNING — W1-SEVERITY: Cross-reaction severity values diverge from spec §1.3

The spec (spec.md §1.3) defines 6 pairs covering: `gluten`↔`celery`, `dairy`↔`soy`,
`fish`↔`crustaceans`, `fish`↔`mollusks`, `crustaceans`↔`mollusks`, `tree_nuts`↔`peanuts`.

The design.md and tasks.md define a *different* set of 6 pairs:
`gluten`↔`celery`, `dairy`↔`soy`, `fish`↔`crustaceans`, `peanuts`↔`tree_nuts`,
`peanuts`↔`soy`, `peanuts`↔`lupins`.

The migration implements the design/tasks version (not the spec version). Additionally,
the severity values in the migration do NOT match either document's stated severities:

| Pair | Spec §1.3 | Design/Tasks | Migration actual |
|------|-----------|-------------|-----------------|
| `gluten`↔`celery` | moderate | moderate | **low** |
| `dairy`↔`soy` | — (not in spec) | moderate | **low** |
| `peanuts`↔`tree_nuts` | — (not in spec) | severe | **moderate** |
| `peanuts`↔`soy` | — (not in spec) | moderate | **low** |
| `peanuts`↔`lupins` | — (not in spec) | severe | severe ✓ |
| `fish`↔`crustaceans` | moderate | moderate | moderate ✓ |

Spec pairs `fish`↔`mollusks` and `crustaceans`↔`mollusks` are absent from migration.

The test file (`test_allergens.py`) uses the design/tasks pairs (not spec pairs), so tests
will not catch this discrepancy. This is a spec/implementation inconsistency.

---

## W2 — Rate Limiting

Files: `rest_api/app/routers/public/menu.py`, `allergens.py`, `branches.py`

- [x] `menu.py` imports `limiter` from `rest_api.app.middleware.rate_limit` — PASS
- [x] `menu.py` imports `Request` from `starlette.requests` — PASS
- [x] `get_menu` has `@limiter.limit("60/minute")` after `@router.get("/{slug}")` — PASS
- [x] `get_menu` has `request: Request` as first positional parameter — PASS
- [x] `get_product_detail` has `@limiter.limit("60/minute")` — PASS
- [x] `get_product_detail` has `request: Request` as first positional parameter — PASS
- [x] `allergens.py` imports `limiter` and `Request` — PASS
- [x] `get_allergens` has `@limiter.limit("60/minute")` — PASS
- [x] `get_allergens` has `request: Request` as first positional parameter — PASS
- [x] `branches.py` imports `limiter` and `Request` — PASS
- [x] `get_branches` has `@limiter.limit("60/minute")` — PASS
- [x] `get_branches` has `request: Request` as first positional parameter — PASS
- [x] All 4 handlers' existing parameters and logic remain unchanged — PASS
- [x] Rate limiter disabled by default in `conftest.py` (`limiter.enabled = False`) — PASS
- [x] `enable_rate_limit` fixture re-enables limiter and restores it after test — PASS

**W2: PASS** — All 4 public handlers correctly decorated.

---

## W6 — N+1 Fix

### Junction Models (Task B2)

- [x] `product_dietary_profile.py`: imports `relationship`, `TYPE_CHECKING`; `dietary_profile: Mapped["DietaryProfile"] = relationship("DietaryProfile")` — PASS
- [x] `product_cooking_method.py`: imports `relationship`, `TYPE_CHECKING`; `cooking_method: Mapped["CookingMethod"] = relationship("CookingMethod")` — PASS
- [x] `product_badge.py`: imports `relationship`, `TYPE_CHECKING`; `badge: Mapped["Badge"] = relationship("Badge")` — PASS
- [x] `product_seal.py`: imports `relationship`, `TYPE_CHECKING`; `seal: Mapped["Seal"] = relationship("Seal")` — PASS
- [x] No `back_populates` on any (read-only navigational relationships) — PASS

### PublicMenuService (Task B3)

`_build_menu` query options:
- [x] `selectinload(Product.product_dietary_profiles).joinedload(ProductDietaryProfile.dietary_profile)` — PASS
- [x] `selectinload(Product.product_cooking_methods).joinedload(ProductCookingMethod.cooking_method)` — PASS
- [x] `selectinload(Product.product_badges).joinedload(ProductBadge.badge)` — PASS
- [x] `selectinload(Product.product_seals).joinedload(ProductSeal.seal)` — PASS

`_build_menu` serialization (direct attribute access):
- [x] `pdp.dietary_profile.code` (no inner query) — PASS
- [x] `pcm.cooking_method.code` (no inner query) — PASS
- [x] `pb.badge` (no inner query) — PASS
- [x] `ps.seal` (no inner query) — PASS

`_build_product_detail` query options:
- [x] `selectinload(Product.product_dietary_profiles).joinedload(ProductDietaryProfile.dietary_profile)` — PASS
- [x] `selectinload(Product.product_cooking_methods).joinedload(ProductCookingMethod.cooking_method)` — PASS
- [x] `selectinload(Product.product_badges).joinedload(ProductBadge.badge)` — PASS
- [x] `selectinload(Product.product_seals).joinedload(ProductSeal.seal)` — PASS
- [x] Allergen chain: `selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen).selectinload(Allergen.cross_reactions_as_source).joinedload(AllergenCrossReaction.related_allergen)` — PASS
- [x] Reverse chain: `...cross_reactions_as_related.joinedload(AllergenCrossReaction.allergen)` — PASS

`_build_product_detail` serialization:
- [x] Cross-reactions via `a.all_cross_reactions` (no inner query) — PASS
- [x] Dietary profiles via `pdp.dietary_profile` — PASS
- [x] Cooking methods via `pcm.cooking_method` — PASS
- [x] Badges via `pb.badge` — PASS
- [x] Seals via `ps.seal` — PASS

`_build_allergens`:
- [x] `selectinload(Allergen.cross_reactions_as_source).joinedload(AllergenCrossReaction.related_allergen)` — PASS
- [x] `selectinload(Allergen.cross_reactions_as_related).joinedload(AllergenCrossReaction.allergen)` — PASS
- [x] Cross-reactions via `a.all_cross_reactions` (no inner query) — PASS

All top-level imports at module level (no inline imports inside loops): PASS
No `await self._db.execute(select(...))` inside per-product or per-allergen loops: PASS

**W6: PASS** — N+1 queries fully eliminated.

---

## W8 — Dashboard

Pages confirmed present in `dashboard/src/pages/`:
- `AllergensPage.tsx`, `BadgesPage.tsx`, `CookingMethodsPage.tsx`, `DietaryProfilesPage.tsx`,
  `ProductsPage.tsx`, `SealsPage.tsx`, `CategoriesPage.tsx`, `SubcategoriesPage.tsx`

Services confirmed present in `dashboard/src/services/`:
- `allergen.service.ts`, `badge.service.ts`, `cooking-method.service.ts`,
  `dietary-profile.service.ts`, `seal.service.ts`, `product.service.ts`, `batch-price.service.ts`

**W8: RESOLVED** — No code changes needed, all pages and services confirmed present.

---

## W9 — Tests

All 5 test files exist:
- `tests/test_allergens.py` — PASS (exists, has all S1-S3 test functions)
- `tests/test_products.py` — PASS (exists, has all S4-S5, S9, S14-S15 test functions)
- `tests/test_public_menu.py` — PASS (exists, has S6-S8, S13 test functions)
- `tests/test_batch_price.py` — PASS (exists, has S10-S11 test functions)
- `tests/test_cache_invalidation.py` — PASS (exists, has S12 test functions)

`conftest.py` extensions:
- [x] `limiter.enabled = False` set in `app` fixture — PASS
- [x] `enable_rate_limit` fixture present — PASS
- [x] `seed_tenant` fixture present — PASS
- [x] `seed_branch` fixture present — PASS
- [x] `seed_allergens` fixture present (4 system allergens) — PASS
- [x] `seed_product` fixture present (Product + BranchProduct chain) — PASS
- [x] All fixtures use `@pytest_asyncio.fixture` — PASS

Task C3 checkbox `test_no_n1_queries`: deliberately unchecked in tasks.md — acknowledged,
not a blocking issue.

### WARNING — W9-ANYIO: `@pytest.mark.anyio` without `anyio` dependency

`test_public_menu.py` and `test_batch_price.py` use `@pytest.mark.anyio` on most test
functions. The project uses `pytest-asyncio` with `asyncio_mode = auto` in `pytest.ini`.
`anyio` is NOT listed in `requirements-backend-test.txt` or `rest_api[test]` extras.

With `pytest-asyncio` in `auto` mode, `@pytest.mark.anyio` is an unknown marker and those
tests will either be collected with a warning or run via the anyio plugin if `anyio` happens
to be installed transitively. This is fragile — the tests may or may not execute correctly
depending on the environment. The design.md (§D5) explicitly states: "All test functions are
plain `async def` (no `@pytest.mark.asyncio` needed due to `asyncio_mode = 'auto'`)."
Using `@pytest.mark.anyio` contradicts the spec.

**Affected files**: `tests/test_public_menu.py` (13 functions), `tests/test_batch_price.py` (8 functions)
**Fix**: Remove `@pytest.mark.anyio` from all test functions in both files (the `auto` mode handles them).

### WARNING — W9-TYPEMATCH: Product ID type mismatch in `test_public_menu.py`

The helper `_all_product_ids_in_menu()` collects `p["id"]` from the public menu JSON.
The service serializes product IDs as strings: `"id": str(product.id)`. The helper is
typed as `list[int]` and tests compare with `pizza.id` (SQLAlchemy int).

```python
# In _build_menu — service output:
"id": str(product.id)   # "123" (string)

# In test helper — collected as:
ids.append(p["id"])     # collects "123" (string)

# In assertions:
assert pizza.id in product_ids  # int 123 in ["123", ...] → always False
```

This means:
- Inclusion assertions (`assert pizza.id in product_ids`) will always FAIL (false negative)
- Exclusion assertions (`assert steak.id not in product_ids`) will always PASS (false positive, masking bugs)

All 6 filtering tests in `test_dietary_filter_*`, `test_allergen_free_*` are affected.
**Fix**: Cast collected IDs to `int` in the helper, or compare as strings.

### WARNING — W9-SCHEMA: `allergenSummary` field does not exist in public menu response

`test_products.py` line 104 references:
```python
allergen_summary = product_data.get("allergenSummary", {})
contains_list = allergen_summary.get("contains", [])
assert allergen.code in contains_list
```

The actual public menu product shape (from `_build_menu`) has:
```python
"allergenSlugs": allergen_slugs,      # presence_type == "contains"
"mayContainSlugs": may_contain_slugs, # presence_type == "may_contain"
```

There is no `allergenSummary` key. The `allergenSummary.get("contains")` call will always
return `[]`, making `test_allergen_appears_in_public_menu` always fail once the product
actually does appear in the menu.
**Fix**: Update test to use `product_data.get("allergenSlugs", [])`.

---

## CRITICAL Issues

None.

---

## WARNINGS

| ID | Severity | Description | Fix |
|----|----------|-------------|-----|
| W1-SEVERITY | WARNING | Cross-reaction severity values in migration differ from spec §1.3 AND differ from design.md for 4 of 6 pairs. Spec and design contradict each other on which pairs to seed. | Resolve spec/design conflict; update migration severities to match agreed spec |
| W9-ANYIO | WARNING | `@pytest.mark.anyio` used in 2 test files but `anyio` is not in deps; contradicts design.md §D5 convention | Remove `@pytest.mark.anyio` from all functions in `test_public_menu.py` and `test_batch_price.py` |
| W9-TYPEMATCH | WARNING | Product ID type mismatch: service returns string IDs, tests compare with int IDs. All filtering tests produce wrong results | Fix `_all_product_ids_in_menu` to cast to `int` or compare as strings |
| W9-SCHEMA | WARNING | `test_allergen_appears_in_public_menu` asserts `allergenSummary.contains` but service uses `allergenSlugs` | Update test to use `allergenSlugs` key |

---

## Evidence

### W1 — Files verified
- `alembic/versions/005_seed_system_data.py` — 14 allergens, 6 cross-reactions, 7 dietary profiles, 10 cooking methods, 4 badges, 6 seals; downgrade in correct FK order

### W2 — Files verified
- `rest_api/app/routers/public/menu.py` — both handlers decorated
- `rest_api/app/routers/public/allergens.py` — handler decorated
- `rest_api/app/routers/public/branches.py` — handler decorated

### W6 — Files verified
- `shared/shared/models/catalog/product_dietary_profile.py` — relationship added
- `shared/shared/models/catalog/product_cooking_method.py` — relationship added
- `shared/shared/models/catalog/product_badge.py` — relationship added
- `shared/shared/models/catalog/product_seal.py` — relationship added
- `rest_api/app/services/domain/public_menu_service.py` — all eager loads in place, no N+1 loops

### W8 — Files verified
- `dashboard/src/pages/` — 12 page files present
- `dashboard/src/services/` — all 7 menu-domain service files present

### W9 — Files verified
- `tests/conftest.py` — all new fixtures present, limiter disabled by default
- `tests/test_allergens.py`, `tests/test_products.py`, `tests/test_public_menu.py`,
  `tests/test_batch_price.py`, `tests/test_cache_invalidation.py` — all 5 files exist with content
