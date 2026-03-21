# Modelo de Datos

> Fuente de verdad para: todas las fases SDD — foundation-auth, tenant-branch-core, menu-domain, table-session-domain, order-domain, billing-domain

---

## Jerarquía de entidades

```
Tenant (Restaurant)
  ├── CookingMethod, FlavorProfile, TextureProfile, CuisineType (catálogos tenant-scoped)
  ├── IngredientGroup → Ingredient → SubIngredient (tenant-scoped)
  └── Branch (N)
        ├── Category (N) → Subcategory (N) → Product (N)
        ├── BranchSector (N) → Table (N) → TableSession → Diner (N)
        │                   → WaiterSectorAssignment (diaria)
        │                   → Round → RoundItem → KitchenTicket
        ├── Check (table: app_check) → Charge → Allocation (FIFO) ← Payment
        └── ServiceCall

User ←→ UserBranchRole (M:N, roles: WAITER/KITCHEN/MANAGER/ADMIN)
Product ←→ BranchProduct (precio por sucursal en centavos)
Product ←→ ProductAllergen (M:N con presence_type + risk_level)
Customer ←→ Diner (1:N via customer_id, device tracking, preferencias implícitas)
```

### Diagrama ER textual completo

```
Tenant (1) ──→ (N) Branch
Tenant (1) ──→ (N) User
Tenant (1) ──→ (N) Product
Tenant (1) ──→ (N) Allergen
Tenant (1) ──→ (N) Customer

User (M) ←──→ (N) Branch  [via UserBranchRole + role]

Branch (1) ──→ (N) BranchSector ──→ (N) Table
Branch (1) ──→ (N) BranchProduct ←── (N) Product
Branch (1) ──→ (N) Category ──→ (N) Subcategory ──→ (N) Product

BranchSector (1) ──→ (N) WaiterSectorAssignment ←── (N) User[WAITER]

Table (1) ──→ (N) TableSession ──→ (N) Diner
                               ──→ (N) Round ──→ (N) RoundItem
                               ──→ (N) CartItem
                               ──→ (N) ServiceCall
                               ──→ (N) Check

Round (1) ──→ (N) RoundItem ──→ Product
Round (1) ──→ (N) KitchenTicket ──→ (N) KitchenTicketItem

Check (1) ──→ (N) Charge
Check (1) ──→ (N) Payment ──→ (N) Allocation ←── (N) Charge

Product (M) ←──→ (N) Allergen [via ProductAllergen]
Allergen (M) ←──→ (N) Allergen [via AllergenCrossReaction]

Diner (N) ──→ (1) Customer [opcional, via customer_id]

Promotion (M) ←──→ (N) Branch [via PromotionBranch]
Promotion (1) ──→ (N) PromotionItem ──→ Product
```

---

## Características transversales

Todas las entidades usan **AuditMixin**, que agrega:
- `is_active` (Boolean) — soft delete flag
- `created_at`, `updated_at`, `deleted_at` (DateTime con timezone)
- `created_by_id`, `created_by_email`, `updated_by_id`, `updated_by_email`, `deleted_by_id`, `deleted_by_email`

Patrones universales:
- **Multi-tenancy**: toda entidad tiene `tenant_id` (BigInteger FK)
- **Soft delete**: nunca se eliminan filas, se marca `is_active = False`
- **IDs**: `BigInteger` en todas las PKs y FKs

---

## Entidades principales

### Tenant (Restaurant)

Tabla: `tenant`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | Identificador del restaurante |
| name | Text | NOT NULL | Nombre del restaurante |
| slug | Text | UNIQUE, NOT NULL | Slug URL-friendly global |
| description | Text | nullable | Descripción |
| logo | Text | nullable | URL del logo |
| theme_color | Text | default="#f97316" | Color accent (naranja) |

**Relaciones:** → branches (1:N), → users (1:N), → products (1:N)

### Branch (Sucursal)

Tabla: `branch`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id | BigInteger | FK(tenant), NOT NULL, indexed | |
| name | Text | NOT NULL | Nombre del local |
| slug | Text | NOT NULL | Slug para URL pública — **NO es único globalmente** |
| address | Text | nullable | Dirección física |
| phone | Text | nullable | Teléfono |
| timezone | Text | default="America/Argentina/Mendoza" | |
| opening_time | Text | nullable | Horario apertura (ej: "09:00") |
| closing_time | Text | nullable | Horario cierre (ej: "23:00") |

