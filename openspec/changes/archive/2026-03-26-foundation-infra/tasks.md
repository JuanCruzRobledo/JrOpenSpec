---
change: foundation-infra
phase: 1
artifact: tasks
source: sdd-otro/sprint-1-infra
date: 2026-03-23
status: done
completed_at: 2026-03-26
---

# SDD Tasks: Sprint 1 — Infraestructura y Modelo de Datos

> **ALL 30 TASKS COMPLETED** (2026-03-26) — Implemented by 3 parallel agents across 79 files.

## Phase 1: Project Scaffolding

### 1.1 Create Monorepo Directory Structure
**Files to create**:
- `rest_api/` directory
- `ws_gateway/` directory
- `shared/` directory (Python package)
- `pwa_menu/` directory
- `pwa_waiter/` directory
- `dashboard/` directory
- `.gitignore`
- `.env.example`
- Root `pyproject.toml` (workspace config)

**Acceptance Criteria**:
- All 6 directories exist
- `.gitignore` covers Python, Node, Docker, .env, __pycache__, .mypy_cache, .ruff_cache
- `.env.example` has all required env vars with placeholder values

### 1.2 Configure shared/ as Python Package
**Files to create**:
- `shared/pyproject.toml`
- `shared/shared/__init__.py`
- `shared/shared/config.py` (Pydantic Settings)
- `shared/shared/exceptions.py` (DuplicateError, NotFoundError, etc.)
- `shared/shared/infrastructure/__init__.py`
- `shared/shared/infrastructure/db.py`
- `shared/shared/infrastructure/redis.py`

**Acceptance Criteria**:
- `shared/pyproject.toml` has correct metadata, dependencies: sqlalchemy[asyncio]>=2.0, asyncpg, pydantic>=2.0, pydantic-settings, redis[hiredis]
- `pip install -e shared/` succeeds
- `from shared.config import settings` works
- `from shared.infrastructure.db import engine, async_session_factory, get_db, safe_commit` works
- `config.py` loads from env vars with .env file fallback
- `db.py` creates AsyncEngine with pool settings: pool_size=20, max_overflow=10, pool_timeout=30, pool_recycle=1800
- `db.py` exports `get_db` async generator for FastAPI Depends
- `db.py` exports `safe_commit` that catches IntegrityError → DuplicateError, SQLAlchemyError → generic error, with rollback
- `redis.py` exports `get_redis` async factory function
- `exceptions.py` defines: `AppException(Exception)`, `DuplicateError(AppException)`, `NotFoundError(AppException)`, `ValidationError(AppException)`

### 1.3 Setup rest_api/ FastAPI Application
**Files to create**:
- `rest_api/pyproject.toml`
- `rest_api/Dockerfile`
- `rest_api/app/__init__.py`
- `rest_api/app/main.py` (app factory + lifespan)
- `rest_api/app/dependencies.py`
- `rest_api/app/routers/__init__.py`

**Acceptance Criteria**:
- `pyproject.toml` depends on: fastapi>=0.115, uvicorn[standard], shared (editable)
- `main.py` uses `create_app()` factory pattern
- `main.py` uses `@asynccontextmanager` lifespan for startup/shutdown
- Lifespan startup: log startup, verify DB connection
- Lifespan shutdown: dispose engine
- Dockerfile is multi-stage (builder + runtime)
- `dependencies.py` re-exports `get_db` from shared for convenience

### 1.4 Setup ws_gateway/ Stub
**Files to create**:
- `ws_gateway/pyproject.toml`
- `ws_gateway/Dockerfile`
- `ws_gateway/main.py` (minimal FastAPI stub with single health endpoint)

**Acceptance Criteria**:
- `main.py` creates a FastAPI app that returns {"status": "gateway stub"} on GET /
- Dockerfile builds and runs successfully
- No business logic — pure stub

