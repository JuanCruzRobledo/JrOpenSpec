---
sprint: 4
artifact: tasks
status: complete
---

# SDD Tasks — Sprint 4: Productos Avanzado y API Pública del Menú

## Status: APPROVED

---

## Phase 1: Database Foundation (Enums, Models, Migrations)

### Task 1.1: Shared Enums
**Description**: Create all new enums for Sprint 4.
**Files**:
- `shared/enums.py` — Add: `PresenceType`, `AllergenSeverity`, `IngredientUnit`, `FlavorProfile`, `TextureProfile`, `BatchPriceOperation`
**Acceptance Criteria**:
- [x] All 6 enums defined as `str, Enum` subclasses
- [x] Values match spec exactly (lowercase snake_case)
- [x] Existing enums not modified
> ⚠️ Enum names `FlavorProfileEnum`/`TextureProfileEnum` deviate from spec (`FlavorProfile`/`TextureProfile`)

### Task 1.2: Allergen Model + Migration
**Description**: Create Allergen SQLAlchemy model and Alembic migration with EU 14 seed data.
**Files**:
- `rest_api/models/allergen.py` — `Allergen` model with all columns from design
- `rest_api/models/__init__.py` — Export new model
- `alembic/versions/xxx_create_allergens_table.py` — Create table + INSERT 14 EU allergens
**Acceptance Criteria**:
- [x] `Allergen` model matches design schema exactly (id, code, name, description, icon, is_system, tenant_id, created_at, updated_at, deleted_at)
- [x] AuditMixin applied (created_at, updated_at, deleted_at)
- [x] UniqueConstraint on (code, tenant_id)
- [x] CheckConstraint: is_system=FALSE OR tenant_id IS NULL
- [x] Indexes: idx_allergens_tenant (filtered), idx_allergens_code (filtered)
- [ ] Migration seeds 14 EU allergens with correct codes: gluten, dairy, eggs, fish, crustaceans, tree_nuts, soy, celery, mustard, sesame, sulfites, lupins, mollusks, peanuts — ⚠️ seed is in `seed.py` (dev-only), not migration
- [ ] Each seeded allergen has: Spanish name, Spanish description, icon identifier, is_system=True, tenant_id=None — ⚠️ seed is in `seed.py` (dev-only), not migration

### Task 1.3: Allergen Cross-Reaction Model + Migration
**Description**: Create AllergenCrossReaction model with seed data for known cross-reactions.
**Files**:
- `rest_api/models/allergen.py` — Add `AllergenCrossReaction` class
- `alembic/versions/xxx_create_allergen_cross_reactions.py`
**Acceptance Criteria**:
- [x] Model: id, allergen_id (FK), related_allergen_id (FK), description, severity, created_at
- [x] UniqueConstraint on (allergen_id, related_allergen_id)
- [x] CheckConstraint: allergen_id < related_allergen_id (canonical ordering)
- [x] Indexes on allergen_id and related_allergen_id
- [x] Bidirectional relationships on Allergen: cross_reactions_as_source, cross_reactions_as_related
- [x] `all_cross_reactions` property returns union of both directions
- [ ] Seed known cross-reactions: peanuts↔tree_nuts, peanuts↔soy, peanuts↔lupins, fish↔crustaceans, dairy↔soy, gluten↔celery — ⚠️ seed is in `seed.py` (dev-only), not migration

### Task 1.4: Product-Allergen Model + Migration
**Description**: Create ProductAllergen junction table.
**Files**:
- `rest_api/models/product_allergen.py` — `ProductAllergen` model
- `rest_api/models/__init__.py` — Export
- `alembic/versions/xxx_create_product_allergens.py`
**Acceptance Criteria**:
- [x] Model: id, product_id (FK), allergen_id (FK), presence_type (enum), risk_level (enum), notes, created_at, updated_at
- [x] UniqueConstraint on (product_id, allergen_id)
- [x] CheckConstraint: presence_type != 'free_of' OR risk_level = 'low'
- [x] Indexes on product_id and allergen_id
- [x] Relationships: product (back_populates), allergen (back_populates)

### Task 1.5: Dietary Profile Model + Migration
**Description**: Create DietaryProfile and ProductDietaryProfile.
**Files**:
- `rest_api/models/dietary_profile.py` — `DietaryProfile`, `ProductDietaryProfile`
- `alembic/versions/xxx_create_dietary_profiles.py`
**Acceptance Criteria**:
- [x] DietaryProfile: id, code, name, description, icon, is_system, tenant_id, timestamps, soft delete
- [x] Same constraints pattern as Allergen (unique code+tenant, system check)
- [x] ProductDietaryProfile: composite PK (product_id, dietary_profile_id)
- [x] Index on dietary_profile_id
- [ ] Seed 7 system profiles: vegetarian, vegan, gluten_free, dairy_free, celiac_safe, keto, low_sodium — ⚠️ seed is in `seed.py` (dev-only), not migration

