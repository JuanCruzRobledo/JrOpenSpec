---
phase: 4
archived_at: 2026-03-30
verify_status: PASS_WITH_WARNINGS
source_change: menu-domain
---

---
sprint: 4
artifact: spec
status: complete
---

# SDD Spec — Sprint 4: Productos Avanzado y API Pública del Menú

> **Updated 2026-03-30**: All Phase 4 warnings resolved via `menu-domain-fixes`. Seed migration (005), rate limiting (60/min), N+1 elimination, dashboard routes confirmed, full test coverage added.

## Status: APPROVED

---

## 1. Requirements (RFC 2119)

### 1.1 Allergen Subsystem

- The system MUST preload 14 EU mandatory allergens on first migration with codes: `gluten`, `dairy`, `eggs`, `fish`, `crustaceans`, `tree_nuts`, `soy`, `celery`, `mustard`, `sesame`, `sulfites`, `lupins`, `mollusks`, `peanuts`.
- Each allergen MUST have: `id` (int, PK), `code` (str, unique per tenant, max 50), `name` (str, max 100), `description` (text, nullable), `icon` (str, nullable — icon identifier), `is_system` (bool, default false — true for EU 14), `tenant_id` (int, FK, nullable — null for system allergens), `created_at`, `updated_at`, `deleted_at`.
- System allergens (is_system=true) MUST NOT be editable or deletable by tenants.
- Tenants MAY create custom allergens (is_system=false, tenant_id set).
- The system MUST support allergen severity levels as an enum: `low`, `moderate`, `severe`, `life_threatening`.
- The system MUST support cross-reactions via `AllergenCrossReaction` table.
- Cross-reactions MUST be bidirectional: if A cross-reacts with B, querying either A or B returns the relation.
- Cross-reaction records: `id`, `allergen_id` (FK), `related_allergen_id` (FK), `description` (text — explains the cross-reaction), `severity` (enum: low/moderate/severe/life_threatening), unique constraint on (allergen_id, related_allergen_id) with CHECK allergen_id < related_allergen_id to prevent duplicates.

### 1.2 Product-Allergen Association

- `ProductAllergen` junction: `id`, `product_id` (FK), `allergen_id` (FK), `presence_type` (enum: `contains`, `may_contain`, `free_of`), `risk_level` (enum: `low`, `moderate`, `severe`, `life_threatening`), `notes` (text, nullable), unique on (product_id, allergen_id).
- A product MUST have at least one allergen record before being published (enforced at service layer, not DB).
- When presence_type is `free_of`, risk_level MUST be `low`.

### 1.3 Dietary Profiles

- `DietaryProfile` table: `id`, `code` (str, unique per tenant, max 50), `name` (str, max 100), `description` (text, nullable), `icon` (str, nullable), `is_system` (bool), `tenant_id` (int, FK, nullable).
- Predefined system profiles (7): `vegetarian`, `vegan`, `gluten_free`, `dairy_free`, `celiac_safe`, `keto`, `low_sodium`.
- `ProductDietaryProfile` junction: `product_id`, `dietary_profile_id`, unique constraint.
- Tenants MAY create custom dietary profiles.

### 1.4 Cooking Methods

- `CookingMethod` table: `id`, `code` (str, unique, max 50), `name` (str, max 100), `icon` (str, nullable), `is_system` (bool), `tenant_id` (int, FK, nullable).
- Predefined system methods (10): `grill`, `oven`, `fryer`, `steam`, `raw`, `sous_vide`, `smoke`, `saute`, `boil`, `roast`.
- `ProductCookingMethod` junction: `product_id`, `cooking_method_id`, unique constraint.

### 1.5 Flavor & Texture Profiles

- Stored as PostgreSQL ARRAY columns on Product (not separate tables — fixed small sets):
  - `flavor_profiles`: Array of enum values from (`sweet`, `salty`, `sour`, `bitter`, `umami`, `spicy`).
  - `texture_profiles`: Array of enum values from (`crispy`, `creamy`, `crunchy`, `soft`, `chewy`, `liquid`).
- Arrays MUST NOT be empty when product is published (service layer validation).

### 1.6 Product Ingredients

- `ProductIngredient` table: `id`, `product_id` (FK), `ingredient_id` (FK — references future Ingredient catalog, nullable for now; use name fallback), `name` (str, max 200 — denormalized or standalone), `quantity` (Decimal(10,3)), `unit` (enum: `g`, `kg`, `ml`, `l`, `unit`, `tbsp`, `tsp`, `cup`, `oz`, `lb`, `pinch`), `sort_order` (int), `is_optional` (bool, default false), `notes` (text, nullable).
- Unique constraint on (product_id, sort_order).
- Ingredients MUST be returned in sort_order ascending.

