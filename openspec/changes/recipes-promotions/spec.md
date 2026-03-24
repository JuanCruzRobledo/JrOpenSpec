---
sprint: 13
artifact: spec
status: complete
---

# Spec: Recetas, Ingredientes y Promociones

## Requirements (RFC 2119)

### Ingredient Groups
- The system MUST support CRUD for ingredient groups with fields: name, description, display_order
- Predefined groups MUST be seeded: Vegetales, Protenas, Lcteos, Cereales, Condimentos, Aceites, Otros
- Groups MUST be unique by name within the system (global, not per branch)

### Ingredients
- The system MUST support CRUD for ingredients with fields: name, group_id, is_processed, state (ACTIVE/INACTIVE), unit_of_measure, cost_per_unit, allergens[], dietary_tags[]
- Processed ingredients (is_processed=true) MUST support sub-ingredients: a list of other ingredients with quantities
- Ingredient names MUST be unique within a group
- The system MUST support searching ingredients by name (partial match) and filtering by group
- Deactivating an ingredient MUST NOT remove it from existing recipes (soft reference)

### Recipes
- The system MUST support CRUD for recipes scoped to a branch (branch_id)
- Recipe basic info MUST include: name, branch_id, difficulty (FACIL/MEDIA/DIFICIL), servings, description
- Recipe times MUST include: prep_time_minutes, cooking_time_minutes, total_time_minutes (auto-calculated as prep + cooking)
- Recipe ingredients MUST reference the ingredient catalog: ingredient_id, quantity, unit_of_measure, is_optional, notes
- Recipe steps MUST be numbered and include: step_number, instruction (text), time_minutes (optional), image_url (optional)
- Recipe MUST support chef_notes (free text)
- Recipe categorization MUST include: cuisine_type (e.g., "Argentina", "Italiana"), allergens[] (auto-derived from ingredients + manual override), dietary_tags[] (VEGETARIANO, VEGANO, CELIACO, SIN_LACTOSA, etc.)
- Recipe sensory profiles MUST include: appearance, aroma, flavor, texture (all free text, optional)
- Recipe safety MUST include: celiac_safe (boolean, derived from ingredients), modification_notes (free text), warnings[] (free text list)
- Recipe costs MUST include: production_cost (sum of ingredient costs * quantities), suggested_price, yield_quantity, cost_per_serving (auto-calculated)
- The system MUST auto-derive allergens from ingredients' allergen lists (union of all ingredient allergens)
- The system MUST auto-calculate celiac_safe based on ingredient allergens (false if any ingredient has GLUTEN)

### Promotion Types
- The system MUST provide 4 predefined promotion types: HAPPY_HOUR, COMBO_FAMILIAR, DOS_POR_UNO, DESCUENTO
- The system MUST support creating custom promotion types with: name, description, icon, requires_combo_price (boolean)
- Predefined types MUST NOT be deletable
- Custom types MUST be soft-deletable

### Promotions
- The system MUST support CRUD for promotions with fields:
  - name, description, promotion_type_id, combo_price (required if type.requires_combo_price), image_url
  - start_date, end_date (date range, inclusive)
  - start_time, end_time (daily time window, e.g., 18:00-21:00)
  - days_of_week[] (e.g., [1,2,3,4,5] for weekdays)
  - branch_ids[] (multi-branch support)
  - products[]: list of { product_id, quantity }
- Temporal validation MUST be strict:
  - A promotion is "active" only when: current date is within [start_date, end_date] AND current time is within [start_time, end_time] AND current day_of_week is in days_of_week[]
