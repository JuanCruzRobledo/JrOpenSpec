---
sprint: 13
artifact: design
status: complete
---

# Design: Recetas, Ingredientes y Promociones

## Architecture Decisions

### AD-1: Global Ingredient Catalog, Branch-scoped Recipes
- **Decision**: Ingredients are global (shared across branches), recipes are scoped to a branch.
- **Rationale**: Ingredients are standardized (Harina 000 is the same everywhere). Recipes may vary by branch (different chefs, local adaptations).
- **Tradeoff**: A branch can't have a "custom" ingredient — mitigated by flexible naming and the OTRO group.

### AD-2: Auto-derived vs Manual Override for Allergens
- **Decision**: Allergens are auto-derived from ingredients (union of all) but can be manually overridden by the admin.
- **Rationale**: Auto-derivation catches most cases. Manual override handles cross-contamination risks or preparation-specific allergens not captured by ingredients alone.
- **Tradeoff**: Admin must review auto-derived allergens for accuracy — UI shows a "review" prompt.

### AD-3: Temporal Promotion Validation on Write + Read
- **Decision**: Overlap validation on promotion creation (write-time). Active status computed dynamically on API read.
- **Rationale**: Write-time validation prevents conflicting promotions. Read-time computation ensures status is always current without background jobs.
- **Tradeoff**: Read-time computation adds ~5ms per request — acceptable with caching (60s).

### AD-4: Promotion as Bundle (Not Discount)
- **Decision**: Promotions are treated as product bundles with a combo price, not as percentage discounts on individual items.
- **Rationale**: Bundles are simpler to display, price, and audit. "2x1" is a bundle of 2 at the price of 1. "Descuento" is a bundle of 1 at a reduced price.
- **Tradeoff**: Cannot apply percentage discounts to arbitrary cart compositions — out of scope for now.

### AD-5: PostgreSQL JSONB for Flexible Fields
- **Decision**: Use JSONB columns for allergens, dietary_tags, sensory profiles, and warnings.
- **Rationale**: These are lists/maps that vary in structure. JSONB allows flexible storage without extra join tables while supporting GIN indexing for queries.
- **Tradeoff**: No FK enforcement on allergen values — mitigated by application-level validation against an enum.

## DB Schema

### ingredient_groups table
```sql
CREATE TABLE ingredient_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    display_order INT NOT NULL DEFAULT 0,
    is_predefined BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### ingredients table
```sql
CREATE TABLE ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    group_id UUID NOT NULL REFERENCES ingredient_groups(id),
    is_processed BOOLEAN NOT NULL DEFAULT false,
    state VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (state IN ('ACTIVE', 'INACTIVE')),
    unit_of_measure VARCHAR(20) NOT NULL,
    cost_per_unit DECIMAL(12,2) NOT NULL DEFAULT 0,
    allergens JSONB NOT NULL DEFAULT '[]',
    dietary_tags JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_ingredient_name_group UNIQUE (name, group_id)
);

CREATE INDEX idx_ingredients_group ON ingredients(group_id);
CREATE INDEX idx_ingredients_state ON ingredients(state);
CREATE INDEX idx_ingredients_name_search ON ingredients USING gin(name gin_trgm_ops);
CREATE INDEX idx_ingredients_allergens ON ingredients USING gin(allergens);
```

### sub_ingredients table
```sql
CREATE TABLE sub_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    child_ingredient_id UUID NOT NULL REFERENCES ingredients(id),
    quantity DECIMAL(12,4) NOT NULL CHECK (quantity > 0),
    unit_of_measure VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_sub_ingredient UNIQUE (parent_ingredient_id, child_ingredient_id),
    CONSTRAINT no_self_reference CHECK (parent_ingredient_id != child_ingredient_id)
);
```

### recipes table
```sql
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('FACIL', 'MEDIA', 'DIFICIL')),
    servings INT NOT NULL CHECK (servings > 0),
    prep_time_minutes INT NOT NULL DEFAULT 0,
    cooking_time_minutes INT NOT NULL DEFAULT 0,
    total_time_minutes INT GENERATED ALWAYS AS (prep_time_minutes + cooking_time_minutes) STORED,
    chef_notes TEXT,
    cuisine_type VARCHAR(100),
    allergens JSONB NOT NULL DEFAULT '[]',
    dietary_tags JSONB NOT NULL DEFAULT '[]',
    appearance TEXT,
    aroma TEXT,
    flavor TEXT,
    texture TEXT,
    celiac_safe BOOLEAN NOT NULL DEFAULT true,
    modification_notes TEXT,
    warnings JSONB NOT NULL DEFAULT '[]',
    production_cost DECIMAL(12,2) NOT NULL DEFAULT 0,
    suggested_price DECIMAL(12,2),
    yield_quantity INT,
    cost_per_serving DECIMAL(12,2),
    state VARCHAR(20) NOT NULL DEFAULT 'DRAFT' CHECK (state IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recipes_branch ON recipes(branch_id);
CREATE INDEX idx_recipes_state ON recipes(state);
```

### recipe_ingredients table
```sql
CREATE TABLE recipe_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id),
    quantity DECIMAL(12,4) NOT NULL CHECK (quantity > 0),
    unit_of_measure VARCHAR(20) NOT NULL,
    is_optional BOOLEAN NOT NULL DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recipe_ingredients_recipe ON recipe_ingredients(recipe_id);
```

### recipe_steps table
```sql
CREATE TABLE recipe_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INT NOT NULL,
    instruction TEXT NOT NULL,
    time_minutes INT,
    image_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_recipe_step_number UNIQUE (recipe_id, step_number)
);

CREATE INDEX idx_recipe_steps_recipe ON recipe_steps(recipe_id);
```

### promotion_types table
```sql
CREATE TABLE promotion_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),
    requires_combo_price BOOLEAN NOT NULL DEFAULT false,
    is_predefined BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### promotions table
