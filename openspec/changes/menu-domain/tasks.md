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
- [ ] All 6 enums defined as `str, Enum` subclasses
- [ ] Values match spec exactly (lowercase snake_case)
- [ ] Existing enums not modified

### Task 1.2: Allergen Model + Migration
**Description**: Create Allergen SQLAlchemy model and Alembic migration with EU 14 seed data.
**Files**:
- `rest_api/models/allergen.py` — `Allergen` model with all columns from design
- `rest_api/models/__init__.py` — Export new model
- `alembic/versions/xxx_create_allergens_table.py` — Create table + INSERT 14 EU allergens
**Acceptance Criteria**:
- [ ] `Allergen` model matches design schema exactly (id, code, name, description, icon, is_system, tenant_id, created_at, updated_at, deleted_at)
- [ ] AuditMixin applied (created_at, updated_at, deleted_at)
- [ ] UniqueConstraint on (code, tenant_id)
- [ ] CheckConstraint: is_system=FALSE OR tenant_id IS NULL
- [ ] Indexes: idx_allergens_tenant (filtered), idx_allergens_code (filtered)
- [ ] Migration seeds 14 EU allergens with correct codes: gluten, dairy, eggs, fish, crustaceans, tree_nuts, soy, celery, mustard, sesame, sulfites, lupins, mollusks, peanuts
- [ ] Each seeded allergen has: Spanish name, Spanish description, icon identifier, is_system=True, tenant_id=None

### Task 1.3: Allergen Cross-Reaction Model + Migration
**Description**: Create AllergenCrossReaction model with seed data for known cross-reactions.
**Files**:
- `rest_api/models/allergen.py` — Add `AllergenCrossReaction` class
- `alembic/versions/xxx_create_allergen_cross_reactions.py`
**Acceptance Criteria**:
- [ ] Model: id, allergen_id (FK), related_allergen_id (FK), description, severity, created_at
- [ ] UniqueConstraint on (allergen_id, related_allergen_id)
- [ ] CheckConstraint: allergen_id < related_allergen_id (canonical ordering)
- [ ] Indexes on allergen_id and related_allergen_id
- [ ] Bidirectional relationships on Allergen: cross_reactions_as_source, cross_reactions_as_related
- [ ] `all_cross_reactions` property returns union of both directions
- [ ] Seed known cross-reactions: peanuts↔tree_nuts, peanuts↔soy, peanuts↔lupins, fish↔crustaceans, dairy↔soy, gluten↔celery (with descriptions and severity levels)

### Task 1.4: Product-Allergen Model + Migration
**Description**: Create ProductAllergen junction table.
**Files**:
- `rest_api/models/product_allergen.py` — `ProductAllergen` model
- `rest_api/models/__init__.py` — Export
- `alembic/versions/xxx_create_product_allergens.py`
**Acceptance Criteria**:
- [ ] Model: id, product_id (FK), allergen_id (FK), presence_type (enum), risk_level (enum), notes, created_at, updated_at
- [ ] UniqueConstraint on (product_id, allergen_id)
- [ ] CheckConstraint: presence_type != 'free_of' OR risk_level = 'low'
- [ ] Indexes on product_id and allergen_id
- [ ] Relationships: product (back_populates), allergen (back_populates)

### Task 1.5: Dietary Profile Model + Migration
**Description**: Create DietaryProfile and ProductDietaryProfile.
**Files**:
- `rest_api/models/dietary_profile.py` — `DietaryProfile`, `ProductDietaryProfile`
- `alembic/versions/xxx_create_dietary_profiles.py`
**Acceptance Criteria**:
- [ ] DietaryProfile: id, code, name, description, icon, is_system, tenant_id, timestamps, soft delete
- [ ] Same constraints pattern as Allergen (unique code+tenant, system check)
- [ ] ProductDietaryProfile: composite PK (product_id, dietary_profile_id)
- [ ] Index on dietary_profile_id
- [ ] Seed 7 system profiles: vegetarian (Vegetariano), vegan (Vegano), gluten_free (Sin gluten), dairy_free (Sin lácteos), celiac_safe (Apto celíacos), keto (Keto), low_sodium (Bajo sodio)