### 1.5 Setup Frontend Stubs
**Files to create**:
- `pwa_menu/package.json`
- `pwa_waiter/package.json`
- `dashboard/package.json`

**Acceptance Criteria**:
- Each `package.json` has name, version, and description only
- No dependencies — pure placeholder

### 1.6 Docker Compose Configuration
**Files to create**:
- `docker-compose.yml`

**Acceptance Criteria**:
- Defines 4 services: postgres, redis, api, gateway
- `postgres` uses `pgvector/pgvector:0.8.0-pg16`
- `postgres` has health check: `pg_isready -U $$POSTGRES_USER` interval=5s timeout=5s retries=5
- `postgres` has named volume `pgdata`
- `redis` uses `redis:7-alpine`
- `redis` has health check: `redis-cli ping` interval=5s timeout=5s retries=5
- `redis` has named volume `redisdata`
- `api` builds from `rest_api/`, port 8000
- `api` depends on postgres (service_healthy) and redis (service_healthy)
- `api` mounts shared/ for dev hot-reload
- `api` passes all env vars from .env
- `gateway` builds from `ws_gateway/`, port 8001
- All services on network `buen-sabor-net`
- `docker compose config` validates without errors
- `docker compose up` starts all services (after Phase 2 models exist)

---

## Phase 2: Models and Mixins

### 2.1 Create Base Model Infrastructure
**Files to create**:
- `shared/shared/models/__init__.py`
- `shared/shared/models/base.py`
- `shared/shared/models/mixins.py`

**Acceptance Criteria**:
- `base.py` defines `Base = declarative_base()` (or DeclarativeBase for SQLAlchemy 2.0+ style)
- `base.py` defines `BaseModel(AuditMixin, Base)` with `__abstract__ = True`
- `BaseModel` has `id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)`
- `BaseModel` has `@declared_attr.directive` that auto-generates `__tablename__` from CamelCase to snake_case plural
- `mixins.py` defines `AuditMixin` with ALL 7 fields: created_at, updated_at, deleted_at, created_by, updated_by, deleted_by, is_active
- `created_at` and `updated_at` have `server_default=func.now()`
- `updated_at` has `onupdate=func.now()`
- `created_by`, `updated_by`, `deleted_by` are plain `Integer`, NULLABLE, NO foreign key
- `is_active` defaults to `True`
- `AuditMixin.soft_delete(user_id=None)` sets deleted_at, deleted_by, is_active=False
- `AuditMixin.restore()` clears deleted_at, deleted_by, sets is_active=True
- Table name generation tested: `UserBranchRole` → `user_branch_roles`, `Category` → `categories`, `Branch` → `branches`

### 2.2 Create Core Domain Models
**Files to create**:
- `shared/shared/models/core/__init__.py`
- `shared/shared/models/core/tenant.py`
- `shared/shared/models/core/branch.py`
- `shared/shared/models/core/user.py`
- `shared/shared/models/core/user_branch_role.py`

**Acceptance Criteria**:
- Each model inherits from `BaseModel`
- All columns match spec exactly (types, constraints, nullability)
- All relationships use `relationship()` with explicit `back_populates`
- All UNIQUE constraints are defined
- Tenant: name UNIQUE, slug UNIQUE+INDEX
- Branch: UNIQUE(tenant_id, slug)
- User: email UNIQUE
- UserBranchRole: UNIQUE(user_id, branch_id, role)
- All `Mapped[]` type annotations used (no legacy Column style)
- All foreign keys properly reference parent table

### 2.3 Create Catalog Domain Models
**Files to create**:
- `shared/shared/models/catalog/__init__.py`
- `shared/shared/models/catalog/category.py`
- `shared/shared/models/catalog/subcategory.py`
- `shared/shared/models/catalog/product.py`
- `shared/shared/models/catalog/branch_product.py`
- `shared/shared/models/catalog/allergen.py`
- `shared/shared/models/catalog/product_allergen.py`