**Relaciones:** → tenant, → tables (1:N), → sectors (1:N), → branch_products (1:N), → waiter_assignments (1:N), → promotions (M:N via PromotionBranch)

---

### User y roles

Tabla: `app_user` (nombre real de tabla — "user" es reservado en algunos contextos)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id | BigInteger | FK(tenant), NOT NULL, indexed | |
| email | Text | NOT NULL, UNIQUE(tenant_id, email) | Email único por tenant, no globalmente |
| password | Text | NOT NULL | Hash bcrypt |
| first_name | Text | nullable | |
| last_name | Text | nullable | |
| phone | Text | nullable | Teléfono del staff |
| dni | Text | nullable | Documento de identidad |
| hire_date | Text | nullable | Fecha de ingreso (YYYY-MM-DD) |

**Relaciones:** → tenant, → branch_roles (1:N via UserBranchRole), → sector_assignments (1:N via WaiterSectorAssignment)

#### UserBranchRole

Tabla: `user_branch_role` — Relación M:N entre User y Branch con rol asignado.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | BigInteger | PK |
| user_id | BigInteger | FK(app_user), NOT NULL |
| tenant_id | BigInteger | FK(tenant), NOT NULL |
| branch_id | BigInteger | FK(branch), NOT NULL |
| role | Text | WAITER, KITCHEN, MANAGER, ADMIN |

Un mismo usuario puede tener **roles diferentes en sucursales distintas**.

---

### Catálogos del Tenant

Todos con `tenant_id` para aislamiento multi-tenant.

- **CookingMethod** (`cooking_method`): métodos de cocción (horneado, frito, grillado, crudo, hervido, vapor, salteado, braseado)
- **FlavorProfile** (`flavor_profile`): perfiles de sabor
- **TextureProfile** (`texture_profile`): perfiles de textura
- **CuisineType** (`cuisine_type`): tipos de cocina

Estos catálogos se vinculan a productos via tablas intermedias `ProductCookingMethod`, `ProductFlavor`, `ProductTexture`.

---

### Menu Domain

#### Category

Tabla: `category`

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| id | BigInteger | PK |
| tenant_id | BigInteger | FK, NOT NULL |
| branch_id | BigInteger | FK(branch), NOT NULL |
| name | Text | NOT NULL, UNIQUE(branch_id, name) |
| icon | Text | nullable |
| image | Text | nullable |
| order | Integer | default=0 |

#### Subcategory

Tabla: `subcategory`

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| id | BigInteger | PK |
| tenant_id | BigInteger | FK, NOT NULL |
| category_id | BigInteger | FK(category), NOT NULL |
| name | Text | NOT NULL, UNIQUE(category_id, name) |
| image | Text | nullable |
| order | Integer | default=0 |

#### Product

Tabla: `product` — definición a nivel tenant; precio y disponibilidad son por sucursal via BranchProduct.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id | BigInteger | FK, NOT NULL | |
| name | Text | NOT NULL | |
| description | Text | nullable | |
| image | Text | nullable | URL validada contra SSRF |
| category_id | BigInteger | FK(category), NOT NULL | |
| subcategory_id | BigInteger | FK(subcategory), nullable | |
| featured | Boolean | indexed, default=False | |
| popular | Boolean | indexed, default=False | |
| badge | Text | nullable | "Nuevo", "Popular", etc. |
| recipe_id | BigInteger | FK(recipe), nullable | Receta vinculada (opcional) |
| inherits_from_recipe | Boolean | default=False | Hereda alérgenos/dietéticos de la receta |
| seal | Text | nullable | DEPRECATED — usar ProductDietaryProfile |
| allergen_ids | Text | nullable | DEPRECATED — usar ProductAllergen |

**Relaciones:** → branch_products (1:N), → product_allergens (1:N), → dietary_profile (1:1), → product_ingredients (1:N), → cooking_methods, → flavors, → textures (M:N via tablas intermedias), → round_items, → promotion_items

