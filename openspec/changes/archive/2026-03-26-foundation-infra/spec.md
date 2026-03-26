---
change: foundation-infra
phase: 1
artifact: spec
source: sdd-otro/sprint-1-infra
date: 2026-03-23
status: approved
---

# SDD Spec: Sprint 1 — Infraestructura y Modelo de Datos

## 1. Requirements (RFC 2119)

### 1.1 Monorepo Structure

- The root directory MUST contain: `rest_api/`, `ws_gateway/`, `shared/`, `pwa_menu/`, `pwa_waiter/`, `dashboard/`
- `shared/` MUST be a Python package installable via `pip install -e .`
- `shared/` MUST contain `__init__.py` at the package root and in every subpackage
- Each backend service (rest_api, ws_gateway) MUST list `shared` as a dependency
- Frontend directories (pwa_menu, pwa_waiter, dashboard) SHOULD contain a minimal `package.json` stub
- The root MUST contain: `docker-compose.yml`, `pyproject.toml` (workspace), `.pre-commit-config.yaml`, `alembic.ini`
- `rest_api/` MUST contain: `main.py`, `Dockerfile`, `pyproject.toml`, `app/` directory
- `ws_gateway/` MUST contain at minimum: `Dockerfile`, `pyproject.toml`, `main.py` (stub)

### 1.2 Docker Compose

- Docker Compose MUST define services: `postgres`, `redis`, `api`, `gateway`
- `postgres` MUST use image `pgvector/pgvector:0.8.0-pg16` (or latest compatible)
- `postgres` MUST expose port 5432 on host
- `postgres` MUST define environment variables: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `postgres` MUST have a health check using `pg_isready`
- `postgres` MUST use a named volume for data persistence
- `redis` MUST use image `redis:7-alpine`
- `redis` MUST expose port 6379 on host
- `redis` MUST have a health check using `redis-cli ping`
- `api` service MUST build from `rest_api/Dockerfile`
- `api` MUST expose port 8000 on host
- `api` MUST depend on `postgres` and `redis` with `condition: service_healthy`
- `api` MUST mount `shared/` as a volume for development hot-reload
- `gateway` service MUST build from `ws_gateway/Dockerfile`
- `gateway` MUST expose port 8001 on host
- All services MUST be on the same Docker network `buen-sabor-net`
- Docker Compose SHOULD support profiles: `dev` (default), `test`

### 1.3 Database Infrastructure