- The system MUST NOT allow two promotions on the same product at the same branch during overlapping time windows
- Promotion status MUST be dynamically computed: SCHEDULED (future start_date), ACTIVE (within all temporal windows), EXPIRED (past end_date), INACTIVE (manually disabled)
- The system MUST validate that combo_price < sum of product regular prices (otherwise it's not a promotion)

### Active Promotions API
- GET /api/branches/{branchId}/promotions/active MUST return only promotions that are currently active (all temporal checks pass)
- The response MUST include full promotion details with product names and regular prices for comparison
- The endpoint MUST be cacheable (Cache-Control: max-age=60)

### pwaMenu Integration
- The diner menu MUST display a "Promociones" section when active promotions exist
- Each promotion card MUST show: name, image, description, combo price, regular price (strikethrough), savings amount, time remaining (countdown if ending within 2 hours)
- The section MUST NOT appear if no active promotions exist
- Products in a promotion MUST be orderable as a bundle (single add-to-cart action)

## Data Models

### IngredientGroup
```python
class IngredientGroup(BaseModel):
    id: UUID
    name: str                           # max 100 chars, unique
    description: str | None
    display_order: int                  # for UI sorting
    is_predefined: bool                 # false = can delete
    created_at: datetime
    updated_at: datetime
```

### Ingredient
```python
class Ingredient(BaseModel):
    id: UUID
    name: str                           # max 200 chars
    group_id: UUID                      # FK to IngredientGroup
    is_processed: bool                  # if true, has sub-ingredients
    state: IngredientState              # ACTIVE | INACTIVE
    unit_of_measure: str                # "kg", "l", "unidad", "g", "ml"
    cost_per_unit: Decimal              # ARS per unit
    allergens: list[str]                # ["GLUTEN", "LACTOSA", "FRUTOS_SECOS", ...]
    dietary_tags: list[str]             # ["VEGETARIANO", "VEGANO", ...]
    created_at: datetime
    updated_at: datetime

class SubIngredient(BaseModel):
    id: UUID
    parent_ingredient_id: UUID          # The processed ingredient
    child_ingredient_id: UUID           # The component ingredient
    quantity: Decimal
    unit_of_measure: str
```

### Recipe
```python
class Recipe(BaseModel):
    id: UUID
    branch_id: UUID                     # FK to Branch
    name: str                           # max 200 chars
    description: str | None
    difficulty: RecipeDifficulty        # FACIL | MEDIA | DIFICIL
    servings: int
    prep_time_minutes: int
    cooking_time_minutes: int
    total_time_minutes: int             # auto-calculated
    chef_notes: str | None
    cuisine_type: str | None            # "Argentina", "Italiana", etc.
    allergens: list[str]                # auto-derived + manual override
    dietary_tags: list[str]
    appearance: str | None              # sensory
    aroma: str | None                   # sensory
    flavor: str | None                  # sensory
    texture: str | None                 # sensory
    celiac_safe: bool                   # auto-derived
    modification_notes: str | None
    warnings: list[str]
    production_cost: Decimal            # auto-calculated
    suggested_price: Decimal | None
    yield_quantity: int | None
    cost_per_serving: Decimal | None    # auto-calculated
    state: RecipeState                  # DRAFT | PUBLISHED | ARCHIVED
    created_at: datetime
    updated_at: datetime

class RecipeIngredient(BaseModel):
    id: UUID
    recipe_id: UUID
    ingredient_id: UUID
    quantity: Decimal
    unit_of_measure: str
    is_optional: bool
    notes: str | None

class RecipeStep(BaseModel):
    id: UUID
    recipe_id: UUID
    step_number: int
    instruction: str
    time_minutes: int | None
    image_url: str | None
```

### PromotionType
```python
class PromotionType(BaseModel):
    id: UUID
    name: str                           # max 100 chars, unique
    description: str | None
    icon: str | None                    # icon identifier
    requires_combo_price: bool          # true for COMBO_FAMILIAR, DOS_POR_UNO
    is_predefined: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### Promotion
```python
class Promotion(BaseModel):
    id: UUID
    name: str                           # max 200 chars
    description: str | None
    promotion_type_id: UUID             # FK to PromotionType
    combo_price: Decimal | None         # required if type.requires_combo_price
    image_url: str | None
    start_date: date
    end_date: date
    start_time: time                    # daily window start (e.g., 18:00)
    end_time: time                      # daily window end (e.g., 21:00)
    days_of_week: list[int]             # 0=Monday, 6=Sunday
    is_enabled: bool                    # manual toggle
    created_at: datetime
    updated_at: datetime

class PromotionBranch(BaseModel):
    promotion_id: UUID
    branch_id: UUID

class PromotionProduct(BaseModel):
    id: UUID
    promotion_id: UUID
    product_id: UUID
    quantity: int                       # how many of this product in the promo
```

## API Contracts

### POST /api/ingredient-groups
**Auth**: Bearer JWT (role: ADMIN)
**Request**: `{ "name": "Vegetales", "description": "...", "displayOrder": 1 }`
**Response 201**: `{ "id": "uuid", "name": "Vegetales", ... }`

### GET /api/ingredient-groups
**Auth**: Bearer JWT (role: ADMIN)
**Response 200**: `{ "groups": [IngredientGroup] }`

### POST /api/ingredients
**Auth**: Bearer JWT (role: ADMIN)
**Request**:
```json
{
  "name": "Harina 000",
  "groupId": "uuid",
  "isProcessed": false,
  "unitOfMeasure": "kg",
  "costPerUnit": 1200.00,
  "allergens": ["GLUTEN"],
  "dietaryTags": []
}
```
**Response 201**: `{ "id": "uuid", ... }`

### GET /api/ingredients
**Auth**: Bearer JWT (role: ADMIN)
**Query**: `?group={groupId}&search={term}&state=ACTIVE`
**Response 200**: `{ "ingredients": [Ingredient], "total": 150 }`

### POST /api/ingredients/{id}/sub-ingredients
**Auth**: Bearer JWT (role: ADMIN)
**Request**: `{ "childIngredientId": "uuid", "quantity": 0.5, "unitOfMeasure": "kg" }`
**Response 201**: SubIngredient

### POST /api/branches/{branchId}/recipes
**Auth**: Bearer JWT (role: ADMIN)
**Request**: Full recipe body with ingredients and steps arrays
**Response 201**: Full Recipe with auto-calculated fields

### GET /api/branches/{branchId}/recipes
**Auth**: Bearer JWT (role: ADMIN)
**Query**: `?search={term}&difficulty={level}&cuisine={type}`
**Response 200**: `{ "recipes": [Recipe], "total": 45 }`

### GET /api/branches/{branchId}/recipes/{recipeId}
**Auth**: Bearer JWT (role: ADMIN)
**Response 200**: Full recipe with ingredients, steps, costs

### POST /api/promotion-types
**Auth**: Bearer JWT (role: ADMIN, SUPERADMIN)
**Request**: `{ "name": "Flash Sale", "description": "...", "icon": "flash", "requiresComboPrice": false }`
**Response 201**: PromotionType

### POST /api/promotions
**Auth**: Bearer JWT (role: ADMIN)
**Request**:
```json
{
  "name": "Happy Hour Cerveza",
  "promotionTypeId": "uuid",
  "comboPrice": null,
  "startDate": "2026-03-20",
  "endDate": "2026-06-30",
  "startTime": "18:00",
  "endTime": "21:00",
  "daysOfWeek": [0, 1, 2, 3, 4],
  "branchIds": ["uuid1", "uuid2"],
  "products": [
    { "productId": "uuid", "quantity": 2 }
  ]
}
```
**Response 201**: Promotion with computed status
**Response 409**: Overlapping promotion on same product/branch/time

### GET /api/branches/{branchId}/promotions/active
**Auth**: Bearer JWT (role: DINER) or public
**Response 200**:
```json
{
  "promotions": [
    {
      "id": "uuid",
      "name": "Happy Hour Cerveza",
      "description": "2 cervezas artesanales al precio de 1",
      "comboPrice": 3500.00,
      "regularPrice": 7000.00,
      "savings": 3500.00,
      "imageUrl": "https://...",
      "endsAt": "2026-03-19T21:00:00-03:00",
      "products": [
        { "productId": "uuid", "productName": "Cerveza IPA", "quantity": 2, "regularPrice": 3500.00 }
      ]
    }
  ]
}
```
**Headers**: `Cache-Control: public, max-age=60`

## Scenarios

### Scenario: Create a processed ingredient with sub-ingredients
```
Given the admin creates ingredient "Masa para empanadas" with is_processed=true
When the admin adds sub-ingredients:
  - Harina 000: 0.5 kg
  - Grasa vacuna: 0.15 kg
  - Sal: 0.01 kg
  - Agua: 0.25 l
Then the ingredient is saved with all sub-ingredients
And the cost_per_unit is NOT auto-calculated (manual entry for processed)
And allergens are derived from sub-ingredients (GLUTEN from Harina)
```

### Scenario: Create a recipe with auto-derived fields
```
Given the admin creates recipe "Empanadas de Carne" with:
  - Ingredients: Masa para empanadas (has GLUTEN), Carne picada, Cebolla, Comino
  - Prep time: 45 min, Cooking time: 25 min
Then total_time_minutes = 70
And allergens auto-includes GLUTEN (from Masa)
And celiac_safe = false (GLUTEN detected)
And production_cost = sum of (ingredient.cost_per_unit * quantity) for all ingredients
And cost_per_serving = production_cost / servings
```

### Scenario: Promotion temporal validation
```
Given a promotion "Happy Hour" configured:
  - Dates: 2026-03-20 to 2026-06-30
  - Time: 18:00 to 21:00
  - Days: Mon-Fri
When checked at 2026-03-19 19:00 (Wednesday, before start_date)
Then status = SCHEDULED (date not yet active)
When checked at 2026-03-21 19:00 (Friday, within all windows)
Then status = ACTIVE
When checked at 2026-03-22 19:00 (Saturday, not in days_of_week)
Then status = ACTIVE (exists but not currently active for ordering)
When checked at 2026-07-01 19:00 (past end_date)
Then status = EXPIRED
```

### Scenario: Overlapping promotion rejected
```
Given promotion "2x1 Cerveza IPA" exists for Branch A:
  - Dates: March 20-30, Time: 18:00-21:00, Days: Mon-Fri
  - Product: Cerveza IPA
When admin creates "Descuento Cerveza IPA" for Branch A:
  - Dates: March 25-31, Time: 19:00-22:00, Days: Wed-Fri
  - Product: Cerveza IPA
Then the system returns 409 Conflict
Because Cerveza IPA at Branch A overlaps on Wed-Fri 19:00-21:00 in March 25-30
```

### Scenario: Diner sees active promotions
```
Given it's Friday 19:30 and "Happy Hour Cerveza" is active
When the diner opens the menu in pwaMenu
Then a "Promociones" section appears at the top
And "Happy Hour Cerveza" shows: image, "2 Cervezas IPA", combo price $3,500, regular $7,000 (strikethrough), "Ahorrás $3,500"
And a countdown shows "Termina en 1h 30m"
When the diner taps the promotion
Then both Cervezas IPA are added to the cart as a bundle at $3,500
```