#### BranchProduct

Tabla: `branch_product` — precio y disponibilidad del producto por sucursal.

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| id | BigInteger | PK |
| tenant_id | BigInteger | FK, NOT NULL |
| branch_id | BigInteger | FK(branch), NOT NULL |
| product_id | BigInteger | FK(product), NOT NULL |
| price_cents | Integer | NOT NULL (en centavos) |
| is_available | Boolean | indexed, default=True |

**UNIQUE:** (branch_id, product_id) — un producto tiene un solo precio por sucursal.

#### ProductAllergen

Tabla: `product_allergen` — relación M:N entre Product y Allergen.

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| product_id | BigInteger | FK(product), NOT NULL |
| allergen_id | BigInteger | FK(allergen), NOT NULL |
| presence_type | Text (Enum) | contains, may_contain, free_from |
| risk_level | Text (Enum) | low, standard, high |

**UNIQUE:** (product_id, allergen_id, presence_type)

#### Allergen

Tabla: `allergen`

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| id | BigInteger | PK |
| tenant_id | BigInteger | FK, NOT NULL |
| name | Text | NOT NULL |
| icon | Text | nullable |
| description | Text | nullable |
| is_mandatory | Boolean | indexed |
| severity | Text (Enum) | mild, moderate, severe, life_threatening |

**AllergenCrossReaction** (`allergen_cross_reaction`): reacciones cruzadas entre alérgenos — M:N self-referential con `probability` (high, medium, low).

#### Ingredientes

- **IngredientGroup** (`ingredient_group`): clasificación (proteina, vegetal, lacteo, cereal, condimento, otro), unique(tenant_id, name)
- **Ingredient** (`ingredient`): catálogo del tenant, puede ser procesado, unique(tenant_id, name)
- **SubIngredient** (`sub_ingredient`): sub-ingredientes de un ingrediente procesado (ej: mayonesa → huevos, aceite, limón)
- **ProductIngredient** (`product_ingredient`): M:N entre Product e Ingredient con `is_main` y `notes`

---

### Table Session Domain

#### BranchSector

Tabla: `branch_sector` — zona/sector dentro de una sucursal para organizar mesas.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id | BigInteger | FK, NOT NULL | |
| branch_id | BigInteger | FK(branch), **nullable** | NULL = sector global disponible en todas las sucursales |
| name | Text | NOT NULL | "Interior", "Terraza", "VIP" |
| prefix | Text | NOT NULL | "INT", "TER", "VIP" — usado para generar códigos de mesa |
| display_order | Integer | default=0 | |

**UNIQUE:** (tenant_id, branch_id, prefix). Índice parcial adicional para sectores globales (branch_id IS NULL).

**Un sector con branch_id=NULL es global** y está disponible para todas las sucursales del tenant.

#### WaiterSectorAssignment

Tabla: `waiter_sector_assignment` — asignación diaria de mozos a sectores.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| sector_id | BigInteger | FK(branch_sector), NOT NULL | |
| waiter_id | BigInteger | FK(app_user), NOT NULL | |
| assignment_date | Date | NOT NULL, indexed | Fecha de la asignación |
| shift | Text | nullable | "MORNING", "AFTERNOON", "NIGHT" o NULL = todo el día |

**UNIQUE:** (tenant_id, branch_id, sector_id, waiter_id, assignment_date, shift)

Un mozo puede ser asignado a **múltiples sectores** en el mismo día/turno (constraint exclusivo anterior fue eliminado).

#### Table

Tabla: `restaurant_table` (renombrada — "table" es reservado en SQL)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| code | Text | NOT NULL | "INT-01", "TER-03" — generado con prefix del sector |
| capacity | Integer | default=4 | |
| sector_id | BigInteger | FK(branch_sector), nullable | FK al nuevo sistema de sectores |
| sector | Text | nullable | Campo legacy — mantener por compatibilidad |
| status | Text (Enum) | indexed | FREE, ACTIVE, PAYING, OUT_OF_SERVICE |

**Importante:** `code` NO es único globalmente ni por branch. Se requiere `branch_slug` para identificar una mesa por código.

#### TableSession