### 1.7 Branch Product (Pricing & Availability)

- `BranchProduct` table: `id`, `branch_id` (FK), `product_id` (FK), `is_active` (bool, default true), `price_cents` (int, nullable — null means use product.base_price_cents), `sort_order` (int, default 0), `created_at`, `updated_at`.
- Unique constraint on (branch_id, product_id).
- `price_cents` MUST be >= 0 when not null. Stored as integer (centavos).
- Effective price resolution: `BranchProduct.price_cents ?? Product.base_price_cents`.
- When a product is created, BranchProduct records SHOULD be auto-created for all active branches of the tenant (is_active=true, price_cents=null).

### 1.8 Batch Price Update

- Input: list of product_ids, operation (`fixed_add`, `fixed_subtract`, `percentage_increase`, `percentage_decrease`), amount (int cents for fixed, Decimal for percentage), target_branch_id (nullable — null means all branches).
- The system MUST generate a preview: list of {product_id, product_name, branch_name, old_price_cents, new_price_cents}.
- The system MUST NOT apply changes without explicit confirmation (two-step: preview → confirm).
- Percentage calculations MUST round to nearest integer (centavo). Use `round()`.
- New price MUST be >= 0. If calculation results in negative, clamp to 0.
- Each price change MUST create an audit log entry with old_value and new_value.

### 1.9 Badges