### Task 1.6: Cooking Method Model + Migration
**Description**: Create CookingMethod and ProductCookingMethod.
**Files**:
- `rest_api/models/cooking_method.py` — `CookingMethod`, `ProductCookingMethod`
- `alembic/versions/xxx_create_cooking_methods.py`
**Acceptance Criteria**:
- [ ] Same pattern as DietaryProfile
- [ ] Seed 10 system methods: grill (Parrilla), oven (Horno), fryer (Fritura), steam (Vapor), raw (Crudo), sous_vide (Sous vide), smoke (Ahumado), saute (Salteado), boil (Hervido), roast (Asado)

### Task 1.7: Product Extended Columns (Flavor + Texture)
**Description**: Add ARRAY columns to existing Product model.
**Files**:
- `rest_api/models/product.py` — Add `flavor_profiles` and `texture_profiles` columns
- `alembic/versions/xxx_alter_products_add_flavor_texture.py`
**Acceptance Criteria**:
- [ ] `flavor_profiles`: ARRAY(String(20)), default empty list
- [ ] `texture_profiles`: ARRAY(String(20)), default empty list
- [ ] Migration is ALTER TABLE ADD COLUMN (not recreate)
- [ ] Existing product data unaffected

### Task 1.8: Product Ingredient Model + Migration
**Description**: Create ProductIngredient table.
**Files**:
- `rest_api/models/product_ingredient.py` — `ProductIngredient`
- `alembic/versions/xxx_create_product_ingredients.py`
**Acceptance Criteria**:
- [ ] Model: id, product_id (FK), ingredient_id (FK nullable), name (str 200), quantity (Decimal 10,3), unit (enum), sort_order (int), is_optional (bool), notes, timestamps
- [ ] UniqueConstraint on (product_id, sort_order)
- [ ] CheckConstraint: quantity > 0
- [ ] Index on product_id
- [ ] Relationship: product (back_populates), ordered by sort_order

### Task 1.9: BranchProduct Model + Migration
**Description**: Create branch_products junction table for pricing and availability.
**Files**:
- `rest_api/models/branch_product.py` — `BranchProduct`
- `alembic/versions/xxx_create_branch_products.py`
**Acceptance Criteria**:
- [ ] Model: id, branch_id (FK), product_id (FK), is_active (bool default True), price_cents (int nullable), sort_order (int default 0), timestamps
- [ ] UniqueConstraint on (branch_id, product_id)
- [ ] CheckConstraint: price_cents IS NULL OR price_cents >= 0
- [ ] Filtered index on branch_id WHERE is_active = TRUE
- [ ] `effective_price_cents` property: returns price_cents ?? product.base_price_cents
- [ ] Relationships: branch, product

### Task 1.10: Badge Model + Migration
**Description**: Create Badge, ProductBadge tables with seed data.
**Files**:
- `rest_api/models/badge.py` — `Badge`, `ProductBadge`
- `alembic/versions/xxx_create_badges.py`
**Acceptance Criteria**:
- [ ] Badge: id, code, name, color (str 7), icon, is_system, tenant_id, timestamps, soft delete
- [ ] ProductBadge: composite PK (product_id, badge_id), sort_order
- [ ] Seed 4: new/Nuevo/#22C55E, best_seller/Más vendido/#F59E0B, chef_recommends/Chef recomienda/#8B5CF6, on_sale/Oferta/#EF4444
- [ ] Same constraint pattern as Allergen

### Task 1.11: Seal Model + Migration
**Description**: Create Seal, ProductSeal tables with seed data.
**Files**:
- `rest_api/models/seal.py` — `Seal`, `ProductSeal`
- `alembic/versions/xxx_create_seals.py`
**Acceptance Criteria**:
- [ ] Same pattern as Badge
- [ ] Seed 6: organic/Orgánico/#16A34A, local/Producto local/#2563EB, preservative_free/Sin conservantes/#D97706, artisan/Artesanal/#9333EA, sustainable/Sustentable/#059669, fair_trade/Comercio justo/#0891B2