```sql
CREATE TABLE promotions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    promotion_type_id UUID NOT NULL REFERENCES promotion_types(id),
    combo_price DECIMAL(12,2),
    image_url VARCHAR(500),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week JSONB NOT NULL DEFAULT '[0,1,2,3,4,5,6]',
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT check_dates CHECK (end_date >= start_date)
);

CREATE INDEX idx_promotions_dates ON promotions(start_date, end_date);
CREATE INDEX idx_promotions_enabled ON promotions(is_enabled);
```

### promotion_branches table
```sql
CREATE TABLE promotion_branches (
    promotion_id UUID NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES branches(id),
    PRIMARY KEY (promotion_id, branch_id)
);
```

### promotion_products table
```sql
CREATE TABLE promotion_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promotion_id UUID NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INT NOT NULL CHECK (quantity > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_promo_product UNIQUE (promotion_id, product_id)
);

CREATE INDEX idx_promo_products_promotion ON promotion_products(promotion_id);
CREATE INDEX idx_promo_products_product ON promotion_products(product_id);
```

## File Structure

### Backend
```
app/
├── models/
│   ├── ingredient_group.py
│   ├── ingredient.py                 # + SubIngredient
│   ├── recipe.py                     # + RecipeIngredient + RecipeStep
│   ├── promotion_type.py
│   └── promotion.py                  # + PromotionBranch + PromotionProduct
├── schemas/
│   ├── ingredient.py
│   ├── recipe.py
│   ├── promotion_type.py
│   └── promotion.py
├── services/
│   ├── ingredient_service.py
│   ├── recipe_service.py             # includes cost calculation, allergen derivation
│   ├── promotion_type_service.py
│   ├── promotion_service.py          # includes temporal validation, overlap check
│   └── promotion_active_service.py   # active promos query with caching
├── routers/
│   ├── ingredients.py                # groups + ingredients + sub-ingredients
│   ├── recipes.py
│   ├── promotion_types.py
│   └── promotions.py                 # CRUD + active endpoint
└── seeds/
    ├── ingredient_groups.py          # 7 predefined groups
    └── promotion_types.py            # 4 predefined types
```

### pwaMenu additions
```
pwaMenu/src/
├── promotions/
│   ├── components/
│   │   ├── PromotionsSection.tsx     # Featured section in menu
│   │   ├── PromoCard.tsx             # Individual promotion card
│   │   ├── PromoCountdown.tsx        # Time remaining countdown
│   │   └── PromoBundleAction.tsx     # Add bundle to cart
│   ├── store/
│   │   └── promotionsStore.ts
│   ├── hooks/
│   │   └── useActivePromotions.ts    # Fetch + refresh
│   └── services/
│       └── promotionsService.ts
```

### Dashboard additions
```
dashboard/src/
├── ingredients/
│   ├── pages/
│   │   ├── IngredientGroupsPage.tsx
│   │   ├── IngredientsPage.tsx
│   │   └── IngredientDetailPage.tsx
│   └── components/
│       ├── GroupList.tsx
│       ├── IngredientForm.tsx
│       ├── SubIngredientEditor.tsx
│       └── IngredientSearch.tsx
├── recipes/
│   ├── pages/
│   │   ├── RecipesPage.tsx
│   │   ├── RecipeDetailPage.tsx
│   │   └── RecipeFormPage.tsx
│   └── components/
│       ├── RecipeCard.tsx
│       ├── RecipeForm.tsx
│       ├── IngredientPicker.tsx
│       ├── StepEditor.tsx
│       ├── CostCalculator.tsx
│       ├── AllergenBadges.tsx
│       └── SensoryFields.tsx
├── promotions/
│   ├── pages/
│   │   ├── PromotionTypesPage.tsx
│   │   ├── PromotionsPage.tsx
│   │   └── PromotionFormPage.tsx
│   └── components/
│       ├── PromotionTypeForm.tsx
│       ├── PromotionForm.tsx
│       ├── TemporalRuleEditor.tsx
│       ├── BranchSelector.tsx
│       └── ProductComposer.tsx
```

## Sequence Diagrams

### Recipe Cost Calculation
```
Admin           RecipeForm        API              RecipeService     DB
  |                |                |                  |               |
  |--save recipe-->|                |                  |               |
  |                |--POST /recipes>|                  |               |
  |                |                |--validate------->|               |
  |                |                |                  |--fetch ingredients costs
  |                |                |                  |  for each recipe_ingredient:
  |                |                |                  |    cost += ingredient.cost_per_unit * qty
  |                |                |                  |--derive allergens (union)
  |                |                |                  |--check celiac_safe (no GLUTEN)
  |                |                |                  |--calc cost_per_serving
  |                |                |                  |--insert recipe + ingredients + steps
  |                |                |<--recipe---------|               |
  |                |<--201----------|                  |               |
  |<--show recipe--|                |                  |               |
```

### Active Promotions Query
```
Diner           pwaMenu           API              PromotionService  DB
  |                |                |                  |               |
  |--open menu---->|                |                  |               |
  |                |--GET /promos/active-------------->|               |
  |                |                |                  |--query where:
  |                |                |                  |  start_date <= now
  |                |                |                  |  end_date >= now
  |                |                |                  |  is_enabled = true
  |                |                |                  |  branch_id = X
  |                |                |                  |--filter in-app:
  |                |                |                  |  current_time in [start_time, end_time]
  |                |                |                  |  current_day in days_of_week
  |                |                |<--active promos--|               |
  |                |<--200 [promos]-|                  |               |
  |                |--render PromotionsSection         |               |
  |<--see promos---|                |                  |               |
```