### Task 1.6: Cooking Method Model + Migration
**Description**: Create CookingMethod and ProductCookingMethod.
**Files**:
- `rest_api/models/cooking_method.py` — `CookingMethod`, `ProductCookingMethod`
- `alembic/versions/xxx_create_cooking_methods.py`
**Acceptance Criteria**:
- [x] Same pattern as DietaryProfile
- [ ] Seed 10 system methods: grill, oven, fryer, steam, raw, sous_vide, smoke, saute, boil, roast — ⚠️ seed is in `seed.py` (dev-only), not migration

### Task 1.7: Product Extended Columns (Flavor + Texture)
**Description**: Add ARRAY columns to existing Product model.
**Files**:
- `rest_api/models/product.py` — Add `flavor_profiles` and `texture_profiles` columns
- `alembic/versions/xxx_alter_products_add_flavor_texture.py`
**Acceptance Criteria**:
- [x] `flavor_profiles`: ARRAY(String(20)), default empty list
- [x] `texture_profiles`: ARRAY(String(20)), default empty list
- [x] Migration is ALTER TABLE ADD COLUMN (not recreate)
- [x] Existing product data unaffected

### Task 1.8: Product Ingredient Model + Migration
**Description**: Create ProductIngredient table.
**Files**:
- `rest_api/models/product_ingredient.py` — `ProductIngredient`
- `alembic/versions/xxx_create_product_ingredients.py`
**Acceptance Criteria**:
- [x] Model: id, product_id (FK), ingredient_id (FK nullable), name (str 200), quantity (Decimal 10,3), unit (enum), sort_order (int), is_optional (bool), notes, timestamps
- [x] UniqueConstraint on (product_id, sort_order)
- [x] CheckConstraint: quantity > 0
- [x] Index on product_id
- [x] Relationship: product (back_populates), ordered by sort_order

### Task 1.9: BranchProduct Model + Migration
**Description**: Create branch_products junction table for pricing and availability.
**Files**:
- `rest_api/models/branch_product.py` — `BranchProduct`
- `alembic/versions/xxx_create_branch_products.py`
**Acceptance Criteria**:
- [x] Model: id, branch_id (FK), product_id (FK), is_active/is_available (bool default True), price_cents (int nullable), sort_order (int default 0), timestamps — ⚠️ field named `is_available` not `is_active` per spec
- [x] UniqueConstraint on (branch_id, product_id)
- [x] CheckConstraint: price_cents IS NULL OR price_cents >= 0
- [x] Filtered index on branch_id (not filtered by is_active exactly, but functional)
- [x] `effective_price_cents` property: returns price_cents ?? product.base_price_cents
- [x] Relationships: branch, product

### Task 1.10: Badge Model + Migration
**Description**: Create Badge, ProductBadge tables with seed data.
**Files**:
- `rest_api/models/badge.py` — `Badge`, `ProductBadge`
- `alembic/versions/xxx_create_badges.py`
**Acceptance Criteria**:
- [x] Badge: id, code, name, color (str 7), icon, is_system, tenant_id, timestamps, soft delete
- [x] ProductBadge: composite PK (product_id, badge_id), sort_order
- [ ] Seed 4: new/Nuevo/#22C55E, best_seller/Más vendido/#F59E0B, chef_recommends/Chef recomienda/#8B5CF6, on_sale/Oferta/#EF4444 — ⚠️ seed is in `seed.py` (dev-only), not migration
- [x] Same constraint pattern as Allergen

### Task 1.11: Seal Model + Migration
**Description**: Create Seal, ProductSeal tables with seed data.
**Files**:
- `rest_api/models/seal.py` — `Seal`, `ProductSeal`
- `alembic/versions/xxx_create_seals.py`
**Acceptance Criteria**:
- [x] Same pattern as Badge
- [ ] Seed 6: organic, local, preservative_free, artisan, sustainable, fair_trade — ⚠️ seed is in `seed.py` (dev-only), not migration

### Task 1.12: Update Product Model Relationships
**Description**: Add all new relationships to existing Product model.
**Files**:
- `rest_api/models/product.py` — Add relationship declarations
**Acceptance Criteria**:
- [x] Added relationships: allergens (ProductAllergen list), dietary_profiles (via secondary), cooking_methods (via secondary), ingredients (ordered by sort_order), branch_products, badges (via secondary, ordered), seals (via secondary, ordered)
- [x] All back_populates correctly wired
- [x] cascade="all, delete-orphan" on owned relationships (allergens, ingredients)