**Acceptance Criteria**:
- All columns match spec
- Product has FKs to profiles (cooking_method_id, flavor_profile_id, texture_profile_id, cuisine_type_id) — all NULLABLE
- Product.base_price_cents has CHECK constraint >= 0
- BranchProduct.price_override_cents has CHECK >= 0 OR NULL
- Allergen is NOT tenant-scoped (no tenant_id)
- ProductAllergen.severity defaults to "contains"
- UNIQUE constraints: Category(tenant_id, slug), Subcategory(category_id, slug), Product(tenant_id, slug), BranchProduct(branch_id, product_id), Allergen(name), Allergen(code), ProductAllergen(product_id, allergen_id)

### 2.4 Create Profiles Domain Models
**Files to create**:
- `shared/shared/models/profiles/__init__.py`
- `shared/shared/models/profiles/cooking_method.py`
- `shared/shared/models/profiles/flavor_profile.py`
- `shared/shared/models/profiles/texture_profile.py`
- `shared/shared/models/profiles/cuisine_type.py`

**Acceptance Criteria**:
- All 4 models have: id, tenant_id, name
- All have UNIQUE(tenant_id, name)
- All inherit from BaseModel

### 2.5 Create Ingredients Domain Models
**Files to create**:
- `shared/shared/models/ingredients/__init__.py`
- `shared/shared/models/ingredients/ingredient_group.py`
- `shared/shared/models/ingredients/ingredient.py`
- `shared/shared/models/ingredients/sub_ingredient.py`

**Acceptance Criteria**:
- IngredientGroup: UNIQUE(tenant_id, name)
- Ingredient: UNIQUE(tenant_id, name), cost_per_unit_cents CHECK >= 0, stock_quantity is Numeric(10,3)
- SubIngredient: UNIQUE(parent_ingredient_id, child_ingredient_id), self-referential through ingredients table
- SubIngredient has relationships to both parent and child ingredient

### 2.6 Create Room Domain Models
**Files to create**:
- `shared/shared/models/room/__init__.py`
- `shared/shared/models/room/sector.py`
- `shared/shared/models/room/table.py`
- `shared/shared/models/room/table_session.py`
- `shared/shared/models/room/diner.py`

**Acceptance Criteria**:
- Sector: UNIQUE(branch_id, name)
- Table: UNIQUE(sector_id, number), status default "available", pos_x/pos_y nullable Float
- TableSession: opened_at server_default, status default "active", has FK to opener/closer users
- Diner: UNIQUE(session_id, seat_number) with partial index (WHERE seat_number IS NOT NULL)
- Table.status validated against enum: available, occupied, reserved, blocked

### 2.7 Create Orders Domain Models
**Files to create**:
- `shared/shared/models/orders/__init__.py`
- `shared/shared/models/orders/round.py`
- `shared/shared/models/orders/round_item.py`
- `shared/shared/models/orders/kitchen_ticket.py`

**Acceptance Criteria**:
- Round: UNIQUE(session_id, round_number), status default "draft"
- RoundItem: quantity CHECK > 0, unit_price_cents CHECK >= 0, status default "pending"
- KitchenTicket: station NOT NULL, priority default 0, status default "pending"
- All status fields match enum values from spec

### 2.8 Create Billing Domain Models
**Files to create**:
- `shared/shared/models/billing/__init__.py`
- `shared/shared/models/billing/check.py`
- `shared/shared/models/billing/charge.py`
- `shared/shared/models/billing/allocation.py`
- `shared/shared/models/billing/payment.py`

**Acceptance Criteria**:
- Check: UNIQUE on session_id (one check per session), all cents fields default 0, CHECK >= 0
- Charge: amount_cents CHECK >= 0
- Allocation: UNIQUE(charge_id, diner_id), split_type default "equal"
- Payment: amount_cents CHECK > 0, method enum validated, external_id nullable