Tabla: `table_session`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| table_id | BigInteger | FK(restaurant_table), NOT NULL | |
| status | Text (Enum) | indexed | OPEN, PAYING, CLOSED |
| assigned_waiter_id | BigInteger | FK(app_user), nullable | |
| opened_at | DateTime | NOT NULL, server_default=now() | |
| closed_at | DateTime | nullable | |
| opened_by | Text (Enum) | NOT NULL, default="DINER" | DINER (escaneo QR) o WAITER (activación manual) |
| opened_by_waiter_id | BigInteger | FK(app_user), nullable | Solo cuando opened_by="WAITER" |
| cart_version | Integer | default=0 | Versión para optimistic locking del carrito compartido |

**Relaciones:** → table, → rounds (1:N), → service_calls (1:N), → checks (1:N), → diners (1:N), → cart_items (1:N)

#### CartItem

Tabla: `cart_item` — ítems del carrito compartido antes de enviarse como round.

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| session_id | BigInteger | FK(table_session), NOT NULL |
| diner_id | BigInteger | FK(diner), NOT NULL |
| product_id | BigInteger | FK(product), NOT NULL |
| quantity | Integer | CHECK > 0 AND <= 99 |
| notes | Text | nullable |

**UNIQUE:** (session_id, diner_id, product_id)

#### ServiceCall

Tabla: `service_call`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| table_session_id | BigInteger | FK(table_session), NOT NULL | |
| type | Text (Enum) | default="WAITER_CALL" | WAITER_CALL, PAYMENT_HELP, OTHER |
| status | Text (Enum) | indexed | OPEN, ACKED, CLOSED |
| acked_at | DateTime | nullable | |
| acked_by_user_id | BigInteger | FK(app_user), nullable | |

---

### Order Domain

#### Round

Tabla: `round`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| table_session_id | BigInteger | FK(table_session), NOT NULL | |
| round_number | Integer | NOT NULL | Número secuencial dentro de la sesión |
| status | Text (Enum) | indexed | DRAFT, SUBMITTED, IN_KITCHEN, READY, SERVED, CANCELED |
| submitted_at | DateTime | indexed | Timestamp de envío |
| idempotency_key | Text | UNIQUE(table_session_id, idempotency_key) | Previene envíos duplicados |
| submitted_by | Text (Enum) | NOT NULL, default="DINER" | DINER (pwaMenu) o WAITER (pwaWaiter) |
| submitted_by_waiter_id | BigInteger | FK(app_user), nullable | Solo cuando submitted_by="WAITER" |
| confirmed_by_user_id | BigInteger | FK(app_user), nullable | Staff que confirmó PENDING → CONFIRMED |

**Flujo de estado con restricción de rol:**
```
PENDING → CONFIRMED → SUBMITTED → IN_KITCHEN → READY → SERVED
(Diner)   (Waiter)   (Admin/Mgr)   (Kitchen)  (Kitchen) (Staff)
```

Kitchen **NO ve** órdenes PENDING ni CONFIRMED. Solo ve SUBMITTED en adelante.

**Nota:** El modelo en DB usa `DRAFT` en lugar de `PENDING`; el flujo documentado en CLAUDE.md usa `PENDING`. Verificar constantes en `shared/config/constants.py` para el valor exacto en uso.

#### RoundItem

Tabla: `round_item`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| round_id | BigInteger | FK(round), NOT NULL | |
| product_id | BigInteger | FK(product), NOT NULL | |
| diner_id | BigInteger | FK(diner), nullable | Quién pidió este ítem |
| qty | Integer | CHECK > 0 | |
| unit_price_cents | Integer | CHECK >= 0 | Precio al momento del pedido (histórico) |
| notes | Text | nullable | Indicaciones especiales |

#### KitchenTicket

Tabla: `kitchen_ticket` — agrupa ítems de un round por estación de preparación.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| round_id | BigInteger | FK(round), NOT NULL | |
| station | Text | NOT NULL, indexed | BAR, HOT_KITCHEN, COLD_KITCHEN, GRILL, etc. |
| status | Text (Enum) | indexed | PENDING, IN_PROGRESS, READY, DELIVERED |
| priority | Integer | default=0 | Mayor valor = más urgente |
| notes | Text | nullable | |
| started_at / completed_at / delivered_at | DateTime | nullable | Timestamps de tracking |