---

## Phase 2: Backend Services (Repositories + Services)

### Task 2.1: Allergen Repository
**Description**: CRUD repository for allergens with tenant scoping.
**Files**:
- `rest_api/repositories/allergen_repository.py`
**Acceptance Criteria**:
- [x] `get_all(tenant_id)` — returns system + tenant allergens, excludes soft-deleted
- [x] `get_by_id(id, tenant_id)` — with tenant scope check
- [x] `get_by_code(code, tenant_id)` — lookup by code
- [x] `create(data)` — validates not system code conflict
- [x] `update(id, data)` — blocks update on is_system=True
- [x] `soft_delete(id)` — blocks delete on is_system=True
- [x] `get_cross_reactions(allergen_id)` — bidirectional query

### Task 2.2: Allergen Service
**Description**: Business logic for allergen management.
**Files**:
- `rest_api/services/allergen_service.py`
**Acceptance Criteria**:
- [x] CRUD operations delegating to repository
- [x] Validation: system allergens immutable
- [x] Cross-reaction management: create, delete, list for allergen
- [x] Cross-reaction validation: allergen_id < related_allergen_id enforcement (swap if needed)
- [x] Duplicate cross-reaction prevention

### Task 2.3: Allergen Router (Dashboard)
**Description**: Dashboard CRUD endpoints for allergens.
**Files**:
- `rest_api/routers/dashboard/allergens_router.py`
**Acceptance Criteria**:
- [x] `GET /api/dashboard/allergens` — list with pagination, search by name/code
- [x] `GET /api/dashboard/allergens/{id}` — detail with cross-reactions
- [x] `POST /api/dashboard/allergens` — create custom allergen
- [x] `PUT /api/dashboard/allergens/{id}` — update (blocked for system)
- [x] `DELETE /api/dashboard/allergens/{id}` — soft delete (blocked for system)
- [x] `GET /api/dashboard/allergens/{id}/cross-reactions` — list cross-reactions
- [x] `POST /api/dashboard/allergens/{id}/cross-reactions` — add cross-reaction
- [x] `DELETE /api/dashboard/allergens/cross-reactions/{id}` — remove cross-reaction
- [x] All endpoints require auth + tenant context + ADMIN or MANAGER role

### Task 2.4: Dietary Profile Repository + Service + Router
**Description**: Full CRUD stack for dietary profiles.
**Files**:
- `rest_api/repositories/dietary_profile_repository.py`
- `rest_api/services/dietary_profile_service.py`
- `rest_api/routers/dashboard/dietary_profiles_router.py`
**Acceptance Criteria**:
- [x] Same pattern as allergen (system immutable, tenant scoped, soft delete)
- [x] CRUD endpoints at `/api/dashboard/dietary-profiles`
- [x] Pagination + search

### Task 2.5: Cooking Method Repository + Service + Router
**Description**: Full CRUD stack for cooking methods.
**Files**:
- `rest_api/repositories/cooking_method_repository.py`
- `rest_api/services/cooking_method_service.py`
- `rest_api/routers/dashboard/cooking_methods_router.py`
**Acceptance Criteria**:
- [x] Same pattern as dietary profiles
- [x] CRUD endpoints at `/api/dashboard/cooking-methods`

### Task 2.6: Badge Repository + Service + Router
**Description**: Full CRUD stack for badges.
**Files**:
- `rest_api/repositories/badge_repository.py`
- `rest_api/services/badge_service.py`
- `rest_api/routers/dashboard/badges_router.py`
**Acceptance Criteria**:
- [x] Same pattern with color validation (hex format)
- [x] CRUD endpoints at `/api/dashboard/badges`

### Task 2.7: Seal Repository + Service + Router
**Description**: Full CRUD stack for seals.
**Files**:
- `rest_api/repositories/seal_repository.py`
- `rest_api/services/seal_service.py`
- `rest_api/routers/dashboard/seals_router.py`
**Acceptance Criteria**:
- [x] Same pattern as badges
- [x] CRUD endpoints at `/api/dashboard/seals`

