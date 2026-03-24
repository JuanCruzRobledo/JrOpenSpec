---
sprint: 13
artifact: tasks
status: complete
---

# Tasks: Recetas, Ingredientes y Promociones

## Phase 1: Ingredient Catalog

### 1.1 Ingredient group model, migration & seed
- Create `IngredientGroup` SQLAlchemy model
- Create Alembic migration with unique constraint on name
- Create seed script for 7 predefined groups: Vegetales, Protenas, Lcteos, Cereales, Condimentos, Aceites, Otros
- **Files**: `app/models/ingredient_group.py`, `alembic/versions/xxx_add_ingredient_groups.py`, `app/seeds/ingredient_groups.py`
- **AC**: Migration runs clean; seed creates 7 groups idempotently; unique constraint enforced

### 1.2 Ingredient model & migration
- Create `Ingredient` and `SubIngredient` SQLAlchemy models
- Create Alembic migration with trigram index for name search, GIN index on allergens JSONB
- Unique constraint on (name, group_id)
- Self-reference prevention on sub_ingredients
- **Files**: `app/models/ingredient.py`, `alembic/versions/xxx_add_ingredients.py`
- **AC**: Migration runs clean; trigram search works; self-reference constraint prevents cycles

### 1.3 Ingredient schemas & service
- Create Pydantic schemas: `IngredientCreate`, `IngredientUpdate`, `IngredientResponse`, `SubIngredientCreate`
- Implement service: CRUD, search by name (trigram), filter by group/state, manage sub-ingredients
- Validate allergen values against enum, prevent circular sub-ingredient references
- **Files**: `app/schemas/ingredient.py`, `app/services/ingredient_service.py`
- **AC**: CRUD works; search returns partial matches; sub-ingredient cycles detected and rejected

### 1.4 Ingredient REST endpoints
- CRUD for groups: POST/GET /api/ingredient-groups, PUT/DELETE /api/ingredient-groups/{id}
- CRUD for ingredients: POST/GET /api/ingredients, GET/PUT/DELETE /api/ingredients/{id}
- Sub-ingredients: POST/GET/DELETE /api/ingredients/{id}/sub-ingredients
- RBAC: ADMIN only for all endpoints
- **Files**: `app/routers/ingredients.py`
- **AC**: All CRUD operations work; RBAC enforced; search + filter query params work

## Phase 2: Recipe System

### 2.1 Recipe model & migration
- Create `Recipe`, `RecipeIngredient`, `RecipeStep` SQLAlchemy models
- Generated column for total_time_minutes
- Unique constraint on (recipe_id, step_number)
- **Files**: `app/models/recipe.py`, `alembic/versions/xxx_add_recipes.py`
- **AC**: Migration runs clean; total_time auto-calculated; step numbers unique per recipe

### 2.2 Recipe schemas
- Create Pydantic schemas: `RecipeCreate`, `RecipeUpdate`, `RecipeResponse`, `RecipeIngredientCreate`, `RecipeStepCreate`
- Nested validation: ingredients must reference valid ingredient IDs, steps must be sequential
- **Files**: `app/schemas/recipe.py`
- **AC**: Schema validates nested arrays; step numbers validated as sequential; ingredient IDs validated

### 2.3 Recipe service with auto-derivation
- Implement `create_recipe()`:
  - Save recipe + ingredients + steps in transaction
  - Auto-derive allergens: union of all ingredient allergens
  - Auto-derive celiac_safe: false if any ingredient has GLUTEN allergen
  - Auto-calculate production_cost: sum(ingredient.cost_per_unit * quantity)
  - Auto-calculate cost_per_serving: production_cost / servings
- Implement `update_recipe()`: recalculate derived fields on any change
- **Files**: `app/services/recipe_service.py`
- **AC**: Allergens correctly derived; celiac_safe accurate; cost calculations correct; all auto-fields update on edit

### 2.4 Recipe REST endpoints
- POST /api/branches/{branchId}/recipes — create with full body
- GET /api/branches/{branchId}/recipes — list with search/filter
- GET /api/branches/{branchId}/recipes/{id} — full detail
- PUT /api/branches/{branchId}/recipes/{id} — update
- DELETE /api/branches/{branchId}/recipes/{id} — archive (soft)
- RBAC: ADMIN only
- **Files**: `app/routers/recipes.py`
- **AC**: Full CRUD works; search by name + filter by difficulty/cuisine; auto-derived fields in response

## Phase 3: Promotion Types

### 3.1 Promotion type model, migration & seed
- Create `PromotionType` SQLAlchemy model
- Create migration + seed for 4 predefined types:
  - HAPPY_HOUR (requires_combo_price=false)
  - COMBO_FAMILIAR (requires_combo_price=true)
  - DOS_POR_UNO (requires_combo_price=true)
  - DESCUENTO (requires_combo_price=false)
- **Files**: `app/models/promotion_type.py`, `alembic/versions/xxx_add_promotion_types.py`, `app/seeds/promotion_types.py`
- **AC**: Migration + seed run clean; predefined types not deletable; custom types soft-deletable