#### KitchenTicketItem

Tabla: `kitchen_ticket_item` — vínculo entre KitchenTicket y RoundItem.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| ticket_id | BigInteger | FK(kitchen_ticket) |
| round_item_id | BigInteger | FK(round_item) |
| qty | Integer | Puede ser parcial |
| status | Text (Enum) | PENDING, IN_PROGRESS, READY |

---

### Billing Domain

#### Check

Tabla: `app_check` (renombrada — "CHECK" es palabra reservada SQL)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| table_session_id | BigInteger | FK(table_session), NOT NULL | |
| status | Text (Enum) | indexed | OPEN, REQUESTED, IN_PAYMENT, PAID, FAILED |
| total_cents | Integer | CHECK >= 0, default=0 | |
| paid_cents | Integer | CHECK >= 0 AND <= total_cents, default=0 | |

**Relaciones:** → payments (1:N), → charges (1:N)

#### Charge

Tabla: `charge` — cargo asignado a un diner específico para split payment.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| check_id | BigInteger | FK(app_check), NOT NULL | |
| diner_id | BigInteger | FK(diner), nullable | Responsable del cargo (nullable para ítems compartidos) |
| round_item_id | BigInteger | FK(round_item), NOT NULL | |
| amount_cents | Integer | CHECK > 0 | |
| description | Text | NOT NULL | |

#### Payment

Tabla: `payment`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| check_id | BigInteger | FK(app_check), NOT NULL | |
| payer_diner_id | BigInteger | FK(diner), nullable | Quién pagó |
| provider | Text | default="CASH" | CASH, MERCADO_PAGO |
| status | Text (Enum) | indexed | PENDING, APPROVED, REJECTED |
| amount_cents | Integer | CHECK > 0 | |
| external_id | Text | nullable | ID de Mercado Pago |
| payment_category | Text (Enum) | NOT NULL, default="DIGITAL" | DIGITAL (MercadoPago) o MANUAL (registrado por mozo) |
| registered_by | Text (Enum) | NOT NULL, default="SYSTEM" | SYSTEM, DINER, WAITER |
| registered_by_waiter_id | BigInteger | FK(app_user), nullable | Solo cuando registered_by="WAITER" |
| manual_method | Text | nullable | CASH, CARD_PHYSICAL, TRANSFER_EXTERNAL, OTHER_MANUAL |
| manual_notes | Text | nullable | Notas para pagos manuales |

#### Allocation

Tabla: `allocation` — vincula Payment con Charges específicos (FIFO).

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| id | BigInteger | PK |
| tenant_id | BigInteger | FK, NOT NULL |
| payment_id | BigInteger | FK(payment), NOT NULL |
| charge_id | BigInteger | FK(charge), NOT NULL |
| amount_cents | Integer | CHECK > 0 |

Un pago puede cubrir múltiples cargos; un cargo puede ser cubierto por múltiples pagos.

---

### Customer Domain

#### Diner