### Task 2.8: Product Extended Service
**Description**: Extend product service for allergen/dietary/cooking/ingredient/badge/seal assignment.
**Files**:
- `rest_api/services/product_extended_service.py`
**Acceptance Criteria**:
- [x] `set_allergens(product_id, allergen_data_list)` — bulk upsert ProductAllergen records
- [x] `set_dietary_profiles(product_id, profile_ids)` — replace all product dietary profiles
- [x] `set_cooking_methods(product_id, method_ids)` — replace all
- [x] `set_ingredients(product_id, ingredient_data_list)` — replace all, enforce sort_order
- [x] `set_badges(product_id, badge_data_list)` — replace all with sort_order
- [x] `set_seals(product_id, seal_data_list)` — replace all with sort_order
- [x] `update_flavor_profiles(product_id, profiles)` — validate enum values
- [x] `update_texture_profiles(product_id, profiles)` — validate enum values
- [x] Validation: free_of → risk_level must be low
- [ ] All operations trigger cache invalidation — ⚠️ CacheInvalidator exists but not wired into ProductExtendedService

### Task 2.9: Product Extended Router Updates
**Description**: Extend existing product router with new endpoints.
**Files**:
- `rest_api/routers/dashboard/products_router.py` — Extend existing
**Acceptance Criteria**:
- [x] `PUT /api/dashboard/products/{id}/allergens`
- [x] `PUT /api/dashboard/products/{id}/dietary-profiles`
- [x] `PUT /api/dashboard/products/{id}/cooking-methods`
- [x] `PUT /api/dashboard/products/{id}/flavor-profiles`
- [x] `PUT /api/dashboard/products/{id}/texture-profiles`
- [x] `PUT /api/dashboard/products/{id}/ingredients`
- [x] `PUT /api/dashboard/products/{id}/badges`
- [x] `PUT /api/dashboard/products/{id}/seals`
- [x] All return updated product data

### Task 2.10: BranchProduct Repository + Service
**Description**: Branch-product pricing and availability management.
**Files**:
- `rest_api/repositories/branch_product_repository.py`
- `rest_api/services/branch_product_service.py`
**Acceptance Criteria**:
- [x] `get_by_branch(branch_id)` — all products for branch with effective prices
- [x] `get_by_product(product_id)` — all branches for product with effective prices
- [x] `upsert(branch_id, product_id, is_active, price_cents)` — create or update
- [x] `bulk_upsert(product_id, branch_data_list)` — for product form submission
- [x] `toggle_availability(branch_id, product_id, is_active)` — quick toggle
- [x] `update_price(branch_id, product_id, price_cents)` — price update
- [x] `auto_create_for_product(product_id, tenant_id)` — creates BranchProduct for all active branches
- [ ] Cache invalidation on all write operations — ⚠️ CacheInvalidator not wired into BranchProductService

### Task 2.11: BranchProduct Router
**Description**: Dashboard endpoints for branch-product management.
**Files**:
- `rest_api/routers/dashboard/branch_products_router.py`
**Acceptance Criteria**:
- [x] `GET /api/dashboard/products/{id}/branches` — branch pricing grid for a product
- [x] `PUT /api/dashboard/products/{id}/branches` — bulk update branch pricing/availability
- [x] `PATCH /api/dashboard/products/{id}/branches/{branch_id}/toggle` — toggle availability
- [x] `PATCH /api/dashboard/products/{id}/branches/{branch_id}/price` — update single price

### Task 2.12: Batch Price Service + Router
**Description**: Batch price update with preview and apply.
**Files**:
- `rest_api/services/batch_price_service.py`
- `rest_api/routers/dashboard/batch_price_router.py`
**Acceptance Criteria**:
- [x] `POST /api/dashboard/products/batch-price/preview` — preview calculation (no side effects)
- [x] `POST /api/dashboard/products/batch-price/apply` — apply with confirmed=true, transactional
- [x] Preview response: changes list with old/new prices
- [x] Apply response: {applied: int, auditLogIds: []}
- [x] Validates max 500 products per batch
- [x] Percentage rounding: round() to nearest integer
- [x] Negative price clamp to 0
- [x] Audit log entry for each price change (graceful fallback if AuditLog model absent)
- [ ] Cache invalidation for affected branches — ⚠️ not called from BatchPriceService.apply

---

## Phase 3: Public API + Caching

### Task 3.1: Cache Service
**Description**: Redis cache abstraction with get_or_set and invalidation.
**Files**:
- `rest_api/services/cache_service.py`
**Acceptance Criteria**:
- [x] `get_or_set(key, factory, ttl=300)` — check cache, compute if miss, store
- [x] `invalidate_pattern(pattern)` — SCAN + DELETE (non-blocking)
- [x] `invalidate_keys(*keys)` — direct DELETE
- [x] Uses `orjson` for serialization (fast, with stdlib fallback)
- [x] Handles Redis connection failures gracefully (fallback to direct query)

