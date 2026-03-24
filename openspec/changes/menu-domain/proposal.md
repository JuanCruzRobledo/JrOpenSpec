---
sprint: 4
artifact: proposal
status: complete
---

# SDD Proposal — Sprint 4: Productos Avanzado y API Pública del Menú

## Status: APPROVED

## Executive Summary

Sprint 4 enriches the Product domain with allergen tracking (EU 14 + custom), dietary profiles, cooking methods, flavor/texture profiles, ingredient references, per-branch pricing/availability, batch price updates, and badges/seals. It also exposes a public, unauthenticated API for the menu (with 5-minute cache TTL) so the pwaMenu client can render menus without requiring login.

## Problem Statement

Currently, the Product model is a skeleton: name, description, category, base price. This is insufficient for:
1. **Food safety compliance**: EU Regulation 1169/2011 mandates allergen declaration. Restaurants need to track 14 mandatory allergens with presence types and severity levels.
2. **Dietary inclusivity**: Customers filter by vegetarian, vegan, gluten-free, keto, etc. Without structured dietary profiles, filtering is impossible.
3. **Multi-branch pricing**: Different branches have different cost structures. A single price per product doesn't work for chains.
4. **Public menu access**: The pwaMenu needs to fetch the menu without authentication. Currently all endpoints require JWT.

## Proposed Solution

### 1. Allergen Subsystem
- Preload 14 EU mandatory allergens as seed data (immutable system records).
- Allow tenants to create custom allergens.
- Model cross-reactions (e.g., latex↔banana, latex↔avocado, latex↔kiwi; shrimp↔dust mites).
- Product-allergen association with: `presence_type` (contains | may_contain | free_of) and `risk_level` (low | moderate | severe | life_threatening).
- Public API exposes allergen catalog with cross-reactions for consumer apps.

### 2. Product Extended Model
- **Dietary profiles**: Many-to-many with predefined profiles (vegetarian, vegan, gluten_free, dairy_free, celiac_safe, keto, low_sodium) + tenant custom profiles.
- **Cooking methods**: Many-to-many multiselect (grill, oven, fryer, steam, raw, sous_vide, smoke, sauté, boil, roast).
- **Flavor profiles**: sweet, salty, sour, bitter, umami, spicy (multiselect).
- **Texture profiles**: crispy, creamy, crunchy, soft, chewy, liquid (multiselect).
- **Ingredients**: Ordered list referencing ingredient catalog, each with quantity (Decimal) + unit (enum: g, kg, ml, l, unit, tbsp, tsp, cup, oz, lb, pinch).

### 3. Per-Branch Pricing & Availability
- `BranchProduct` junction table: branch_id, product_id, is_active (availability toggle), price_cents (nullable — falls back to product.base_price_cents if null), sort_order.
- Dashboard UI: toggle "Precios por sucursal" → shows grid of branches with active/price columns.
- Exclusions: simple toggle per branch to enable/disable product availability.

### 4. Batch Price Update
- Select multiple products → choose operation (fixed amount add/subtract OR percentage increase/decrease) → preview changes (old price → new price) → confirm.
- Applies to selected branch or all branches.
- Audit log entry for each price change.

### 5. Badges & Seals
- **Badges** (4 predefined): "Nuevo", "Más vendido", "Chef recomienda", "Oferta". Tenants can create custom badges with name + color + icon.
- **Seals** (6 predefined): "Orgánico", "Producto local", "Sin conservantes", "Artesanal", "Sustentable", "Comercio justo". Tenants can create custom seals.
- Product can have multiple badges and seals.

### 6. Public Menu API
- No authentication required. Rate-limited (60 req/min per IP).
- `GET /api/public/menu/{slug}` — Full menu for a branch (organized by categories).
- `GET /api/public/menu/{slug}/product/{id}` — Single product detail with allergens, cross-reactions, dietary info, ingredients.
- `GET /api/public/branches` — Active branches with slug, name, address, hours.
- `GET /api/public/allergens` — Full allergen catalog with cross-reactions.
- Redis cache with 5-minute TTL. Cache key pattern: `public:menu:{slug}`, `public:product:{slug}:{id}`, `public:branches:{tenant}`, `public:allergens:{tenant}`.
- Cache invalidation: on product/branch/allergen write operations, delete relevant cache keys.

## Scope Boundaries

### In Scope
- All 6 subsystems above
- Seed data migration for allergens, cooking methods, dietary profiles
- Dashboard CRUD UI for allergens, products (extended), branch pricing, badges, seals
- Public API with caching
- Batch price update with preview

### Out of Scope
- Nutritional information (calories, macros) — Sprint 5
- AI-powered allergen detection from ingredient text — future
- Menu versioning / scheduled menus — future
- Product images upload — already handled by media service
- Order system integration — Sprint 6+

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Allergen data accuracy | Legal liability if wrong | Seed EU 14 from official source; require admin confirmation on allergen assignment |
| Cache staleness | Customer sees outdated menu | 5min TTL + explicit invalidation on writes |
| Batch update mistakes | Wrong prices across branches | Mandatory preview step; audit log; undo within 5 minutes |
| Complex product form UX | Admin frustration, data entry errors | Tabbed interface, progressive disclosure, sensible defaults |
| N+1 queries on public menu | Slow public API | Eager loading with joinedload; denormalized cache |

## Dependencies

- Sprint 1-3 completed: tenant, branch, category, base product, auth, RBAC
- PostgreSQL with proper indexes on junction tables
- Redis available for caching

## Next Recommended

→ `sdd-spec` (detailed specification with models, API contracts, scenarios)