### Task 1.12: Update Product Model Relationships
**Description**: Add all new relationships to existing Product model.
**Files**:
- `rest_api/models/product.py` — Add relationship declarations
**Acceptance Criteria**:
- [ ] Added relationships: allergens (ProductAllergen list), dietary_profiles (via secondary), cooking_methods (via secondary), ingredients (ordered by sort_order), branch_products, badges (via secondary, ordered), seals (via secondary, ordered)
- [ ] All back_populates correctly wired
- [ ] cascade="all, delete-orphan" on owned relationships (allergens, ingredients)

---

## Phase 2: Backend Services (Repositories + Services)

### Task 2.1: Allergen Repository
**Description**: CRUD repository for allergens with tenant scoping.
**Files**:
- `rest_api/repositories/allergen_repository.py`
**Acceptance Criteria**:
- [ ] `get_all(tenant_id)` — returns system + tenant allergens, excludes soft-deleted
- [ ] `get_by_id(id, tenant_id)` — with tenant scope check
- [ ] `get_by_code(code, tenant_id)` — lookup by code
- [ ] `create(data)` — validates not system code conflict
- [ ] `update(id, data)` — blocks update on is_system=True
- [ ] `soft_delete(id)` — blocks delete on is_system=True
- [ ] `get_cross_reactions(allergen_id)` — bidirectional query

### Task 2.2: Allergen Service
**Description**: Business logic for allergen management.
**Files**:
- `rest_api/services/allergen_service.py`
**Acceptance Criteria**:
- [ ] CRUD operations delegating to repository
- [ ] Validation: system allergens immutable
- [ ] Cross-reaction management: create, delete, list for allergen
- [ ] Cross-reaction validation: allergen_id < related_allergen_id enforcement (swap if needed)
- [ ] Duplicate cross-reaction prevention

### Task 2.3: Allergen Router (Dashboard)
**Description**: Dashboard CRUD endpoints for allergens.
**Files**:
- `rest_api/routers/dashboard/allergens_router.py`
**Acceptance Criteria**:
- [ ] `GET /api/dashboard/allergens` — list with pagination, search by name/code
- [ ] `GET /api/dashboard/allergens/{id}` — detail with cross-reactions
- [ ] `POST /api/dashboard/allergens` — create custom allergen
- [ ] `PUT /api/dashboard/allergens/{id}` — update (blocked for system)
- [ ] `DELETE /api/dashboard/allergens/{id}` — soft delete (blocked for system)
- [ ] `GET /api/dashboard/allergens/{id}/cross-reactions` — list cross-reactions
- [ ] `POST /api/dashboard/allergens/{id}/cross-reactions` — add cross-reaction
- [ ] `DELETE /api/dashboard/allergens/cross-reactions/{id}` — remove cross-reaction
- [ ] All endpoints require auth + tenant context + ADMIN or MANAGER role

### Task 2.4: Dietary Profile Repository + Service + Router
**Description**: Full CRUD stack for dietary profiles.
**Files**:
- `rest_api/repositories/dietary_profile_repository.py`
- `rest_api/services/dietary_profile_service.py`
- `rest_api/routers/dashboard/dietary_profiles_router.py`
**Acceptance Criteria**:
- [ ] Same pattern as allergen (system immutable, tenant scoped, soft delete)
- [ ] CRUD endpoints at `/api/dashboard/dietary-profiles`
- [ ] Pagination + search

### Task 2.5: Cooking Method Repository + Service + Router
**Description**: Full CRUD stack for cooking methods.
**Files**:
- `rest_api/repositories/cooking_method_repository.py`
- `rest_api/services/cooking_method_service.py`
- `rest_api/routers/dashboard/cooking_methods_router.py`
**Acceptance Criteria**:
- [ ] Same pattern as dietary profiles
- [ ] CRUD endpoints at `/api/dashboard/cooking-methods`

### Task 2.6: Badge Repository + Service + Router
**Description**: Full CRUD stack for badges.
**Files**:
- `rest_api/repositories/badge_repository.py`
- `rest_api/services/badge_service.py`
- `rest_api/routers/dashboard/badges_router.py`
**Acceptance Criteria**:
- [ ] Same pattern with color validation (hex format)
- [ ] CRUD endpoints at `/api/dashboard/badges`