### Task 3.2: Cache Invalidation Hooks
**Description**: Centralized invalidation logic triggered by service layer writes.
**Files**:
- `rest_api/services/cache_invalidation.py`
**Acceptance Criteria**:
- [x] `on_product_change(product_id, tenant_id)` — invalidates menu and product caches
- [x] `on_branch_change(branch_slug, tenant_slug)` — invalidates branch and menu caches
- [x] `on_allergen_change(tenant_id, tenant_slug)` — invalidates allergen and menu caches
- [x] `on_branch_product_change(branch_slug)` — invalidates menu and product caches
- [x] `on_badge_or_seal_change(tenant_id)` — invalidates menu caches
- [x] All methods use correct key patterns from spec

### Task 3.3: Public Menu Repository
**Description**: Optimized read-only queries for public API with eager loading.
**Files**:
- `rest_api/repositories/public_menu_repository.py`
**Acceptance Criteria**:
- [x] `get_branch_menu(branch_slug, filters)` — full menu query with joinedload/selectinload
- [x] `get_product_detail(branch_slug, product_id)` — single product with all relations + cross-reactions
- [x] `get_active_branches(tenant_slug)` — active branches with product/category counts
- [x] `get_allergen_catalog(tenant_slug)` — all allergens with cross-reactions
- [x] Dietary filter: AND logic (product must match ALL specified profiles)
- [x] Allergen-free filter: excludes products with contains OR may_contain for specified allergens
- [ ] NO N+1 queries — ⚠️ N+1 present for dietary profiles and cooking methods (queried in loop)
- [x] Results filtered: only is_available=True BranchProducts, non-deleted products/branches

### Task 3.4: Public Menu Service
**Description**: Orchestrates caching + repository for public endpoints.
**Files**:
- `rest_api/services/public_menu_service.py`
**Acceptance Criteria**:
- [x] `get_menu(branch_slug, filters)` — cache_key with query param hash, delegates to repo on miss
- [x] `get_product(branch_slug, product_id)` — cached product detail
- [x] `get_branches(tenant_slug)` — cached branch list
- [x] `get_allergens(tenant_slug)` — cached allergen catalog
- [x] All methods use CacheService.get_or_set with 300s TTL
- [x] Response serialization uses camelCase (manual mapping in service, not Pydantic alias_generator)

### Task 3.5: Public API Routers
**Description**: Public endpoints (no auth required).
**Files**:
- `rest_api/routers/public/menu_router.py`
- `rest_api/routers/public/branches_router.py`
- `rest_api/routers/public/allergens_router.py`
- `rest_api/routers/public/__init__.py`
**Acceptance Criteria**:
- [x] `GET /api/public/menu/{slug}` — query params: dietary, allergen_free (lang missing — ⚠️)
- [x] `GET /api/public/menu/{slug}/product/{id}` — full product detail
- [x] `GET /api/public/branches?tenant={slug}` — active branches
- [x] `GET /api/public/allergens?tenant={slug}` — allergen catalog
- [x] No auth dependency on any public endpoint
- [x] All responses include `Cache-Control: public, max-age=300` header
- [x] Response schemas use camelCase field names (manual mapping)
- [x] 404 responses with descriptive detail messages

### Task 3.6: Rate Limiter Middleware
**Description**: IP-based rate limiting for public API.
**Files**:
- `rest_api/middleware/rate_limit.py`
**Acceptance Criteria**:
- [ ] Uses Redis INCR + EXPIRE (sliding window) — ⚠️ uses in-memory storage, not Redis
- [ ] 60 requests/minute per IP — ⚠️ global limiter set to 100/min; public menu/allergens/branches have no @limiter.limit decorator
- [x] Returns 429 with Retry-After header when exceeded (slowapi handler registered)
- [ ] Applied as dependency on public router group only — ⚠️ not applied to menu/allergens/branches routers
- [x] Handles Redis failure gracefully (allow request through)

### Task 3.7: Register Public Routers in App
**Description**: Wire public routers into FastAPI app.
**Files**:
- `rest_api/main.py` — Include public router group
**Acceptance Criteria**:
- [x] Public routers mounted under `/api/public` prefix
- [ ] Rate limiter applied as group dependency — ⚠️ not applied at group level
- [x] No auth middleware on public routes
- [x] CORS configured to allow public API access from any origin

---

## Phase 4: Dashboard Frontend

### Task 4.1: Allergen Zustand Store + API Client
**Description**: Frontend state management and API client for allergens.
**Files**:
- `dashboard/src/features/allergens/api/allergenApi.ts`
- `dashboard/src/features/allergens/hooks/useAllergens.ts`
**Acceptance Criteria**:
- [ ] API client: fetchAll, fetchById, create, update, delete, fetchCrossReactions, addCrossReaction, removeCrossReaction
- [ ] Zustand store: allergens list, loading/error state, CRUD actions
- [ ] Individual selectors only (no destructuring — React 19 convention)

