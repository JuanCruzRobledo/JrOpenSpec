---
sprint: 13
artifact: proposal
status: complete
---

# Proposal: Recetas, Ingredientes y Promociones

## Intent

Build the kitchen's technical documentation system (ingredient catalog + recipe cards) and a promotion engine that supports time-based promotional offers — giving the business tools for cost control, kitchen standardization, and marketing.

## Scope

### In Scope
- Ingredient catalog: groups (vegetales, proteinas, lacteos, etc.), ingredients with processing state, sub-ingredients for processed items
- Recipe system: full technical cards with prep/cooking times, ingredient quantities, step-by-step instructions, chef notes, categorization (cuisine, allergens, dietary), sensory profiles, safety info, cost calculation
- Promotion types: 4 predefined (Happy Hour, Combo Familiar, 2x1, Descuento) + custom types
- Promotions: name, type, combo price, image, date/time restrictions, multi-branch, product composition with quantities, strict temporal validation, dynamic status (active/scheduled/expired)
- Active promotions API for pwaMenu consumption
- Featured promotions section in diner menu

### Out of Scope
- Inventory/stock management (quantity tracking, purchase orders)
- Automatic cost updates from supplier pricing
- Recipe versioning / history
- Kitchen display integration with recipes
- Loyalty programs / points

## Modules

| Module | Description |
|--------|-------------|
| `ingredients` | Ingredient groups, ingredients, sub-ingredients CRUD |
| `recipes` | Recipe CRUD with full technical card data |
| `promotion-types` | Promotion type management (predefined + custom) |
| `promotions` | Promotion CRUD with temporal rules + composition |
| `promos-api` | Active promotions endpoint for pwaMenu |
| `promos-pwamenu` | Featured promotions section in diner menu |

## Approach

1. **Ingredient catalog** — groups CRUD, ingredients CRUD with group assignment, sub-ingredients for processed items
2. **Recipe system** — full CRUD with all technical card fields, auto-calculated total time, cost engine
3. **Promotion types** — 4 seeded types + custom CRUD
4. **Promotions** — CRUD with date/time rules, multi-branch, product composition
5. **Temporal validation** — strict enforcement: promotions only active during configured windows
6. **Active promos API** — filtered by current time + branch
7. **pwaMenu integration** — featured section in menu with promo cards

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Recipe data model too rigid for diverse cuisines | Medium — awkward data entry | Flexible JSON fields for sensory profiles and safety; optional fields where possible |
| Temporal promotion conflicts (overlapping promos on same product) | Medium — confusing pricing | Validate no overlapping promos on same product at same branch during same time window |
| Large ingredient catalog slowing recipe creation | Low — UX friction | Autocomplete search, recent ingredients, favorites |
| Cost calculation drift from actual costs | Medium — inaccurate margins | Mark costs as "estimated" with last-updated timestamp; flag stale costs |
| Timezone issues in temporal promotion rules | High — promotions active/inactive at wrong times | Store all times in UTC; convert to branch timezone for display; server-side validation always in UTC |

## Rollback

- All entities are new tables — rollback by dropping and removing endpoints
- Promotion display in pwaMenu is conditional — no promotions = no section shown
- Seeded promotion types can be re-seeded idempotently
- No modifications to existing product/order models