### 3.2 Promotion type schemas, service & endpoints
- CRUD schemas + service + endpoints
- Validation: predefined types cannot be deleted; name unique
- **Files**: `app/schemas/promotion_type.py`, `app/services/promotion_type_service.py`, `app/routers/promotion_types.py`
- **AC**: CRUD works; predefined deletion returns 403; name uniqueness enforced

## Phase 4: Promotions

### 4.1 Promotion model & migration
- Create `Promotion`, `PromotionBranch`, `PromotionProduct` models
- Migration with date check constraint, indexes on dates and enabled
- **Files**: `app/models/promotion.py`, `alembic/versions/xxx_add_promotions.py`
- **AC**: Migration runs clean; date constraint prevents end < start; indexes created

### 4.2 Promotion service with temporal validation
- Implement `create_promotion()`:
  - Validate combo_price required if type.requires_combo_price
  - Validate combo_price < sum of product regular prices
  - Check for overlapping promotions on same product/branch/time windows
  - Save promotion + branches + products in transaction
- Implement overlap detection: query existing promotions matching any product_id + branch_id, check date/time/day overlap
- Implement `get_computed_status()`: SCHEDULED/ACTIVE/EXPIRED/INACTIVE based on current datetime
- **Files**: `app/services/promotion_service.py`
- **AC**: Overlap detection prevents conflicts; combo_price validated; status dynamically computed

### 4.3 Promotion REST endpoints
- CRUD: POST/GET/PUT/DELETE /api/promotions
- List: GET /api/promotions with filters (branch, type, status)
- RBAC: ADMIN for CRUD
- **Files**: `app/routers/promotions.py`
- **AC**: Full CRUD works; overlap returns 409; computed status in all responses

### 4.4 Active promotions endpoint
- GET /api/branches/{branchId}/promotions/active
- Query: enabled=true, date range includes today, filter by current time + day_of_week in application
- Include product details with regular prices for comparison
- Cache-Control: public, max-age=60
- RBAC: DINER or public
- **Files**: `app/services/promotion_active_service.py`, additions to `app/routers/promotions.py`
- **AC**: Returns only currently-active promotions; includes savings calculation; cached for 60s

## Phase 5: Frontend — Dashboard

### 5.1 Ingredient management pages
- Build `IngredientGroupsPage.tsx`: list + create/edit groups
- Build `IngredientsPage.tsx`: searchable list with group filter, status filter
- Build `IngredientDetailPage.tsx`: full detail with sub-ingredient editor
- Build `IngredientForm.tsx`, `SubIngredientEditor.tsx`, `IngredientSearch.tsx`
- **Files**: `dashboard/src/ingredients/pages/*.tsx`, `dashboard/src/ingredients/components/*.tsx`
- **AC**: Groups CRUD in UI; ingredients searchable; sub-ingredients editable for processed items

### 5.2 Recipe management pages
- Build `RecipesPage.tsx`: card grid with search + difficulty/cuisine filters
- Build `RecipeFormPage.tsx`: multi-section form (basic, times, ingredients, steps, categorization, sensory, safety, costs)
- Build `RecipeDetailPage.tsx`: full read-only view with all sections
- Build components: `IngredientPicker.tsx`, `StepEditor.tsx`, `CostCalculator.tsx`, `AllergenBadges.tsx`, `SensoryFields.tsx`
- **Files**: `dashboard/src/recipes/pages/*.tsx`, `dashboard/src/recipes/components/*.tsx`
- **AC**: Full recipe CRUD in UI; auto-derived fields displayed; ingredient picker with search; steps reorderable

### 5.3 Promotion management pages
- Build `PromotionTypesPage.tsx`: list + create custom types
- Build `PromotionsPage.tsx`: list with status badges, filters
- Build `PromotionFormPage.tsx`: form with temporal rule editor, branch selector, product composer
- Build `TemporalRuleEditor.tsx`: date range picker + time range + day-of-week checkboxes
- Build `ProductComposer.tsx`: product search + quantity + total price preview
- **Files**: `dashboard/src/promotions/pages/*.tsx`, `dashboard/src/promotions/components/*.tsx`
- **AC**: Full promo CRUD in UI; temporal rules editable; overlap error shown; status badges accurate

## Phase 6: Frontend — pwaMenu

### 6.1 Active promotions in menu
- Build `PromotionsSection.tsx`: horizontal scrollable section at top of menu, hidden when no active promos
- Build `PromoCard.tsx`: image, name, combo price, regular price strikethrough, savings badge
- Build `PromoCountdown.tsx`: "Termina en Xh Ym" countdown, updates every minute
- Build `PromoBundleAction.tsx`: "Agregar al carrito" adds all products as a bundle
- Create `promotionsStore.ts` and `promotionsService.ts`
- Fetch active promos on menu load and refresh every 60s
- **Files**: `pwaMenu/src/promotions/components/*.tsx`, `pwaMenu/src/promotions/store/promotionsStore.ts`, `pwaMenu/src/promotions/hooks/useActivePromotions.ts`, `pwaMenu/src/promotions/services/promotionsService.ts`
- **AC**: Section visible only when promos exist; countdown accurate; bundle adds correct items at combo price; hidden when expired