### Task 4.2: Allergen List + Form Pages
**Description**: Dashboard pages for allergen management.
**Files**:
- `dashboard/src/features/allergens/pages/AllergenListPage.tsx`
- `dashboard/src/features/allergens/pages/AllergenFormPage.tsx`
- `dashboard/src/features/allergens/components/AllergenTable.tsx`
- `dashboard/src/features/allergens/components/AllergenForm.tsx`
- `dashboard/src/features/allergens/components/CrossReactionManager.tsx`
- `dashboard/src/features/allergens/components/AllergenBadge.tsx`
**Acceptance Criteria**:
- [ ] List page: searchable table, columns (icon, name, code, system/custom, actions), system allergens show lock icon
- [ ] Form page: create/edit with code, name, description, icon select. System allergens: read-only
- [ ] CrossReactionManager: shows existing cross-reactions, add new (allergen select + severity + description), remove
- [ ] AllergenBadge: small presentational component showing icon + name
- [ ] Container/presentational pattern enforced
- [ ] TailwindCSS 4 only, no inline styles

### Task 4.3: Product Form Tabs
**Description**: Tabbed product form with all new fields.
**Files**:
- `dashboard/src/features/products/components/ProductForm/ProductFormTabs.tsx`
- `dashboard/src/features/products/components/ProductForm/BasicInfoTab.tsx`
- `dashboard/src/features/products/components/ProductForm/AllergensTab.tsx`
- `dashboard/src/features/products/components/ProductForm/DietaryTab.tsx`
- `dashboard/src/features/products/components/ProductForm/CookingMethodsTab.tsx`
- `dashboard/src/features/products/components/ProductForm/FlavorTextureTab.tsx`
- `dashboard/src/features/products/components/ProductForm/IngredientsTab.tsx`
- `dashboard/src/features/products/components/ProductForm/BadgesSealsTab.tsx`
- `dashboard/src/features/products/components/ProductForm/BranchPricingTab.tsx`
**Acceptance Criteria**:
- [ ] TabContainer: 8 tabs with icons, responsive (scrollable on mobile)
- [ ] BasicInfoTab: name, short description, full description (textarea), category select, base price (cents input with $ format display)
- [ ] AllergensTab: table of available allergens. Checkbox to select → reveals presence_type dropdown (contains/may_contain/free_of), risk_level dropdown, notes textarea. Free_of auto-sets risk to low
- [ ] DietaryTab: chip/tag multiselect for dietary profiles
- [ ] CookingMethodsTab: chip/tag multiselect for cooking methods
- [ ] FlavorTextureTab: two groups of toggle chips (flavors, textures)
- [ ] IngredientsTab: sortable list (drag-and-drop or up/down buttons). Each row: name input, quantity number input, unit select, optional checkbox, notes. Add/remove row buttons
- [ ] BadgesSealsTab: two sections. Each shows available badges/seals as selectable cards with visual preview (color, icon, name)
- [ ] BranchPricingTab: toggle "Habilitar precios por sucursal". When enabled: grid with columns (branch name, active toggle, price input). When price is blank, shows base price as placeholder in gray

### Task 4.4: Product Form Hook + API
**Description**: Form state management for the extended product form.
**Files**:
- `dashboard/src/features/products/hooks/useProductForm.ts`
- `dashboard/src/features/products/api/productApi.ts` — Extend existing
**Acceptance Criteria**:
- [ ] useProductForm manages all tab states in a single form object
- [ ] Dirty tracking per tab (show unsaved indicator)
- [ ] Submit sends separate API calls per changed section (not one giant payload)
- [ ] API client: setAllergens, setDietaryProfiles, setCookingMethods, setFlavorProfiles, setTextureProfiles, setIngredients, setBadges, setSeals, setBranchPricing
- [ ] Optimistic updates with rollback on error

### Task 4.5: Batch Price Update UI
**Description**: Modal flow for batch price updates.
**Files**:
- `dashboard/src/features/products/components/BatchPriceModal.tsx`
- `dashboard/src/features/products/components/BatchPricePreview.tsx`
- `dashboard/src/features/products/hooks/useBatchPrice.ts`
- `dashboard/src/features/products/api/batchPriceApi.ts`
**Acceptance Criteria**:
- [ ] Modal triggered from product list toolbar when products are selected
- [ ] Step 1: Select operation (dropdown), enter amount, optionally select target branch
- [ ] Step 2: Preview table showing (product, branch, old price, new price, diff with color: green for increase, red for decrease)
- [ ] Step 3: Confirm button with summary text ("Actualizar X precios en Y sucursales")
- [ ] Loading states for preview and apply
- [ ] Success toast with count of applied changes
- [ ] Error handling with descriptive messages