### 2.9 Create Services Domain Models
**Files to create**:
- `shared/shared/models/services/__init__.py`
- `shared/shared/models/services/service_call.py`
- `shared/shared/models/services/waiter_sector_assignment.py`

**Acceptance Criteria**:
- ServiceCall: type enum (waiter, water, bill, other), status default "pending", called_at server_default
- WaiterSectorAssignment: partial unique on (user_id, sector_id) WHERE unassigned_at IS NULL
- All FK relationships defined

### 2.10 Create Marketing Domain Models
**Files to create**:
- `shared/shared/models/marketing/__init__.py`
- `shared/shared/models/marketing/promotion.py`
- `shared/shared/models/marketing/promotion_product.py`
- `shared/shared/models/marketing/badge.py`
- `shared/shared/models/marketing/seal.py`

**Acceptance Criteria**:
- Promotion: discount_type enum, discount_value CHECK > 0, dates validated
- PromotionProduct: UNIQUE(promotion_id, product_id)
- Badge: UNIQUE(tenant_id, name), color is String(7) for hex
- Seal: UNIQUE(tenant_id, name)

### 2.11 Create Recipes Domain Models
**Files to create**:
- `shared/shared/models/recipes/__init__.py`
- `shared/shared/models/recipes/recipe.py`
- `shared/shared/models/recipes/recipe_ingredient.py`
- `shared/shared/models/recipes/recipe_step.py`

**Acceptance Criteria**:
- Recipe: UNIQUE on product_id (one recipe per product), yield_quantity Numeric(10,3)
- RecipeIngredient: UNIQUE(recipe_id, ingredient_id), quantity Numeric(10,3)
- RecipeStep: UNIQUE(recipe_id, step_number), instruction NOT NULL
- All relationships defined with back_populates

### 2.12 Register All Models in __init__.py
**Files to modify**:
- `shared/shared/models/__init__.py`

**Acceptance Criteria**:
- Imports ALL models from ALL 10 domains
- This is CRITICAL for Alembic autogenerate to detect all tables
- Pattern: `from shared.models.core.tenant import Tenant` for every model
- Export `__all__` list with all model names
- Import `Base` from `base.py` and export it

---

## Phase 3: Alembic Migrations