### Task 2.7: Seal Repository + Service + Router
**Description**: Full CRUD stack for seals.
**Files**:
- `rest_api/repositories/seal_repository.py`
- `rest_api/services/seal_service.py`
- `rest_api/routers/dashboard/seals_router.py`
**Acceptance Criteria**:
- [ ] Same pattern as badges
- [ ] CRUD endpoints at `/api/dashboard/seals`

### Task 2.8: Product Extended Service
**Description**: Extend product service for allergen/dietary/cooking/ingredient/badge/seal assignment.
**Files**:
- `rest_api/services/product_extended_service.py`
**Acceptance Criteria**:
- [ ] `set_allergens(product_id, allergen_data_list)` — bulk upsert ProductAllergen records
- [ ] `set_dietary_profiles(product_id, profile_ids)` — replace all product dietary profiles
- [ ] `set_cooking_methods(product_id, method_ids)` — replace all
- [ ] `set_ingredients(product_id, ingredient_data_list)` — replace all, enforce sort_order
- [ ] `set_badges(product_id, badge_data_list)` — replace all with sort_order
- [ ] `set_seals(product_id, seal_data_list)` — replace all with sort_order
- [ ] `update_flavor_profiles(product_id, profiles)` — validate enum values
- [ ] `update_texture_profiles(product_id, profiles)` — validate enum values
- [ ] Validation: free_of → risk_level must be low
- [ ] All operations trigger cache invalidation

### Task 2.9: Product Extended Router Updates
**Description**: Extend existing product router with new endpoints.
**Files**:
- `rest_api/routers/dashboard/products_router.py` — Extend existing
**Acceptance Criteria**:
- [ ] `PUT /api/dashboard/products/{id}/allergens` — body: list of {allergen_id, presence_type, risk_level, notes}
- [ ] `PUT /api/dashboard/products/{id}/dietary-profiles` — body: {profile_ids: []}
- [ ] `PUT /api/dashboard/products/{id}/cooking-methods` — body: {method_ids: []}
- [ ] `PUT /api/dashboard/products/{id}/flavor-profiles` — body: {profiles: []}
- [ ] `PUT /api/dashboard/products/{id}/texture-profiles` — body: {profiles: []}
- [ ] `PUT /api/dashboard/products/{id}/ingredients` — body: list of ingredient data
- [ ] `PUT /api/dashboard/products/{id}/badges` — body: list of {badge_id, sort_order}
- [ ] `PUT /api/dashboard/products/{id}/seals` — body: list of {seal_id, sort_order}
- [ ] All return updated product with full relationships

### Task 2.10: BranchProduct Repository + Service
**Description**: Branch-product pricing and availability management.
**Files**:
- `rest_api/repositories/branch_product_repository.py`
- `rest_api/services/branch_product_service.py`
**Acceptance Criteria**:
- [ ] `get_by_branch(branch_id)` — all products for branch with effective prices
- [ ] `get_by_product(product_id)` — all branches for product with effective prices
- [ ] `upsert(branch_id, product_id, is_active, price_cents)` — create or update
- [ ] `bulk_upsert(product_id, branch_data_list)` — for product form submission
- [ ] `toggle_availability(branch_id, product_id, is_active)` — quick toggle
- [ ] `update_price(branch_id, product_id, price_cents)` — price update
- [ ] `auto_create_for_product(product_id, tenant_id)` — creates BranchProduct for all active branches
- [ ] Cache invalidation on all write operations

### Task 2.11: BranchProduct Router
**Description**: Dashboard endpoints for branch-product management.
**Files**:
- `rest_api/routers/dashboard/branch_products_router.py`
**Acceptance Criteria**:
- [ ] `GET /api/dashboard/products/{id}/branches` — branch pricing grid for a product
- [ ] `PUT /api/dashboard/products/{id}/branches` — bulk update branch pricing/availability
- [ ] `PATCH /api/dashboard/products/{id}/branches/{branch_id}/toggle` — toggle availability
- [ ] `PATCH /api/dashboard/products/{id}/branches/{branch_id}/price` — update single price