### Task 4.6: Branch Availability Grid
**Description**: Toggle grid for managing product availability across branches.
**Files**:
- `dashboard/src/features/products/components/BranchAvailabilityGrid.tsx`
- `dashboard/src/features/products/hooks/useBranchProducts.ts`
- `dashboard/src/features/products/api/branchProductApi.ts`
**Acceptance Criteria**:
- [ ] Grid: rows = products (or branches depending on context), columns include toggle + price
- [ ] Toggle sends PATCH request immediately (no save button needed)
- [ ] Price input: debounced save (500ms after typing stops)
- [ ] Visual feedback: green/red toggle states, price changes highlighted briefly

### Task 4.7: Badge & Seal Management Pages
**Description**: CRUD pages for badges and seals.
**Files**:
- `dashboard/src/features/badges/pages/BadgeListPage.tsx`
- `dashboard/src/features/badges/components/BadgeTable.tsx`
- `dashboard/src/features/badges/components/BadgeForm.tsx`
- `dashboard/src/features/badges/components/BadgePreview.tsx`
- `dashboard/src/features/badges/api/badgeApi.ts`
- `dashboard/src/features/seals/pages/SealListPage.tsx`
- `dashboard/src/features/seals/components/SealTable.tsx`
- `dashboard/src/features/seals/components/SealForm.tsx`
- `dashboard/src/features/seals/components/SealPreview.tsx`
- `dashboard/src/features/seals/api/sealApi.ts`
**Acceptance Criteria**:
- [ ] Badge list: table with preview column (shows colored badge), system badges locked
- [ ] Badge form: name, code, color picker (hex), icon select, live preview
- [ ] Seal list/form: identical pattern to badges
- [ ] System badges/seals: read-only in form, no delete button

### Task 4.8: Dashboard Route Registration
**Description**: Add new routes to dashboard router.
**Files**:
- `dashboard/src/routes/index.tsx` or equivalent router config
**Acceptance Criteria**:
- [ ] `/dashboard/allergens` — AllergenListPage
- [ ] `/dashboard/allergens/new` — AllergenFormPage (create)
- [ ] `/dashboard/allergens/:id` — AllergenFormPage (edit)
- [ ] `/dashboard/badges` — BadgeListPage
- [ ] `/dashboard/badges/new` — BadgeFormPage (create)
- [ ] `/dashboard/badges/:id` — BadgeFormPage (edit)
- [ ] `/dashboard/seals` — SealListPage
- [ ] `/dashboard/seals/new` — SealFormPage (create)
- [ ] `/dashboard/seals/:id` — SealFormPage (edit)
- [ ] Product form route already exists; tabs are added to existing form
- [ ] Navigation sidebar updated with new entries under "Catálogo" section

---

## Phase 5: Pydantic Schemas (Request/Response)

### Task 5.1: Allergen Schemas
**Files**: `rest_api/schemas/allergen_schemas.py`
**Acceptance Criteria**:
- [x] `AllergenCreate`: code, name, description?, icon?
- [x] `AllergenUpdate`: name?, description?, icon?
- [x] `AllergenResponse`: id, code, name, description, icon, isSystem, crossReactions[]
- [x] `CrossReactionCreate`: relatedAllergenId, description, severity
- [x] `CrossReactionResponse`: id, relatedAllergen (code, name), description, severity
- [x] `ProductAllergenInput`: allergenId, presenceType, riskLevel, notes?
- [x] Validators: free_of → risk_level must be low

### Task 5.2: Product Extended Schemas
**Files**: `rest_api/schemas/product_schemas.py` — Extend existing
**Acceptance Criteria**:
- [x] Extended `ProductResponse` with allergens, dietary, cooking, flavor, texture, ingredients, badges, seals, branchProducts
- [x] `ProductIngredientInput`: name, quantity, unit, sortOrder, isOptional, notes?
- [x] `BranchProductInput`: branchId, isActive, priceCents?
- [x] `BadgeAssignInput`: badgeId, sortOrder
- [x] `SealAssignInput`: sealId, sortOrder