- `shared/infrastructure/db.py` MUST export: `engine`, `async_session_factory`, `get_db`, `safe_commit`
- `engine` MUST be an `AsyncEngine` created with `create_async_engine` using `asyncpg` driver
- `engine` MUST configure: `pool_size=20`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800`, `echo=False` (configurable via env)
- `async_session_factory` MUST be an `async_sessionmaker` bound to the engine with `expire_on_commit=False`
- `get_db` MUST be an async generator yielding `AsyncSession` for FastAPI Depends injection
- `get_db` MUST properly close the session in the finally block
- `safe_commit(session)` MUST attempt `session.commit()`, catch `IntegrityError`, call `session.rollback()`, and raise a domain-specific exception
- `safe_commit` MUST also catch `SQLAlchemyError` as a fallback, rollback, and raise
- Database URL MUST be read from environment variable `DATABASE_URL`
- Database URL format MUST be: `postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}`
- Redis URL MUST be read from environment variable `REDIS_URL`

### 1.4 Configuration

- `shared/config.py` MUST define a Pydantic `Settings` class using `pydantic-settings`
- Settings MUST include: `DATABASE_URL`, `REDIS_URL`, `ENVIRONMENT` (dev/staging/prod), `DEBUG` (bool), `API_PREFIX` ("/api"), `LOG_LEVEL` (default "INFO")
- Settings MUST load from environment variables with `.env` file support
- Settings MUST be instantiated as a singleton via `@lru_cache`

### 1.5 AuditMixin

- `shared/models/mixins.py` MUST define `AuditMixin` as a SQLAlchemy mixin class
- AuditMixin MUST include these columns:
  - `created_at`: `DateTime(timezone=True)`, NOT NULL, server_default=`func.now()`
  - `updated_at`: `DateTime(timezone=True)`, NOT NULL, server_default=`func.now()`, onupdate=`func.now()`
  - `deleted_at`: `DateTime(timezone=True)`, NULLABLE, default=None
  - `created_by`: `Integer`, NULLABLE, `ForeignKey("users.id")`
  - `updated_by`: `Integer`, NULLABLE, `ForeignKey("users.id")`
  - `deleted_by`: `Integer`, NULLABLE, `ForeignKey("users.id")`
  - `is_active`: `Boolean`, NOT NULL, default=True
- AuditMixin MUST provide a `soft_delete(user_id: int | None = None)` method that sets `deleted_at=now()`, `deleted_by=user_id`, `is_active=False`
- AuditMixin MUST provide a `restore()` method that sets `deleted_at=None`, `deleted_by=None`, `is_active=True`

### 1.6 Base Model

- `shared/models/base.py` MUST define `Base = declarative_base()`
- `shared/models/base.py` MUST define `BaseModel(AuditMixin, Base)` as abstract base for all domain models
- `BaseModel` MUST declare `__abstract__ = True`
- `BaseModel` MUST auto-generate `__tablename__` from class name (CamelCase to snake_case plural)
- `BaseModel` MUST include `id: Mapped[int]` as primary key with `autoincrement=True`

### 1.7 Domain Models

All models MUST inherit from `BaseModel`. All models MUST use `Mapped[]` type annotations (SQLAlchemy 2.0 style). All foreign keys MUST use `mapped_column(ForeignKey(...))`. All relationships MUST use `relationship()` with explicit `back_populates`.

#### 1.7.1 Core Domain

**Tenant**
- `id`: Integer, PK
- `name`: String(100), NOT NULL, UNIQUE
- `slug`: String(100), NOT NULL, UNIQUE, INDEX
- `logo_url`: String(500), NULLABLE
- `is_active`: Boolean (inherited from AuditMixin)
- Relationships: `branches`, `users`

**Branch**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL
- `slug`: String(100), NOT NULL, INDEX
- `address`: String(300), NULLABLE
- `phone`: String(50), NULLABLE
- `latitude`: Float, NULLABLE
- `longitude`: Float, NULLABLE
- `timezone`: String(50), NOT NULL, default="America/Argentina/Buenos_Aires"
- `is_open`: Boolean, NOT NULL, default=False
- Constraint: UNIQUE(tenant_id, slug)
- Relationships: `tenant`, `sectors`, `branch_products`, `waiter_assignments`

**User**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `email`: String(255), NOT NULL, UNIQUE
- `hashed_password`: String(255), NOT NULL
- `first_name`: String(100), NOT NULL
- `last_name`: String(100), NOT NULL
- `phone`: String(50), NULLABLE
- `avatar_url`: String(500), NULLABLE
- `is_superadmin`: Boolean, NOT NULL, default=False
- `last_login_at`: DateTime(timezone=True), NULLABLE
- Relationships: `tenant`, `branch_roles`

**UserBranchRole**
- `id`: Integer, PK
- `user_id`: Integer, FK(users.id), NOT NULL, INDEX
- `branch_id`: Integer, FK(branches.id), NOT NULL, INDEX
- `role`: String(50), NOT NULL (enum: owner, manager, chef, waiter, cashier, kitchen_display)
- Constraint: UNIQUE(user_id, branch_id, role)
- Relationships: `user`, `branch`

#### 1.7.2 Catalog Domain

**Category**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL
- `slug`: String(100), NOT NULL, INDEX
- `description`: Text, NULLABLE
- `image_url`: String(500), NULLABLE
- `display_order`: Integer, NOT NULL, default=0
- Constraint: UNIQUE(tenant_id, slug)
- Relationships: `tenant`, `subcategories`

**Subcategory**
- `id`: Integer, PK
- `category_id`: Integer, FK(categories.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL
- `slug`: String(100), NOT NULL
- `description`: Text, NULLABLE
- `image_url`: String(500), NULLABLE
- `display_order`: Integer, NOT NULL, default=0
- Constraint: UNIQUE(category_id, slug)
- Relationships: `category`, `products`

**Product**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `subcategory_id`: Integer, FK(subcategories.id), NOT NULL, INDEX
- `name`: String(200), NOT NULL
- `slug`: String(200), NOT NULL, INDEX
- `description`: Text, NULLABLE
- `image_url`: String(500), NULLABLE
- `base_price_cents`: Integer, NOT NULL (price in cents)
- `prep_time_minutes`: Integer, NULLABLE
- `is_available`: Boolean, NOT NULL, default=True
- `is_visible_in_menu`: Boolean, NOT NULL, default=True
- `cooking_method_id`: Integer, FK(cooking_methods.id), NULLABLE
- `flavor_profile_id`: Integer, FK(flavor_profiles.id), NULLABLE
- `texture_profile_id`: Integer, FK(texture_profiles.id), NULLABLE
- `cuisine_type_id`: Integer, FK(cuisine_types.id), NULLABLE
- Constraint: UNIQUE(tenant_id, slug)
- Relationships: `tenant`, `subcategory`, `branch_products`, `product_allergens`, `recipe`, `cooking_method`, `flavor_profile`, `texture_profile`, `cuisine_type`

**BranchProduct**
- `id`: Integer, PK
- `branch_id`: Integer, FK(branches.id), NOT NULL, INDEX
- `product_id`: Integer, FK(products.id), NOT NULL, INDEX
- `price_override_cents`: Integer, NULLABLE (NULL = use base_price)
- `is_available`: Boolean, NOT NULL, default=True
- `stock_quantity`: Integer, NULLABLE (NULL = unlimited)
- Constraint: UNIQUE(branch_id, product_id)
- Relationships: `branch`, `product`

**Allergen**
- `id`: Integer, PK
- `name`: String(100), NOT NULL, UNIQUE
- `code`: String(20), NOT NULL, UNIQUE (e.g., "gluten", "crustaceans", "eggs")
- `icon_url`: String(500), NULLABLE
- `description`: Text, NULLABLE
- Relationships: `product_allergens`
- Note: NOT tenant-specific — global table with the 14 EU allergens

**ProductAllergen**
- `id`: Integer, PK
- `product_id`: Integer, FK(products.id), NOT NULL, INDEX
- `allergen_id`: Integer, FK(allergens.id), NOT NULL, INDEX
- `severity`: String(20), NOT NULL, default="contains" (enum: contains, may_contain, trace)
- Constraint: UNIQUE(product_id, allergen_id)
- Relationships: `product`, `allergen`

#### 1.7.3 Profiles Domain

**CookingMethod**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL (e.g., "A la parrilla", "Frito", "Al horno")
- Constraint: UNIQUE(tenant_id, name)

**FlavorProfile**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL (e.g., "Dulce", "Salado", "Umami", "Picante")
- Constraint: UNIQUE(tenant_id, name)

**TextureProfile**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL (e.g., "Crocante", "Cremoso", "Suave")
- Constraint: UNIQUE(tenant_id, name)

**CuisineType**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL (e.g., "Argentina", "Italiana", "Japonesa")
- Constraint: UNIQUE(tenant_id, name)

#### 1.7.4 Ingredients Domain

**IngredientGroup**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL (e.g., "Lácteos", "Verduras", "Carnes")
- Constraint: UNIQUE(tenant_id, name)
- Relationships: `ingredients`

**Ingredient**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `group_id`: Integer, FK(ingredient_groups.id), NOT NULL, INDEX
- `name`: String(200), NOT NULL
- `unit`: String(50), NOT NULL (e.g., "kg", "lt", "unidad")
- `cost_per_unit_cents`: Integer, NOT NULL, default=0
- `stock_quantity`: Numeric(10,3), NULLABLE
- `min_stock_threshold`: Numeric(10,3), NULLABLE
- Constraint: UNIQUE(tenant_id, name)
- Relationships: `group`, `sub_ingredients`, `recipe_ingredients`

**SubIngredient**
- `id`: Integer, PK
- `parent_ingredient_id`: Integer, FK(ingredients.id), NOT NULL, INDEX
- `child_ingredient_id`: Integer, FK(ingredients.id), NOT NULL, INDEX
- `quantity`: Numeric(10,3), NOT NULL
- `unit`: String(50), NOT NULL
- Constraint: UNIQUE(parent_ingredient_id, child_ingredient_id)
- Relationships: `parent_ingredient`, `child_ingredient`

#### 1.7.5 Room Domain

**Sector**
- `id`: Integer, PK
- `branch_id`: Integer, FK(branches.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL (e.g., "Salón Principal", "Terraza", "Barra")
- `display_order`: Integer, NOT NULL, default=0
- Constraint: UNIQUE(branch_id, name)
- Relationships: `branch`, `tables`, `waiter_assignments`

**Table**
- `id`: Integer, PK
- `sector_id`: Integer, FK(sectors.id), NOT NULL, INDEX
- `number`: String(20), NOT NULL (e.g., "1", "2A", "VIP-1")
- `capacity`: Integer, NOT NULL, default=4
- `status`: String(20), NOT NULL, default="available" (enum: available, occupied, reserved, blocked)
- `pos_x`: Float, NULLABLE (for floor plan layout)
- `pos_y`: Float, NULLABLE
- Constraint: UNIQUE(sector_id, number)
- Relationships: `sector`, `sessions`

**TableSession**
- `id`: Integer, PK
- `table_id`: Integer, FK(tables.id), NOT NULL, INDEX
- `opened_at`: DateTime(timezone=True), NOT NULL, server_default=func.now()
- `closed_at`: DateTime(timezone=True), NULLABLE
- `opened_by`: Integer, FK(users.id), NOT NULL
- `closed_by`: Integer, FK(users.id), NULLABLE
- `guest_count`: Integer, NOT NULL, default=1
- `status`: String(20), NOT NULL, default="active" (enum: active, closed, cancelled)
- Relationships: `table`, `diners`, `check`, `opener`, `closer`

**Diner**
- `id`: Integer, PK
- `session_id`: Integer, FK(table_sessions.id), NOT NULL, INDEX
- `name`: String(100), NULLABLE (e.g., "Comensal 1" or user-given name)
- `seat_number`: Integer, NULLABLE
- Constraint: UNIQUE(session_id, seat_number) WHERE seat_number IS NOT NULL
- Relationships: `session`, `round_items`

#### 1.7.6 Orders Domain

**Round**
- `id`: Integer, PK
- `session_id`: Integer, FK(table_sessions.id), NOT NULL, INDEX
- `round_number`: Integer, NOT NULL
- `status`: String(20), NOT NULL, default="draft" (enum: draft, sent, preparing, ready, delivered, cancelled)
- `sent_at`: DateTime(timezone=True), NULLABLE
- `sent_by`: Integer, FK(users.id), NULLABLE
- Constraint: UNIQUE(session_id, round_number)
- Relationships: `session`, `items`, `sender`

**RoundItem**
- `id`: Integer, PK
- `round_id`: Integer, FK(rounds.id), NOT NULL, INDEX
- `product_id`: Integer, FK(products.id), NOT NULL, INDEX
- `diner_id`: Integer, FK(diners.id), NULLABLE
- `quantity`: Integer, NOT NULL, default=1
- `unit_price_cents`: Integer, NOT NULL (snapshot at order time)
- `notes`: Text, NULLABLE (e.g., "sin cebolla", "bien cocido")
- `status`: String(20), NOT NULL, default="pending" (enum: pending, preparing, ready, delivered, cancelled)
- Relationships: `round`, `product`, `diner`, `kitchen_ticket`

**KitchenTicket**
- `id`: Integer, PK
- `round_item_id`: Integer, FK(round_items.id), NOT NULL, INDEX
- `station`: String(50), NOT NULL (e.g., "cocina", "parrilla", "barra")
- `priority`: Integer, NOT NULL, default=0 (higher = more urgent)
- `status`: String(20), NOT NULL, default="pending" (enum: pending, in_progress, ready, delivered, cancelled)
- `started_at`: DateTime(timezone=True), NULLABLE
- `completed_at`: DateTime(timezone=True), NULLABLE
- `assigned_to`: Integer, FK(users.id), NULLABLE
- Relationships: `round_item`, `assignee`

#### 1.7.7 Billing Domain

**Check**
- `id`: Integer, PK
- `session_id`: Integer, FK(table_sessions.id), NOT NULL, UNIQUE
- `subtotal_cents`: Integer, NOT NULL, default=0
- `tax_cents`: Integer, NOT NULL, default=0
- `discount_cents`: Integer, NOT NULL, default=0
- `total_cents`: Integer, NOT NULL, default=0
- `tip_cents`: Integer, NOT NULL, default=0
- `status`: String(20), NOT NULL, default="open" (enum: open, closed, voided)
- `closed_at`: DateTime(timezone=True), NULLABLE
- `closed_by`: Integer, FK(users.id), NULLABLE
- Relationships: `session`, `charges`, `payments`, `closer`

**Charge**
- `id`: Integer, PK
- `check_id`: Integer, FK(checks.id), NOT NULL, INDEX
- `round_item_id`: Integer, FK(round_items.id), NOT NULL, INDEX
- `description`: String(200), NOT NULL
- `amount_cents`: Integer, NOT NULL
- `quantity`: Integer, NOT NULL, default=1
- Relationships: `check`, `round_item`, `allocations`

**Allocation**
- `id`: Integer, PK
- `charge_id`: Integer, FK(charges.id), NOT NULL, INDEX
- `diner_id`: Integer, FK(diners.id), NOT NULL, INDEX
- `amount_cents`: Integer, NOT NULL
- `split_type`: String(20), NOT NULL, default="equal" (enum: equal, custom, full)
- Constraint: UNIQUE(charge_id, diner_id)
- Relationships: `charge`, `diner`

**Payment**
- `id`: Integer, PK
- `check_id`: Integer, FK(checks.id), NOT NULL, INDEX
- `diner_id`: Integer, FK(diners.id), NULLABLE
- `amount_cents`: Integer, NOT NULL
- `method`: String(30), NOT NULL (enum: cash, card, mercadopago, transfer)
- `status`: String(20), NOT NULL, default="pending" (enum: pending, completed, failed, refunded)
- `external_id`: String(200), NULLABLE (payment gateway reference)
- `paid_at`: DateTime(timezone=True), NULLABLE
- Relationships: `check`, `diner`

#### 1.7.8 Services Domain

**ServiceCall**
- `id`: Integer, PK
- `table_id`: Integer, FK(tables.id), NOT NULL, INDEX
- `session_id`: Integer, FK(table_sessions.id), NOT NULL, INDEX
- `type`: String(30), NOT NULL (enum: waiter, water, bill, other)
- `message`: Text, NULLABLE
- `status`: String(20), NOT NULL, default="pending" (enum: pending, acknowledged, resolved, cancelled)
- `called_at`: DateTime(timezone=True), NOT NULL, server_default=func.now()
- `acknowledged_at`: DateTime(timezone=True), NULLABLE
- `resolved_at`: DateTime(timezone=True), NULLABLE
- `resolved_by`: Integer, FK(users.id), NULLABLE
- Relationships: `table`, `session`, `resolver`

**WaiterSectorAssignment**
- `id`: Integer, PK
- `user_id`: Integer, FK(users.id), NOT NULL, INDEX
- `branch_id`: Integer, FK(branches.id), NOT NULL, INDEX
- `sector_id`: Integer, FK(sectors.id), NOT NULL, INDEX
- `assigned_at`: DateTime(timezone=True), NOT NULL, server_default=func.now()
- `unassigned_at`: DateTime(timezone=True), NULLABLE
- Constraint: UNIQUE(user_id, sector_id) WHERE unassigned_at IS NULL
- Relationships: `user`, `branch`, `sector`

#### 1.7.9 Marketing Domain

**Promotion**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(200), NOT NULL
- `description`: Text, NULLABLE
- `discount_type`: String(20), NOT NULL (enum: percentage, fixed_amount, buy_x_get_y)
- `discount_value`: Integer, NOT NULL (percentage as int 0-100, or cents)
- `min_order_cents`: Integer, NULLABLE
- `max_discount_cents`: Integer, NULLABLE
- `start_date`: DateTime(timezone=True), NOT NULL
- `end_date`: DateTime(timezone=True), NULLABLE
- `is_active`: Boolean (inherited)
- Relationships: `tenant`, `promotion_products`

**PromotionProduct**
- `id`: Integer, PK
- `promotion_id`: Integer, FK(promotions.id), NOT NULL, INDEX
- `product_id`: Integer, FK(products.id), NOT NULL, INDEX
- Constraint: UNIQUE(promotion_id, product_id)
- Relationships: `promotion`, `product`

**Badge**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL (e.g., "Nuevo", "Popular", "Chef Recomienda")
- `color`: String(7), NULLABLE (hex color, e.g., "#FF5733")
- `icon`: String(50), NULLABLE
- Constraint: UNIQUE(tenant_id, name)

**Seal**
- `id`: Integer, PK
- `tenant_id`: Integer, FK(tenants.id), NOT NULL, INDEX
- `name`: String(100), NOT NULL (e.g., "Sin TACC", "Vegano", "Orgánico")
- `icon_url`: String(500), NULLABLE
- `description`: Text, NULLABLE
- Constraint: UNIQUE(tenant_id, name)

#### 1.7.10 Recipes Domain

**Recipe**
- `id`: Integer, PK
- `product_id`: Integer, FK(products.id), NOT NULL, UNIQUE
- `yield_quantity`: Numeric(10,3), NOT NULL, default=1
- `yield_unit`: String(50), NOT NULL, default="porción"
- `total_cost_cents`: Integer, NOT NULL, default=0 (calculated)
- `notes`: Text, NULLABLE
- Relationships: `product`, `ingredients`, `steps`

**RecipeIngredient**
- `id`: Integer, PK
- `recipe_id`: Integer, FK(recipes.id), NOT NULL, INDEX
- `ingredient_id`: Integer, FK(ingredients.id), NOT NULL, INDEX
- `quantity`: Numeric(10,3), NOT NULL
- `unit`: String(50), NOT NULL
- `notes`: Text, NULLABLE
- Constraint: UNIQUE(recipe_id, ingredient_id)
- Relationships: `recipe`, `ingredient`

**RecipeStep**
- `id`: Integer, PK
- `recipe_id`: Integer, FK(recipes.id), NOT NULL, INDEX
- `step_number`: Integer, NOT NULL
- `instruction`: Text, NOT NULL
- `duration_minutes`: Integer, NULLABLE
- `image_url`: String(500), NULLABLE
- Constraint: UNIQUE(recipe_id, step_number)
- Relationships: `recipe`

### 1.8 Repositories

- `shared/repositories/base.py` MUST define `BaseRepository[T]` generic class
- `BaseRepository` MUST accept `AsyncSession` in constructor
- `BaseRepository` MUST provide: `get_by_id(id)`, `get_all(skip, limit)`, `create(obj)`, `update(obj)`, `soft_delete(id, user_id)`, `restore(id)`
- `BaseRepository` MUST filter by `is_active=True` by default on all read operations
- `BaseRepository` SHOULD accept `include_deleted=False` parameter to override the filter
- `TenantRepository(BaseRepository)` MUST add `tenant_id` filter to ALL queries
- `TenantRepository` MUST accept `tenant_id` in constructor
- `BranchRepository(TenantRepository)` MUST add `branch_id` filter on top of tenant filter
- `BranchRepository` MUST accept `branch_id` in constructor

### 1.9 Health Checks

- `GET /api/health/live` MUST return `{"status": "alive"}` with HTTP 200
- `GET /api/health/live` MUST NOT check any external dependencies
- `GET /api/health/ready` MUST check PostgreSQL connectivity (execute `SELECT 1`)
- `GET /api/health/ready` MUST check Redis connectivity (execute `PING`)
- `GET /api/health/ready` MUST return `{"status": "ready", "checks": {"postgres": "ok", "redis": "ok"}}` with HTTP 200 when all pass
- `GET /api/health/ready` MUST return `{"status": "not_ready", "checks": {"postgres": "ok"|"error", "redis": "ok"|"error"}}` with HTTP 503 when any check fails
- Health check endpoints MUST NOT require authentication

### 1.10 Seed Data

- Seed script MUST be idempotent (safe to run multiple times)
- Seed script MUST create 1 tenant: "Buen Sabor" (slug: "buen-sabor")
- Seed script MUST create 1 branch: "Sede Central" (slug: "sede-central")
- Seed script MUST create 3 sectors: "Salón Principal", "Terraza", "Barra"
- Seed script MUST create tables: Salón(1-10), Terraza(T1-T6), Barra(B1-B4) — 20 tables total
- Seed script MUST create test users:
  - admin@buensabor.com (role: owner, is_superadmin: true)
  - manager@buensabor.com (role: manager)
  - chef@buensabor.com (role: chef)
  - waiter1@buensabor.com (role: waiter)
  - waiter2@buensabor.com (role: waiter)
  - cashier@buensabor.com (role: cashier)
- Seed script MUST create categories: "Entradas", "Platos Principales", "Postres", "Bebidas", "Guarniciones"
- Seed script MUST create subcategories (at least 2 per category)
- Seed script MUST create sample products (at least 3 per subcategory)
- Seed script MUST create the 14 EU allergens: Gluten, Crustaceans, Eggs, Fish, Peanuts, Soybeans, Milk, Tree Nuts, Celery, Mustard, Sesame, Sulphites, Lupin, Molluscs
- Seed script MUST create sample cooking methods: "A la parrilla", "Frito", "Al horno", "Hervido", "Salteado", "Crudo"
- Seed script MUST create sample flavor profiles: "Dulce", "Salado", "Ácido", "Amargo", "Umami", "Picante"
- Seed script MUST create sample texture profiles: "Crocante", "Cremoso", "Suave", "Firme", "Esponjoso"
- Seed script MUST create sample cuisine types: "Argentina", "Italiana", "Japonesa", "Mexicana", "Francesa"
- Passwords for test users MUST be hashed (using passlib bcrypt or similar)
- Default password for all test users SHALL be "TestPassword123!" (documented in README)

### 1.11 Alembic Migrations

- Alembic MUST be configured for async with asyncpg
- `alembic.ini` MUST reference `shared/models/` for autogenerate
- Initial migration MUST create ALL tables defined above
- Migration MUST enable `pgvector` extension: `CREATE EXTENSION IF NOT EXISTS vector`
- `alembic/env.py` MUST import ALL models so autogenerate detects them
- Migrations MUST be reversible (downgrade drops tables in correct FK order)

### 1.12 CI / Code Quality

- `.pre-commit-config.yaml` MUST configure: ruff (format + check), mypy
- `ruff` MUST use config in `pyproject.toml` with rules: E, F, W, I (isort), UP, B, SIM, N
- `ruff` line-length MUST be 120
- `mypy` MUST be configured with `strict = false`, `warn_return_any = true`, `warn_unused_configs = true`
- `mypy` MUST have SQLAlchemy plugin enabled: `plugins = ["sqlalchemy.ext.mypy.plugin"]`

## 2. Scenarios (Given/When/Then)

### Scenario 1: Fresh environment startup
```
GIVEN a clean machine with Docker installed
WHEN the developer runs `docker compose up -d`
THEN all 4 services start without errors
AND postgres passes health check within 30 seconds
AND redis passes health check within 10 seconds
AND api starts and binds to port 8000
AND gateway starts and binds to port 8001
```

### Scenario 2: Health check — live
```
GIVEN the API service is running
WHEN a GET request is made to /api/health/live
THEN the response status is 200
AND the response body is {"status": "alive"}
```

### Scenario 3: Health check — ready (all healthy)
```
GIVEN the API service is running
AND PostgreSQL is accepting connections
AND Redis is accepting connections
WHEN a GET request is made to /api/health/ready
THEN the response status is 200
AND the response body contains {"status": "ready", "checks": {"postgres": "ok", "redis": "ok"}}
```

### Scenario 4: Health check — ready (DB down)
```
GIVEN the API service is running
AND PostgreSQL is NOT accepting connections
AND Redis is accepting connections
WHEN a GET request is made to /api/health/ready
THEN the response status is 503
AND the response body contains {"status": "not_ready", "checks": {"postgres": "error", "redis": "ok"}}
```

### Scenario 5: Seed data idempotency
```
GIVEN the database has been migrated (tables exist)
WHEN the seed script is executed for the first time
THEN all seed data is created
AND running the seed script again does NOT create duplicates
AND running the seed script again does NOT raise errors
```

### Scenario 6: Tenant isolation in repository
```
GIVEN two tenants exist: "Buen Sabor" (id=1) and "Other" (id=2)
AND tenant 1 has 5 products
AND tenant 2 has 3 products
WHEN TenantRepository is instantiated with tenant_id=1
AND get_all() is called
THEN only 5 products from tenant 1 are returned
AND no products from tenant 2 are returned
```

### Scenario 7: Soft delete behavior
```
GIVEN a product exists with id=1 and is_active=True
WHEN soft_delete(id=1, user_id=5) is called
THEN the product's is_active becomes False
AND the product's deleted_at is set to the current timestamp
AND the product's deleted_by is set to 5
AND the product is NOT returned by default get_all()
AND the product IS returned by get_all(include_deleted=True)
```

### Scenario 8: Alembic migration up/down
```
GIVEN a clean database with no tables
WHEN `alembic upgrade head` is executed
THEN all tables are created
AND the pgvector extension is enabled
WHEN `alembic downgrade base` is executed
THEN all tables are dropped
AND the database is clean
```

### Scenario 9: Safe commit with IntegrityError
```
GIVEN a user with email "admin@buensabor.com" exists
WHEN a new user with email "admin@buensabor.com" is created
AND safe_commit() is called
THEN an IntegrityError is caught
AND the session is rolled back
AND a domain-specific DuplicateError is raised
```

## 3. Edge Cases

- **Circular FK on AuditMixin**: `created_by` FK references `users.id`, but users table also uses AuditMixin. Solution: make `created_by`, `updated_by`, `deleted_by` NULLABLE and do NOT add FK constraint on these columns in AuditMixin. Instead, these are plain Integer columns — FK enforcement only at application level.
- **Table auto-naming collision**: If two models produce the same snake_case plural, one MUST override `__tablename__` explicitly.
- **pgvector extension**: Must be created BEFORE any tables that use vector columns. In initial migration, `CREATE EXTENSION` is the first operation.
- **Async session in seed script**: Seed script must use `async with async_session_factory() as session` — cannot use `get_db()` FastAPI dependency outside of request context.
- **Alembic with async**: `env.py` must use `run_async()` wrapper and `connectable = create_async_engine(...)`.
- **Redis connection failure on startup**: API MUST start even if Redis is temporarily unavailable. Health check reports it, but the app doesn't crash.
- **Empty tenant_id**: TenantRepository MUST raise ValueError if instantiated with tenant_id=None.