Tabla: `diner` — persona en una sesión de mesa.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id / branch_id | BigInteger | FK, NOT NULL | |
| session_id | BigInteger | FK(table_session), NOT NULL | |
| name | Text | NOT NULL | Nombre de display |
| color | Text | NOT NULL | Color hex para UI (#RRGGBB) |
| local_id | Text | indexed, UNIQUE(session_id, local_id) | UUID del frontend para sincronización |
| joined_at | DateTime | NOT NULL, server_default=now() | |
| device_id | Text | indexed, nullable | UUID persistente del dispositivo |
| device_fingerprint | Text | indexed, nullable | Hash de fingerprint del browser |
| implicit_preferences | Text (JSON) | nullable | `{"excluded_allergen_ids": [1,3], "dietary": ["vegan"]}` |
| customer_id | BigInteger | FK(customer), nullable, indexed | Link opcional al Customer identificado |

**Relaciones:** → session, → round_items (1:N), → charges (1:N), → customer (N:1, opcional), → cart_items (1:N)

#### Customer

Tabla: `customer` — cliente identificado con consentimiento explícito (Fase 4).

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | BigInteger | PK | |
| tenant_id | BigInteger | FK, NOT NULL | |
| name | Text | nullable | |
| phone | Text | nullable, UNIQUE(tenant_id, phone) cuando no es null | |
| email | Text | nullable, UNIQUE(tenant_id, email) cuando no es null | |
| first_visit_at / last_visit_at | DateTime | server_default=now() | |
| total_visits | Integer | default=1 | |
| total_spent_cents | BigInteger | default=0 | |
| avg_ticket_cents | Integer | default=0 | |
| excluded_allergen_ids | Text (JSON) | nullable | IDs de alérgenos a excluir |
| dietary_preferences | Text (JSON) | nullable | ["vegan", "gluten_free"] |
| excluded_cooking_methods | Text (JSON) | nullable | ["frito", "horneado"] |
| favorite_product_ids | Text (JSON) | nullable | Top 5 product IDs por frecuencia |
| segment | Text | indexed, default="new" | new, occasional, regular, vip, at_risk, churned |
| churn_risk_score | Float | nullable | 0.0 (leal) a 1.0 (alto riesgo) |
| predicted_next_visit | DateTime | nullable | |
| consent_remember | Boolean | default=True | Recordar preferencias |
| consent_marketing | Boolean | default=False | Permitir marketing |
| consent_date | DateTime | server_default=now() | |
| ai_personalization_enabled | Boolean | default=True | |
| birthday_month / birthday_day | Integer | nullable | Para saludos personalizados |
| device_ids | Text (JSON) | nullable | ["uuid-1", "uuid-2"] — múltiples dispositivos por customer |

---

### Outbox (Eventos Transaccionales)

Tabla: `outbox_event`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | BigInteger | PK |
| tenant_id | BigInteger | FK |
| event_type | Text | Tipo de evento (CHECK_REQUESTED, PAYMENT_APPROVED, etc.) |
| payload | JSON | Datos del evento |
| created_at | DateTime | Timestamp |
| published | Boolean | default=False |
| published_at | DateTime | nullable |

Usado para eventos críticos que no pueden perderse (financieros, pagos, rounds SUBMITTED/READY).

---

### Exclusiones de Catálogo

- **BranchCategoryExclusion** (`branch_category_exclusion`): oculta una categoría en una sucursal específica sin eliminarla del tenant.
- **BranchSubcategoryExclusion** (`branch_subcategory_exclusion`): idem para subcategorías.

---

## Índices principales

| Tabla | Índice | Propósito |
|-------|--------|-----------|
| Todas | `tenant_id` | Filtrado multi-tenant |
| Todas | `is_active` | Filtrado soft delete |
| restaurant_table | `status`, `(branch_id, status)` | Búsqueda por estado |
| table_session | `status`, `(branch_id, status)` | Sesiones activas |
| round | `status`, `submitted_at`, `(branch_id, status)`, `(status, submitted_at)` | Filtro y cola de cocina |
| app_check | `status`, `(branch_id, status)` | Cuentas activas |
| payment | `status` | Pagos pendientes |
| branch_product | `is_available`, `(branch_id, product_id)` | Productos disponibles |
| product | `featured`, `popular` | Destacados |
| diner | `local_id`, `device_id`, `device_fingerprint`, `(session_id, local_id)` | Lookup rápido e idempotencia |
| customer | `segment` | Segmentación |
| waiter_sector_assignment | `(assignment_date, branch_id)` | Asignaciones del día |
| kitchen_ticket | `(station, status)`, `(branch_id, status)` | Cola de cocina por estación |
| allocation | `(charge_id, payment_id)` | Consultas de balance |

---

## Convenciones importantes

### Nombres de tablas que evitan palabras reservadas SQL

| Clase SQLAlchemy | Nombre real de tabla | Razón |
|-----------------|----------------------|-------|
| `Check` | `app_check` | CHECK es palabra reservada SQL (usado en constraints) |
| `Table` | `restaurant_table` | TABLE es palabra reservada SQL |
| `User` | `app_user` | USER es palabra reservada en PostgreSQL |

### Precios en centavos

Todos los precios y montos se almacenan como **enteros en centavos**:
- `$125.50` → `12550`
- `price_cents`, `amount_cents`, `total_cents`, `paid_cents`, `unit_price_cents`

### IDs

- **Backend**: `BigInteger` (enteros)
- **Frontend**: `string` (los IDs se convierten a string en el cliente)

---

## Conversiones frontend-backend

| Dato | Backend | Frontend | Conversión |
|------|---------|----------|------------|
| IDs de entidades | `number` (BigInteger) | `string` | `String(backendId)` / `parseInt(frontendId, 10)` |
| Precios | `number` en centavos (`int`) | `number` en pesos (`float`) | `backendCents / 100` / `Math.round(price * 100)` |
| Estado de sesión | `UPPERCASE` (ej: `OPEN`) | `lowercase` (ej: `open`) | `.toLowerCase()` / `.toUpperCase()` |

---

## Gotchas y edge cases

- **Códigos de mesa NO son únicos por sucursal**: `Table.code` (ej: "INT-01") no tiene unique constraint global. Para identificar una mesa por código se necesita `branch_slug` además del código. El endpoint usa `/api/tables/code/{code}/session` pero requiere contexto de sucursal.

- **`app_check` — nombre de tabla**: la clase Python se llama `Check`, pero la tabla en DB es `app_check`. Toda FK a esta tabla referencia `app_check.id`, no `check.id`.

- **BranchProduct para precios**: el `Product` a nivel tenant NO tiene precio. El precio está SIEMPRE en `BranchProduct.price_cents`. Un producto sin entrada en `branch_product` no aparece en esa sucursal.

- **WaiterSectorAssignment es DIARIA**: la asignación de un mozo a un sector es por fecha (`assignment_date`). Para que un mozo pueda loguearse y trabajar en una sucursal, DEBE tener una asignación con la fecha de HOY. El endpoint `/api/waiter/verify-branch-assignment?branch_id={id}` verifica esto en el login.

- **Diner rastrea dispositivo sin Customer**: el `Diner` tiene `device_id` y `device_fingerprint` incluso cuando `customer_id` es NULL. El tracking de dispositivo es Fase 1 (automático); la vinculación con `Customer` es Fase 4 (con consentimiento explícito).

- **Round status DRAFT vs PENDING**: el modelo en DB tiene `DRAFT` como valor por defecto del status. La documentación de flujo usa `PENDING`. Verificar `shared/config/constants.py` (`RoundStatus`) para el mapping exacto en producción.

- **Sectores globales (branch_id IS NULL)**: `BranchSector` con `branch_id=NULL` es un sector global disponible para todas las sucursales del tenant. El unique constraint sobre `prefix` usa un índice parcial separado para este caso (NULL no se considera igual a NULL en PostgreSQL).

- **Waiters asignados a múltiples sectores**: el constraint exclusivo que impedía a un mozo estar en más de un sector fue eliminado. Un mozo puede tener asignaciones en múltiples sectores para el mismo día/turno.

- **CartItem es pre-round**: el carrito compartido (`CartItem`) vive en `TableSession` y es sincronizado en tiempo real via WebSocket. Al hacer submit, los ítems del carrito se convierten en un `Round` con sus `RoundItem`s. El `cart_version` en `TableSession` previene race conditions via optimistic locking.

- **RoundItem.unit_price_cents almacena precio histórico**: al crear un `RoundItem`, se copia el precio del momento desde `BranchProduct.price_cents`. Esto garantiza que cambios de precio futuros no afecten órdenes ya enviadas.

- **Customer.device_ids es JSON array como Text**: los campos JSON en `Customer` y `Diner` se almacenan como `Text` (string JSON serializado), no como columna JSON nativa de PostgreSQL. Deserializar con `json.loads()` antes de usar.

- **Email de User es único por tenant, no global**: `UniqueConstraint("tenant_id", "email")` — el mismo email puede existir en distintos tenants. No hay unique global en `email`.

- **Charge.diner_id es nullable**: para ítems compartidos entre comensales, el cargo puede no estar asignado a un diner específico.

- **Allocation implementa FIFO**: los pagos se asignan a cargos en orden de creación (FIFO). Un pago puede cubrir múltiples cargos y un cargo puede ser cubierto por múltiples pagos.