### 3.1 Configure Alembic for Async
**Files to create**:
- `alembic.ini`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/versions/` (empty directory)

**Acceptance Criteria**:
- `alembic.ini` points `sqlalchemy.url` to env var or placeholder
- `env.py` uses `run_async()` pattern with `create_async_engine`
- `env.py` imports `Base` from `shared.models` (triggering all model imports)
- `env.py` imports `target_metadata = Base.metadata`
- `env.py` properly handles async migration context
- `alembic revision --autogenerate` successfully detects all tables

### 3.2 Generate and Validate Initial Migration
**Files to create**:
- `alembic/versions/001_initial.py` (auto-generated + manual edits)

**Acceptance Criteria**:
- Migration begins with `CREATE EXTENSION IF NOT EXISTS vector` (pgvector)
- Migration creates ALL tables (52+) in correct FK dependency order
- ALL UNIQUE constraints are present
- ALL CHECK constraints are present
- ALL indexes are present
- `upgrade()` creates all tables from clean DB
- `downgrade()` drops all tables in reverse FK order
- Migration is reversible: `alembic upgrade head` then `alembic downgrade base` succeeds without errors

---

## Phase 4: Repositories

### 4.1 Create Base Repository
**Files to create**:
- `shared/shared/repositories/__init__.py`
- `shared/shared/repositories/base.py`

**Acceptance Criteria**:
- `BaseRepository[T]` is generic, parameterized by model type
- Constructor accepts `AsyncSession` and sets `self.session`
- `model` class attribute set via `__init_subclass__` or generic inference
- `get_by_id(id, include_deleted=False)` returns `T | None`
- `get_all(skip=0, limit=100, include_deleted=False)` returns `list[T]`
- Default queries filter `WHERE is_active = True`
- `include_deleted=True` removes the is_active filter
- `create(entity: T)` adds to session, calls safe_commit, refreshes, returns entity
- `update(entity: T)` calls safe_commit, refreshes, returns entity
- `soft_delete(id, user_id=None)` calls entity.soft_delete(user_id), commits
- `restore(id)` calls entity.restore(), commits
- Type hints are correct for all methods

### 4.2 Create Tenant and Branch Repositories
**Files to create**:
- `shared/shared/repositories/tenant.py`
- `shared/shared/repositories/branch.py`

**Acceptance Criteria**:
- `TenantRepository[T](BaseRepository[T])`:
  - Constructor accepts `session` + `tenant_id: int`
  - Raises `ValueError` if `tenant_id` is None
  - Overrides `_base_query()` to add `WHERE tenant_id = self.tenant_id`
  - ALL query methods automatically filter by tenant
- `BranchRepository[T](TenantRepository[T])`:
  - Constructor accepts `session` + `tenant_id` + `branch_id: int`
  - Raises `ValueError` if `branch_id` is None
  - Adds `WHERE branch_id = self.branch_id` on top of tenant filter
- Both properly inherit and extend parent query building

---

## Phase 5: Health Checks

### 5.1 Implement Health Check Endpoints
**Files to create**:
- `rest_api/app/routers/health.py`

**Acceptance Criteria**:
- Router with prefix="" and tag="health"
- `GET /live`: Returns `{"status": "alive"}`, HTTP 200, no external calls
- `GET /ready`:
  - Checks PostgreSQL: executes `SELECT 1` via async session
  - Checks Redis: executes `PING` via redis client
  - If both pass: `{"status": "ready", "checks": {"postgres": "ok", "redis": "ok"}}`, HTTP 200
  - If any fails: `{"status": "not_ready", "checks": {...}}`, HTTP 503
  - Each check wrapped in try/except — one failing doesn't prevent checking the other
- No authentication required on either endpoint
- Router registered in `main.py` with prefix `/api/health`

---

## Phase 6: Seed Data

### 6.1 Create Seed Script
**Files to create**:
- `rest_api/scripts/seed.py`

**Acceptance Criteria**:
- Script is importable as `from rest_api.scripts.seed import run_seed`
- Also executable standalone: `python -m rest_api.scripts.seed`
- Uses `async with async_session_factory() as session` (NOT get_db)
- IDEMPOTENT: checks existence before creating each entity group
- Idempotency strategy: query by unique field (slug/email/name), skip if exists
- Creates entities in correct FK order:
  1. Tenant "Buen Sabor" (slug: "buen-sabor")
  2. Branch "Sede Central" (slug: "sede-central")
  3. Sectors: "Salón Principal", "Terraza", "Barra"
  4. Tables: Salón 1-10, Terraza T1-T6, Barra B1-B4 (20 total)
  5. Users (6): admin, manager, chef, waiter1, waiter2, cashier
  6. UserBranchRoles for each user
  7. Allergens (14 EU): gluten, crustaceans, eggs, fish, peanuts, soybeans, milk, tree_nuts, celery, mustard, sesame, sulphites, lupin, molluscs
  8. Cooking methods (6): "A la parrilla", "Frito", "Al horno", "Hervido", "Salteado", "Crudo"
  9. Flavor profiles (6): "Dulce", "Salado", "Ácido", "Amargo", "Umami", "Picante"
  10. Texture profiles (5): "Crocante", "Cremoso", "Suave", "Firme", "Esponjoso"
  11. Cuisine types (5): "Argentina", "Italiana", "Japonesa", "Mexicana", "Francesa"
  12. Categories (5): "Entradas", "Platos Principales", "Postres", "Bebidas", "Guarniciones"
  13. Subcategories (2+ per category, 10+ total)
  14. Products (3+ per subcategory, 30+ total with realistic names/prices)
- User passwords hashed with passlib bcrypt
- Default password: "TestPassword123!"
- All prices in cents (e.g., empanada = 850 = $8.50)
- Products assigned to branch via BranchProduct
- Some products assigned allergens via ProductAllergen
- Some products assigned profiles (cooking method, flavor, etc.)
- Commit at the end (single transaction)
- Logs progress: "Seeding tenants... done", "Seeding users... done", etc.

### 6.2 Integrate Seed into API Lifespan
**Files to modify**:
- `rest_api/app/main.py`

**Acceptance Criteria**:
- Lifespan startup calls `run_seed()` after migrations
- Seed only runs if `ENVIRONMENT == "development"` (configurable)
- Seed failure logs error but does NOT crash the API
- Seed wrapped in try/except with logging

---

## Phase 7: CI and Code Quality

### 7.1 Configure Pre-commit and Linting
**Files to create**:
- `.pre-commit-config.yaml`
- Root `pyproject.toml` — ruff and mypy config sections

**Acceptance Criteria**:
- `.pre-commit-config.yaml` hooks:
  - `ruff` (format): auto-formats on commit
  - `ruff` (check): lint check with --fix
  - `mypy`: type check
- `pyproject.toml` [tool.ruff]:
  - `line-length = 120`
  - `select = ["E", "F", "W", "I", "UP", "B", "SIM", "N"]`
  - `target-version = "py312"`
- `pyproject.toml` [tool.mypy]:
  - `strict = false`
  - `warn_return_any = true`
  - `warn_unused_configs = true`
  - `plugins = ["sqlalchemy.ext.mypy.plugin"]`
- `pre-commit install` works
- `ruff check shared/ rest_api/` passes
- `mypy shared/ rest_api/` passes (or only known issues)

### 7.2 Create .env.example and Documentation Stubs
**Files to create/modify**:
- `.env.example` (if not already created in 1.1)

**Acceptance Criteria**:
- `.env.example` contains ALL env vars with placeholder values:
  ```
  POSTGRES_USER=buensabor
  POSTGRES_PASSWORD=changeme
  POSTGRES_DB=buensabor
  DATABASE_URL=postgresql+asyncpg://buensabor:changeme@postgres:5432/buensabor
  REDIS_URL=redis://redis:6379/0
  ENVIRONMENT=development
  DEBUG=true
  LOG_LEVEL=DEBUG
  API_PREFIX=/api
  ```
- NO real credentials in .env.example

---

## Task Dependency Graph

```
Phase 1 (Scaffolding):
  1.1 → 1.2 → 1.3 → 1.6
  1.1 → 1.4
  1.1 → 1.5

Phase 2 (Models): depends on 1.2
  2.1 → 2.2 through 2.11 (parallel, all depend on 2.1)
  2.12 depends on ALL of 2.2-2.11

Phase 3 (Alembic): depends on 2.12
  3.1 → 3.2

Phase 4 (Repositories): depends on 2.1
  4.1 → 4.2

Phase 5 (Health): depends on 1.3
  5.1

Phase 6 (Seed): depends on 2.12, 3.2
  6.1 → 6.2

Phase 7 (CI): can run in parallel with Phase 2+
  7.1 (after 1.1)
  7.2 (after 1.1)
```

## Execution Order (Recommended)

Session 1: Tasks 1.1, 1.2, 1.4, 1.5
Session 2: Tasks 1.3, 1.6
Session 3: Tasks 2.1, 2.2, 2.3, 2.4
Session 4: Tasks 2.5, 2.6, 2.7
Session 5: Tasks 2.8, 2.9, 2.10, 2.11, 2.12
Session 6: Tasks 3.1, 3.2
Session 7: Tasks 4.1, 4.2
Session 8: Task 5.1
Session 9: Tasks 6.1, 6.2
Session 10: Tasks 7.1, 7.2

## Total: 52+ files to create, ~10 sessions estimated