### Task 2.12: Batch Price Service + Router
**Description**: Batch price update with preview and apply.
**Files**:
- `rest_api/services/batch_price_service.py`
- `rest_api/routers/dashboard/batch_price_router.py`
**Acceptance Criteria**:
- [ ] `POST /api/dashboard/products/batch-price/preview` — preview calculation (no side effects)
- [ ] `POST /api/dashboard/products/batch-price/apply` — apply with confirmed=true, transactional
- [ ] Preview response: list of {productId, productName, branchId, branchName, oldPriceCents, newPriceCents}
- [ ] Apply response: {applied: int, auditLogIds: []}
- [ ] Validates max 500 products per batch
- [ ] Percentage rounding: round() to nearest integer
- [ ] Negative price clamp to 0
- [ ] Audit log entry for each price change
- [ ] Cache invalidation for affected branches

---

## Phase 3: Public API + Caching

### Task 3.1: Cache Service
**Description**: Redis cache abstraction with get_or_set and invalidation.
**Files**:
- `rest_api/services/cache_service.py`
**Acceptance Criteria**:
- [ ] `get_or_set(key, factory, ttl=300)` — check cache, compute if miss, store
- [ ] `invalidate_pattern(pattern)` — SCAN + DELETE (non-blocking)
- [ ] `invalidate_keys(*keys)` — direct DELETE
- [ ] Uses `orjson` for serialization (fast)
- [ ] Handles Redis connection failures gracefully (fallback to direct query)

### Task 3.2: Cache Invalidation Hooks
**Description**: Centralized invalidation logic triggered by service layer writes.
**Files**:
- `rest_api/services/cache_invalidation.py`
**Acceptance Criteria**:
- [ ] `on_product_change(product_id, tenant_id)` — invalidates menu and product caches
- [ ] `on_branch_change(branch_slug, tenant_slug)` — invalidates branch and menu caches
- [ ] `on_allergen_change(tenant_id, tenant_slug)` — invalidates allergen and menu caches
- [ ] `on_branch_product_change(branch_slug)` — invalidates menu and product caches
- [ ] `on_badge_or_seal_change(tenant_id)` — invalidates menu caches
- [ ] All methods use correct key patterns from spec

### Task 3.3: Public Menu Repository
**Description**: Optimized read-only queries for public API with eager loading.
**Files**:
- `rest_api/repositories/public_menu_repository.py`
**Acceptance Criteria**:
- [ ] `get_branch_menu(branch_slug, filters)` — full menu query with joinedload/selectinload
- [ ] `get_product_detail(branch_slug, product_id)` — single product with all relations + cross-reactions
- [ ] `get_active_branches(tenant_slug)` — active branches with product/category counts
- [ ] `get_allergen_catalog(tenant_slug)` — all allergens with cross-reactions
- [ ] Dietary filter: AND logic (product must match ALL specified profiles)
- [ ] Allergen-free filter: excludes products with contains OR may_contain for specified allergens
- [ ] NO N+1 queries — verified via SQLAlchemy echo or query count assertion in tests
- [ ] Results filtered: only is_active=True BranchProducts, non-deleted products/branches

### Task 3.4: Public Menu Service
**Description**: Orchestrates caching + repository for public endpoints.
**Files**:
- `rest_api/services/public_menu_service.py`
**Acceptance Criteria**:
- [ ] `get_menu(branch_slug, filters)` — cache_key with query param hash, delegates to repo on miss
- [ ] `get_product(branch_slug, product_id)` — cached product detail
- [ ] `get_branches(tenant_slug)` — cached branch list
- [ ] `get_allergens(tenant_slug)` — cached allergen catalog
- [ ] All methods use CacheService.get_or_set with 300s TTL
- [ ] Response serialization uses camelCase (via Pydantic alias_generator)