- `Badge` table: `id`, `code` (str, unique per tenant, max 50), `name` (str, max 100), `color` (str, max 7 — hex color like #FF0000), `icon` (str, nullable), `is_system` (bool), `tenant_id` (int, FK, nullable), `created_at`, `updated_at`, `deleted_at`.
- Predefined (4): `new` (Nuevo, #22C55E), `best_seller` (Más vendido, #F59E0B), `chef_recommends` (Chef recomienda, #8B5CF6), `on_sale` (Oferta, #EF4444).
- `ProductBadge` junction: `product_id`, `badge_id`, `sort_order`, unique on (product_id, badge_id).

### 1.10 Seals

- `Seal` table: `id`, `code` (str, unique per tenant, max 50), `name` (str, max 100), `color` (str, max 7), `icon` (str, nullable), `is_system` (bool), `tenant_id` (int, FK, nullable), `created_at`, `updated_at`, `deleted_at`.
- Predefined (6): `organic` (Orgánico, #16A34A), `local` (Producto local, #2563EB), `preservative_free` (Sin conservantes, #D97706), `artisan` (Artesanal, #9333EA), `sustainable` (Sustentable, #059669), `fair_trade` (Comercio justo, #0891B2).
- `ProductSeal` junction: `product_id`, `seal_id`, `sort_order`, unique on (product_id, seal_id).

### 1.11 Public Menu API

- All public endpoints MUST NOT require authentication.
- All public endpoints MUST be rate-limited to 60 requests/minute per IP.
- All public endpoints MUST be prefixed with `/api/public/`.
- Responses MUST use camelCase field names (frontend convention).
- All responses MUST include `Cache-Control: public, max-age=300` header.

---

## 2. API Contracts

### 2.1 GET /api/public/menu/{slug}

**Description**: Full menu for a branch, organized by categories.

**Path Parameters**:
- `slug` (str): Branch slug (e.g., "buen-sabor-centro").

**Query Parameters**:
- `dietary` (str, optional): Comma-separated dietary profile codes to filter (e.g., "vegan,gluten_free"). Products MUST match ALL specified profiles.
- `allergen_free` (str, optional): Comma-separated allergen codes. Excludes products that `contains` or `may_contain` these allergens.
- `lang` (str, optional, default "es"): Language code for i18n.

**Response 200**:
```json
{
  "branch": {
    "id": 1,
    "name": "Buen Sabor Centro",
    "slug": "buen-sabor-centro",
    "address": "Av. San Martín 1234",
    "phone": "+54 261 555-1234",
    "openNow": true,
    "schedule": {
      "monday": {"open": "11:00", "close": "23:00"}
    }
  },
  "categories": [
    {
      "id": 1,
      "name": "Pizzas",
      "slug": "pizzas",
      "description": "Nuestras pizzas artesanales",
      "sortOrder": 1,
      "products": [
        {
          "id": 10,
          "name": "Pizza Margherita",
          "shortDescription": "Tomate, mozzarella, albahaca",
          "priceCents": 1500,
          "imageUrl": "https://...",
          "badges": [{"code": "chef_recommends", "name": "Chef recomienda", "color": "#8B5CF6", "icon": "star"}],
          "seals": [{"code": "artisan", "name": "Artesanal", "color": "#9333EA", "icon": "hand"}],
          "dietaryProfiles": ["vegetarian"],
          "allergenSummary": {
            "contains": ["gluten", "dairy"],
            "mayContain": ["eggs"],
            "freeOf": []
          },
          "cookingMethods": ["oven"],
          "flavorProfiles": ["salty", "umami"],
          "isAvailable": true
        }
      ]
    }
  ],
  "allergenLegend": [
    {"code": "gluten", "name": "Gluten", "icon": "wheat"},
    {"code": "dairy", "name": "Lácteos", "icon": "milk"}
  ],
  "generatedAt": "2026-03-19T15:30:00Z"
}
```

**Response 404**: `{"detail": "Branch not found"}`

### 2.2 GET /api/public/menu/{slug}/product/{id}

**Description**: Full product detail with allergens, cross-reactions, ingredients.

**Path Parameters**:
- `slug` (str): Branch slug.
- `id` (int): Product ID.

**Response 200**:
```json
{
  "id": 10,
  "name": "Pizza Margherita",
  "description": "Pizza artesanal con salsa de tomate San Marzano, mozzarella fior di latte y albahaca fresca.",
  "shortDescription": "Tomate, mozzarella, albahaca",
  "priceCents": 1500,
  "imageUrl": "https://...",
  "imageGallery": ["https://..."],
  "badges": [{"code": "chef_recommends", "name": "Chef recomienda", "color": "#8B5CF6", "icon": "star"}],
  "seals": [{"code": "artisan", "name": "Artesanal", "color": "#9333EA", "icon": "hand"}],
  "dietaryProfiles": [
    {"code": "vegetarian", "name": "Vegetariano", "icon": "leaf"}
  ],
  "allergens": [
    {
      "code": "gluten",
      "name": "Gluten",
      "icon": "wheat",
      "presenceType": "contains",
      "riskLevel": "severe",
      "notes": "Masa de harina de trigo",
      "crossReactions": [
        {"code": "celery", "name": "Apio", "description": "Proteínas similares pueden causar reacción cruzada", "severity": "low"}
      ]
    },
    {
      "code": "dairy",
      "name": "Lácteos",
      "icon": "milk",
      "presenceType": "contains",
      "riskLevel": "moderate",
      "notes": "Mozzarella fior di latte",
      "crossReactions": []
    }
  ],
  "cookingMethods": [{"code": "oven", "name": "Horno", "icon": "flame"}],
  "flavorProfiles": ["salty", "umami"],
  "textureProfiles": ["crispy", "soft"],
  "ingredients": [
    {"name": "Harina 000", "quantity": 250.0, "unit": "g", "isOptional": false},
    {"name": "Salsa de tomate", "quantity": 100.0, "unit": "ml", "isOptional": false},
    {"name": "Mozzarella fior di latte", "quantity": 150.0, "unit": "g", "isOptional": false},
    {"name": "Albahaca fresca", "quantity": 5.0, "unit": "unit", "isOptional": false},
    {"name": "Aceite de oliva", "quantity": 1.0, "unit": "tbsp", "isOptional": true}
  ],
  "branch": {
    "id": 1,
    "name": "Buen Sabor Centro",
    "slug": "buen-sabor-centro"
  },
  "category": {
    "id": 1,
    "name": "Pizzas",
    "slug": "pizzas"
  },
  "generatedAt": "2026-03-19T15:30:00Z"
}
```

**Response 404**: `{"detail": "Product not found or not available in this branch"}`

### 2.3 GET /api/public/branches

**Description**: Active branches for tenant discovery.

**Query Parameters**:
- `tenant` (str, required): Tenant slug.

**Response 200**:
```json
{
  "branches": [
    {
      "id": 1,
      "name": "Buen Sabor Centro",
      "slug": "buen-sabor-centro",
      "address": "Av. San Martín 1234, Mendoza",
      "phone": "+54 261 555-1234",
      "latitude": -32.8895,
      "longitude": -68.8458,
      "openNow": true,
      "schedule": {
        "monday": {"open": "11:00", "close": "23:00"},
        "tuesday": {"open": "11:00", "close": "23:00"},
        "wednesday": null,
        "thursday": {"open": "11:00", "close": "23:00"},
        "friday": {"open": "11:00", "close": "00:00"},
        "saturday": {"open": "11:00", "close": "00:00"},
        "sunday": {"open": "12:00", "close": "22:00"}
      },
      "productCount": 45,
      "categoryCount": 8
    }
  ],
  "generatedAt": "2026-03-19T15:30:00Z"
}
```

### 2.4 GET /api/public/allergens

**Description**: Full allergen catalog with cross-reactions.

**Query Parameters**:
- `tenant` (str, required): Tenant slug.

**Response 200**:
```json
{
  "allergens": [
    {
      "code": "gluten",
      "name": "Gluten",
      "description": "Cereales que contienen gluten: trigo, centeno, cebada, avena, espelta, kamut",
      "icon": "wheat",
      "isSystem": true,
      "crossReactions": [
        {"relatedCode": "celery", "relatedName": "Apio", "description": "Sensibilidad cruzada por profilinas", "severity": "low"}
      ]
    },
    {
      "code": "dairy",
      "name": "Lácteos",
      "description": "Leche y productos derivados, incluyendo lactosa y caseína",
      "icon": "milk",
      "isSystem": true,
      "crossReactions": [
        {"relatedCode": "soy", "relatedName": "Soja", "description": "Proteínas de soja pueden causar reacción en alérgicos a caseína", "severity": "low"}
      ]
    }
  ],
  "generatedAt": "2026-03-19T15:30:00Z"
}
```

---

## 3. Caching Specification

- **Backend**: Redis (already in stack).
- **TTL**: 300 seconds (5 minutes).
- **Key patterns**:
  - `cache:public:menu:{branch_slug}` — full menu response (optionally with query params hash suffix for filtered variants: `cache:public:menu:{slug}:q:{md5(query_params)}`).
  - `cache:public:product:{branch_slug}:{product_id}` — product detail.
  - `cache:public:branches:{tenant_slug}` — branches list.
  - `cache:public:allergens:{tenant_slug}` — allergen catalog.
- **Invalidation triggers** (delete matching cache keys):
  - Product create/update/delete → invalidate `cache:public:menu:{all_branch_slugs_for_tenant}*`, `cache:public:product:*:{product_id}`.
  - Branch update → invalidate `cache:public:branches:{tenant_slug}`, `cache:public:menu:{branch_slug}*`.
  - Allergen create/update/delete → invalidate `cache:public:allergens:{tenant_slug}`, `cache:public:menu:{all_branch_slugs}*`.
  - BranchProduct update → invalidate `cache:public:menu:{branch_slug}*`, `cache:public:product:{branch_slug}:*`.
  - Badge/Seal update → invalidate `cache:public:menu:{all_branch_slugs}*`.
- **Implementation**: Decorator `@cache_public(key_pattern, ttl=300)` on public router handlers. Invalidation via `cache_invalidate(pattern)` helper using Redis SCAN + DELETE.
- **Serialization**: JSON via `orjson` for speed.
- **Cache-Control header**: `public, max-age=300` on all public responses.

---

## 4. Batch Price Update Rules

1. User selects products (checkboxes in product list).
2. User chooses operation: `fixed_add` | `fixed_subtract` | `percentage_increase` | `percentage_decrease`.
3. User enters amount: integer (cents) for fixed, decimal for percentage.
4. User optionally selects target branch (default: all branches).
5. System returns preview: `POST /api/dashboard/products/batch-price/preview`.
6. User reviews preview table (product name, branch, old price, new price, diff).
7. User confirms: `POST /api/dashboard/products/batch-price/apply` with same payload + `confirmed: true`.
8. System applies changes transactionally and creates audit log entries.
9. Cache invalidation triggered for affected branches.

**Business Rules**:
- Minimum price: 0 cents (free items allowed).
- Maximum single batch: 500 products (prevent accidental mass updates).
- Percentage precision: 2 decimal places (e.g., 10.50%).
- Rounding: `round(old_price * (1 + pct/100))` for increases; `round(old_price * (1 - pct/100))` for decreases.
- If result < 0, clamp to 0.

**Internal API**:

`POST /api/dashboard/products/batch-price/preview`:
```json
{
  "productIds": [1, 2, 3],
  "operation": "percentage_increase",
  "amount": 15.5,
  "branchId": null
}
```
Response:
```json
{
  "changes": [
    {"productId": 1, "productName": "Pizza Margherita", "branchId": 1, "branchName": "Centro", "oldPriceCents": 1500, "newPriceCents": 1733},
    {"productId": 1, "productName": "Pizza Margherita", "branchId": 2, "branchName": "Sur", "oldPriceCents": 1600, "newPriceCents": 1848}
  ],
  "totalProducts": 3,
  "totalBranches": 2,
  "totalChanges": 6
}
```

`POST /api/dashboard/products/batch-price/apply`:
```json
{
  "productIds": [1, 2, 3],
  "operation": "percentage_increase",
  "amount": 15.5,
  "branchId": null,
  "confirmed": true
}
```
Response: `{"applied": 6, "auditLogIds": [101, 102, 103, 104, 105, 106]}`

---

## 5. Scenarios (Given/When/Then)

### S1: Allergen Seed Data
- **Given** a fresh tenant database migration runs
- **When** the migration completes
- **Then** 14 EU allergens exist with is_system=true, codes match EU standard, tenant_id is null

### S2: Custom Allergen Creation
- **Given** an admin user for tenant "buen-sabor"
- **When** they create an allergen with code "sesame_oil", name "Aceite de sésamo"
- **Then** the allergen is created with is_system=false, tenant_id=buen-sabor's ID

### S3: Allergen Cross-Reaction Query
- **Given** allergen "crustaceans" has cross-reaction with "dust_mites" (severity: moderate)
- **When** public API returns allergen "crustaceans" details
- **Then** cross-reactions include {"relatedCode": "dust_mites", "severity": "moderate"}
- **And** querying "dust_mites" also shows cross-reaction with "crustaceans"

### S4: Product Allergen Assignment
- **Given** product "Pizza Margherita" exists
- **When** admin assigns allergen "gluten" with presence_type="contains", risk_level="severe"
- **Then** ProductAllergen record is created
- **And** public menu shows "gluten" in allergenSummary.contains

### S5: Free-Of Validation
- **Given** admin assigns allergen "peanuts" to a product
- **When** presence_type is "free_of" and risk_level is "severe"
- **Then** the system rejects with validation error: "free_of presence must have low risk level"

### S6: Dietary Profile Filtering
- **Given** branch "centro" has products: Pizza (vegetarian), Steak (none), Salad (vegan, vegetarian)
- **When** public menu is requested with `?dietary=vegetarian`
- **Then** response includes Pizza and Salad, excludes Steak

### S7: Allergen-Free Filtering
- **Given** branch "centro" has products: Pizza (contains gluten), Steak (free_of gluten), Salad (may_contain gluten)
- **When** public menu is requested with `?allergen_free=gluten`
- **Then** response includes only Steak (excludes contains AND may_contain)

### S8: Per-Branch Pricing
- **Given** product "Pizza" has base_price_cents=1500
- **And** BranchProduct for branch "centro" has price_cents=1800
- **And** BranchProduct for branch "sur" has price_cents=null
- **When** public menu for "centro" is requested
- **Then** Pizza shows priceCents=1800
- **When** public menu for "sur" is requested
- **Then** Pizza shows priceCents=1500 (fallback to base)

### S9: Branch Exclusion
- **Given** product "Pizza" exists with BranchProduct for branches "centro" (is_active=true) and "sur" (is_active=false)
- **When** public menu for "sur" is requested
- **Then** Pizza is NOT in the response

### S10: Batch Price Update Preview
- **Given** products [Pizza, Steak] selected, operation=percentage_increase, amount=10.0, branchId=null
- **When** preview is requested
- **Then** response shows old and new prices for ALL branches for both products
- **And** new prices are rounded to nearest integer

### S11: Batch Price Negative Clamp
- **Given** product "Water" has price_cents=50 in branch "centro"
- **When** batch update with operation=fixed_subtract, amount=100
- **Then** preview shows new_price_cents=0 (clamped, not -50)

### S12: Cache Invalidation
- **Given** public menu for branch "centro" is cached
- **When** admin updates a product in that branch
- **Then** cache key `cache:public:menu:buen-sabor-centro*` is deleted
- **And** next public request hits the database and re-caches

### S13: Public API Rate Limiting
- **Given** an IP address has made 60 requests in the last minute
- **When** they make request #61 to any public endpoint
- **Then** response is 429 Too Many Requests with Retry-After header

### S14: Badge Assignment
- **Given** product "Pizza" exists and badge "chef_recommends" exists
- **When** admin assigns the badge to the product
- **Then** public menu shows the badge in product.badges array

### S15: Custom Seal Creation
- **Given** tenant "buen-sabor" admin
- **When** they create seal code="homemade", name="Casero", color="#F97316"
- **Then** seal is created with is_system=false, tenant_id set
- **And** it can be assigned to products

---

## Next Recommended

→ `sdd-design` (DB schema, component architecture, caching implementation details)