### Task 5.3: Public API Schemas
**Files**: `rest_api/schemas/public_schemas.py`
**Acceptance Criteria**:
- [ ] All field names use camelCase (Pydantic `alias_generator = to_camel`) — ⚠️ camelCase done via manual dict mapping, not Pydantic schemas
- [x] `PublicMenuResponse`: branch info, categories with products, allergenLegend, generatedAt
- [x] `PublicProductResponse`: full product detail with allergens (including crossReactions), ingredients, dietary, cooking, flavor, texture, badges, seals
- [x] `PublicBranchesResponse`: branches list with schedule, productCount, categoryCount
- [ ] `PublicAllergensResponse`: allergens with crossReactions
- [ ] All schemas have `model_config = ConfigDict(populate_by_name=True)` for camelCase

### Task 5.4: Batch Price Schemas
**Files**: `rest_api/schemas/batch_price_schemas.py`
**Acceptance Criteria**:
- [x] `BatchPriceRequest`: productIds (list[int], max 500), operation (enum), amount (Decimal), branchId? (int)
- [x] `BatchPricePreviewResponse`: changes[] with prices; totalProducts, totalBranches, totalChanges
- [x] `BatchPriceApplyRequest`: extends BatchPriceRequest with confirmed (bool, must be true)
- [x] `BatchPriceApplyResponse`: applied (int), auditLogIds (list[int])

---

## Phase 6: Testing

### Task 6.1: Allergen Unit Tests
**Files**: `tests/unit/test_allergen_service.py`
**Acceptance Criteria**:
- [ ] Test CRUD operations
- [ ] Test system allergen immutability (update/delete blocked)
- [ ] Test cross-reaction bidirectional query
- [ ] Test cross-reaction canonical ordering (allergen_id < related_allergen_id)

### Task 6.2: Product Extended Tests
**Files**: `tests/unit/test_product_extended_service.py`
**Acceptance Criteria**:
- [ ] Test allergen assignment with presence/risk validation
- [ ] Test free_of + non-low risk rejection
- [ ] Test dietary/cooking/ingredient/badge/seal assignment and replacement
- [ ] Test flavor/texture profile enum validation

### Task 6.3: Batch Price Tests
**Files**: `tests/unit/test_batch_price_service.py`
**Acceptance Criteria**:
- [ ] Test all 4 operations (fixed add/subtract, percentage increase/decrease)
- [ ] Test percentage rounding
- [ ] Test negative price clamping to 0
- [ ] Test max 500 products validation
- [ ] Test audit log creation
- [ ] Test preview vs apply (preview has no side effects)

### Task 6.4: BranchProduct Tests
**Files**: `tests/unit/test_branch_product_service.py`
**Acceptance Criteria**:
- [ ] Test effective price resolution (branch price vs fallback)
- [ ] Test availability toggle
- [ ] Test auto-creation for new products

### Task 6.5: Public Menu Integration Tests
**Files**: `tests/integration/test_public_menu_api.py`
**Acceptance Criteria**:
- [ ] Test full menu endpoint returns correct structure
- [ ] Test dietary filtering (AND logic)
- [ ] Test allergen-free filtering (excludes contains + may_contain)
- [ ] Test branch not found returns 404
- [ ] Test inactive products excluded
- [ ] Test effective pricing in response
- [ ] Test cache hit (second request faster, no DB query)
- [ ] Test cache invalidation on product update

### Task 6.6: Rate Limiter Tests
**Files**: `tests/unit/test_rate_limiter.py`
**Acceptance Criteria**:
- [ ] Test 60 requests pass
- [ ] Test request #61 returns 429
- [ ] Test Retry-After header present
- [ ] Test Redis failure allows request through

---

## Execution Order

1. Phase 1 (Tasks 1.1-1.12): Database foundation — sequential, migrations depend on each other
2. Phase 5 (Tasks 5.1-5.4): Pydantic schemas — can start after enums (1.1) done
3. Phase 2 (Tasks 2.1-2.12): Backend services — depends on Phase 1 models
4. Phase 3 (Tasks 3.1-3.7): Public API — depends on Phase 2 services
5. Phase 4 (Tasks 4.1-4.8): Frontend — can start after Phase 2 API contracts defined
6. Phase 6 (Tasks 6.1-6.6): Testing — alongside each phase

**Parallelization opportunities**:
- Phase 5 in parallel with late Phase 1
- Phase 4 tasks 4.1-4.2 in parallel with Phase 2 (API client mocked)
- Phase 6 tasks alongside their respective phases
- Within Phase 2: Tasks 2.1-2.7 (entity CRUDs) can be parallelized
- Within Phase 4: Tasks 4.1-4.2, 4.7 (entity pages) can be parallelized

---

## Next Recommended

→ `sdd-apply` (begin implementation in batches)