### Task 3.5: Public API Routers
**Description**: Public endpoints (no auth required).
**Files**:
- `rest_api/routers/public/menu_router.py`
- `rest_api/routers/public/branches_router.py`
- `rest_api/routers/public/allergens_router.py`
- `rest_api/routers/public/__init__.py`
**Acceptance Criteria**:
- [ ] `GET /api/public/menu/{slug}` — query params: dietary, allergen_free, lang
- [ ] `GET /api/public/menu/{slug}/product/{id}` — full product detail
- [ ] `GET /api/public/branches?tenant={slug}` — active branches
- [ ] `GET /api/public/allergens?tenant={slug}` — allergen catalog
- [ ] No auth dependency on any public endpoint
- [ ] All responses include `Cache-Control: public, max-age=300` header
- [ ] Response schemas use camelCase field names
- [ ] 404 responses with descriptive detail messages

### Task 3.6: Rate Limiter Middleware
**Description**: IP-based rate limiting for public API.
**Files**:
- `rest_api/middleware/rate_limit.py`
**Acceptance Criteria**:
- [ ] Uses Redis INCR + EXPIRE (sliding window)
- [ ] 60 requests/minute per IP
- [ ] Returns 429 with Retry-After header when exceeded
- [ ] Applied as dependency on public router group only
- [ ] Handles Redis failure gracefully (allow request through)

### Task 3.7: Register Public Routers in App
**Description**: Wire public routers into FastAPI app.
**Files**:
- `rest_api/main.py` — Include public router group
**Acceptance Criteria**:
- [ ] Public routers mounted under `/api/public` prefix
- [ ] Rate limiter applied as group dependency
- [ ] No auth middleware on public routes
- [ ] CORS configured to allow public API access from any origin

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
- [ ] `AllergenCreate`: code, name, description?, icon?
- [ ] `AllergenUpdate`: name?, description?, icon?
- [ ] `AllergenResponse`: id, code, name, description, icon, isSystem, crossReactions[]
- [ ] `CrossReactionCreate`: relatedAllergenId, description, severity
- [ ] `CrossReactionResponse`: id, relatedAllergen (code, name), description, severity
- [ ] `ProductAllergenInput`: allergenId, presenceType, riskLevel, notes?
- [ ] Validators: free_of → risk_level must be low

### Task 5.2: Product Extended Schemas
**Files**: `rest_api/schemas/product_schemas.py` — Extend existing
**Acceptance Criteria**:
- [ ] Extended `ProductResponse`: add allergens, dietaryProfiles, cookingMethods, flavorProfiles, textureProfiles, ingredients, badges, seals, branchProducts
- [ ] `ProductIngredientInput`: name, quantity, unit, sortOrder, isOptional, notes?
- [ ] `BranchProductInput`: branchId, isActive, priceCents?
- [ ] `BadgeAssignInput`: badgeId, sortOrder
- [ ] `SealAssignInput`: sealId, sortOrder

### Task 5.3: Public API Schemas
**Files**: `rest_api/schemas/public_schemas.py`
**Acceptance Criteria**:
- [ ] All field names use camelCase (Pydantic `alias_generator = to_camel`)
- [ ] `PublicMenuResponse`: branch info, categories with products, allergenLegend, generatedAt
- [ ] `PublicProductResponse`: full product detail with allergens (including crossReactions), ingredients, dietary, cooking, flavor, texture, badges, seals
- [ ] `PublicBranchesResponse`: branches list with schedule, productCount, categoryCount
- [ ] `PublicAllergensResponse`: allergens with crossReactions
- [ ] All schemas have `model_config = ConfigDict(populate_by_name=True)` for camelCase

### Task 5.4: Batch Price Schemas
**Files**: `rest_api/schemas/batch_price_schemas.py`
**Acceptance Criteria**:
- [ ] `BatchPriceRequest`: productIds (list[int], max 500), operation (enum), amount (Decimal), branchId? (int)
- [ ] `BatchPricePreviewResponse`: changes[] with productId, productName, branchId, branchName, oldPriceCents, newPriceCents; totalProducts, totalBranches, totalChanges
- [ ] `BatchPriceApplyRequest`: extends BatchPriceRequest with confirmed (bool, must be true)
- [ ] `BatchPriceApplyResponse`: applied (int), auditLogIds (list[int])

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
