---
change: foundation-infra
phase: 1
artifact: design
source: sdd-otro/sprint-1-infra
date: 2026-03-23
status: approved
---

# SDD Design: Sprint 1 — Infraestructura y Modelo de Datos

## 1. Architecture Decisions

### ADR-001: Row-Level Multi-Tenancy (not Schema-per-Tenant)
**Decision**: Use `tenant_id` column on all tenant-scoped tables with query-level filtering.
**Rationale**: Schema-per-tenant requires dynamic schema creation, complicates migrations (N schemas × M migrations), and makes shared queries (cross-tenant analytics) nearly impossible. Row-level is simpler, Alembic-friendly, and sufficient for the expected scale (< 100 tenants initially).
**Trade-off**: Must be disciplined about ALWAYS filtering by tenant_id. A missed filter leaks data across tenants. Mitigated by TenantRepository base class.

### ADR-002: Prices as Integer Cents (not Decimal/Float)
**Decision**: All monetary values stored as integer cents (e.g., $15.50 = 1550).
**Rationale**: Floating point arithmetic causes rounding errors in financial calculations. Decimal is correct but adds complexity in serialization. Integer cents is the industry standard (Stripe, MercadoPago all use cents). Frontend formats for display.
**Trade-off**: Must remember to divide by 100 for display. Convention must be documented and enforced.

### ADR-003: Soft Delete on All Models (via AuditMixin)
**Decision**: No physical deletes. All models use `is_active` flag + `deleted_at` timestamp.
**Rationale**: Restaurant data has legal retention requirements (invoices, payments). Soft delete provides audit trail, easy undo, and prevents cascade issues. Periodic hard-delete job can purge old data later.
**Trade-off**: Queries must filter `is_active=True`. Indexes must include `is_active` for performance. BaseRepository handles this automatically.

### ADR-004: AuditMixin without FK on created_by/updated_by/deleted_by
**Decision**: `created_by`, `updated_by`, `deleted_by` are plain Integer columns WITHOUT foreign key constraints to `users.id`.
**Rationale**: The `users` table itself uses AuditMixin, creating a circular dependency. Additionally, system-generated records (seeds, migrations) have no associated user. Application-level validation is sufficient.
**Trade-off**: No referential integrity on audit columns at DB level. Acceptable because these are audit/logging fields, not business logic fields.

### ADR-005: AsyncPG + SQLAlchemy 2.0 Async
**Decision**: Use `asyncpg` driver with SQLAlchemy 2.0 async API exclusively.
**Rationale**: FastAPI is async-native. Mixing sync/async drivers causes event loop issues. SQLAlchemy 2.0's `Mapped[]` annotations provide excellent type safety. asyncpg is the fastest PostgreSQL driver for Python async.
**Trade-off**: Alembic needs async wrapper in env.py. Some SQLAlchemy patterns (eager loading) behave differently in async mode. Must use `selectinload` instead of `joinedload` for collections.

### ADR-006: Single Alembic Initial Migration
**Decision**: One migration creates all 52+ tables instead of incremental per-domain migrations.
**Rationale**: All tables are needed together (FK dependencies span domains). Sprint 1 is the starting point — there's no "existing state" to migrate from. Incremental migrations start from Sprint 2 onward.
**Trade-off**: Large initial migration file. But it's auto-generated and only runs once.

### ADR-007: Declarative Table Naming Convention
**Decision**: Auto-generate `__tablename__` from class name using CamelCase-to-snake_case-plural convention.
**Rationale**: Consistent naming without manual `__tablename__` on every model. Reduces human error.
**Implementation**: `@declared_attr` on BaseModel that converts `UserBranchRole` → `user_branch_roles`.
**Trade-off**: Some names may need override (e.g., `TableSession` → `table_sessions` works fine, but hypothetical edge cases like `Status` → `statuss` would need manual fix).

## 2. Module Structure

```
restaurantes-multi-sucursal/
├── docker-compose.yml
├── .env                          # Local dev env vars (gitignored)
├── .env.example                  # Template for env vars
├── .pre-commit-config.yaml
├── .gitignore
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial.py
├── shared/
│   ├── pyproject.toml
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic Settings
│   │   ├── exceptions.py         # Domain exceptions
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── db.py             # Engine, session, get_db, safe_commit
│   │   │   └── redis.py          # Redis client factory
│   │   ├── models/
│   │   │   ├── __init__.py       # Import ALL models (for Alembic)
│   │   │   ├── base.py           # Base, BaseModel
│   │   │   ├── mixins.py         # AuditMixin
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── tenant.py
│   │   │   │   ├── branch.py
│   │   │   │   ├── user.py
│   │   │   │   └── user_branch_role.py
│   │   │   ├── catalog/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── category.py
│   │   │   │   ├── subcategory.py
│   │   │   │   ├── product.py
│   │   │   │   ├── branch_product.py
│   │   │   │   ├── allergen.py
│   │   │   │   └── product_allergen.py
│   │   │   ├── profiles/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cooking_method.py
│   │   │   │   ├── flavor_profile.py
│   │   │   │   ├── texture_profile.py
│   │   │   │   └── cuisine_type.py
│   │   │   ├── ingredients/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ingredient_group.py
│   │   │   │   ├── ingredient.py
│   │   │   │   └── sub_ingredient.py
│   │   │   ├── room/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sector.py
│   │   │   │   ├── table.py
│   │   │   │   ├── table_session.py
│   │   │   │   └── diner.py
│   │   │   ├── orders/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── round.py
│   │   │   │   ├── round_item.py
│   │   │   │   └── kitchen_ticket.py
│   │   │   ├── billing/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── check.py
│   │   │   │   ├── charge.py
│   │   │   │   ├── allocation.py
│   │   │   │   └── payment.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── service_call.py
│   │   │   │   └── waiter_sector_assignment.py
│   │   │   ├── marketing/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── promotion.py
│   │   │   │   ├── promotion_product.py
│   │   │   │   ├── badge.py
│   │   │   │   └── seal.py
│   │   │   └── recipes/
│   │   │       ├── __init__.py
│   │   │       ├── recipe.py
│   │   │       ├── recipe_ingredient.py
│   │   │       └── recipe_step.py
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── base.py           # BaseRepository[T]
│   │       ├── tenant.py         # TenantRepository
│   │       └── branch.py         # BranchRepository
├── rest_api/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app factory
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── health.py         # Health check endpoints
│   │   └── dependencies.py       # FastAPI dependencies
│   └── scripts/
│       └── seed.py               # Seed data script
├── ws_gateway/
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── main.py                   # Stub
├── pwa_menu/
│   └── package.json              # Stub
├── pwa_waiter/
│   └── package.json              # Stub
└── dashboard/
    └── package.json              # Stub
```

## 3. Database Schema — Physical Design

### 3.1 Index Strategy

Every table gets these indexes automatically from SQLAlchemy:
- PK index on `id`
- FK indexes (SQLAlchemy auto-creates for ForeignKey columns)

Additional explicit indexes:

| Table | Index | Columns | Type | Rationale |
|-------|-------|---------|------|-----------|
| tenants | ix_tenants_slug | slug | UNIQUE | Lookup by slug |
| branches | ix_branches_tenant_slug | tenant_id, slug | UNIQUE | Lookup within tenant |
| users | ix_users_email | email | UNIQUE | Login lookup |
| users | ix_users_tenant | tenant_id | BTREE | Tenant filtering |
| products | ix_products_tenant_slug | tenant_id, slug | UNIQUE | Product lookup |
| products | ix_products_subcategory | subcategory_id | BTREE | Category browsing |
| branch_products | ix_bp_branch_product | branch_id, product_id | UNIQUE | Branch product lookup |
| tables | ix_tables_sector_number | sector_id, number | UNIQUE | Table lookup |
| table_sessions | ix_sessions_table_status | table_id, status | BTREE | Active session lookup |
| rounds | ix_rounds_session_number | session_id, round_number | UNIQUE | Round ordering |
| round_items | ix_round_items_status | status | BTREE | Kitchen display filtering |
| kitchen_tickets | ix_tickets_station_status | station, status | BTREE | Station queue |
| checks | ix_checks_session | session_id | UNIQUE | One check per session |
| service_calls | ix_calls_table_status | table_id, status | BTREE | Active calls lookup |

### 3.2 Constraint Summary

All UNIQUE constraints listed per model in the spec. Additional CHECK constraints:

| Table | Constraint | Expression |
|-------|-----------|------------|
| products | ck_price_positive | `base_price_cents >= 0` |
| branch_products | ck_override_positive | `price_override_cents >= 0 OR price_override_cents IS NULL` |
| round_items | ck_quantity_positive | `quantity > 0` |
| round_items | ck_unit_price_positive | `unit_price_cents >= 0` |
| charges | ck_charge_positive | `amount_cents >= 0` |
| payments | ck_payment_positive | `amount_cents > 0` |
| checks | ck_subtotal_positive | `subtotal_cents >= 0` |
| ingredients | ck_cost_positive | `cost_per_unit_cents >= 0` |
| promotions | ck_discount_positive | `discount_value > 0` |

### 3.3 Enum Values (stored as String, validated at application level)

| Field | Allowed Values |
|-------|---------------|
| UserBranchRole.role | owner, manager, chef, waiter, cashier, kitchen_display |
| Table.status | available, occupied, reserved, blocked |
| TableSession.status | active, closed, cancelled |
| Round.status | draft, sent, preparing, ready, delivered, cancelled |
| RoundItem.status | pending, preparing, ready, delivered, cancelled |
| KitchenTicket.status | pending, in_progress, ready, delivered, cancelled |
| Check.status | open, closed, voided |
| Payment.method | cash, card, mercadopago, transfer |
| Payment.status | pending, completed, failed, refunded |
| ServiceCall.type | waiter, water, bill, other |
| ServiceCall.status | pending, acknowledged, resolved, cancelled |
| ProductAllergen.severity | contains, may_contain, trace |
| Promotion.discount_type | percentage, fixed_amount, buy_x_get_y |
| Allocation.split_type | equal, custom, full |

**Decision**: Store as String(20-30), NOT as PostgreSQL ENUM type.
**Rationale**: PostgreSQL ENUMs require `ALTER TYPE` to add values, which is painful in migrations. String columns with CHECK constraints or application-level validation (Pydantic) are more flexible. The slight storage overhead is negligible.

## 4. Docker Compose Service Topology

```yaml
# Service dependency graph:
#
#   postgres ──┐
#              ├──> api (:8000)
#   redis ────┘
#              ├──> gateway (:8001)
#   redis ────┘
#
# Network: buen-sabor-net (bridge)
# Volumes: pgdata (postgres), redisdata (redis)
```

### Service Details

| Service | Image | Port | Health Check | Depends On | Volumes |
|---------|-------|------|-------------|------------|---------|
| postgres | pgvector/pgvector:0.8.0-pg16 | 5432:5432 | `pg_isready -U $POSTGRES_USER` interval=5s, retries=5 | — | pgdata:/var/lib/postgresql/data |
| redis | redis:7-alpine | 6379:6379 | `redis-cli ping` interval=5s, retries=5 | — | redisdata:/data |
| api | build: rest_api/ | 8000:8000 | `curl -f http://localhost:8000/api/health/live` interval=10s, start_period=15s | postgres (healthy), redis (healthy) | ./shared:/app/shared (dev mount) |
| gateway | build: ws_gateway/ | 8001:8001 | — (stub) | postgres (healthy), redis (healthy) | ./shared:/app/shared |

### Environment Variables

```
# .env (local development)
POSTGRES_USER=buensabor
POSTGRES_PASSWORD=buensabor_dev_2024
POSTGRES_DB=buensabor
DATABASE_URL=postgresql+asyncpg://buensabor:buensabor_dev_2024@postgres:5432/buensabor
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
API_PREFIX=/api
```

## 5. Sequence Diagrams

### 5.1 Health Check — Ready

```
Client          API Router       PostgreSQL    Redis
  |                |                |            |
  |  GET /health/ready             |            |
  |--------------->|                |            |
  |                | SELECT 1       |            |
  |                |--------------->|            |
  |                |    OK          |            |
  |                |<---------------|            |
  |                |                | PING       |
  |                |                |----------->|
  |                |                |   PONG     |
  |                |                |<-----------|
  |                |                             |
  |   200 {status: ready, checks: {pg: ok, redis: ok}}
  |<---------------|                             |
```

### 5.2 Seed Data Execution

```
Seed Script      AsyncSession     PostgreSQL
  |                  |                |
  | Check if tenant exists            |
  |----------------->|  SELECT        |
  |                  |--------------->|
  |   Result         |                |
  |<-----------------|<---------------|
  |                  |                |
  | [if not exists]  |                |
  | Create Tenant    |                |
  |----------------->| INSERT         |
  |                  |--------------->|
  | Create Branch    |                |
  |----------------->| INSERT         |
  |                  |--------------->|
  | Create Sectors   |                |
  |----------------->| INSERT ×3      |
  |                  |--------------->|
  | Create Tables    |                |
  |----------------->| INSERT ×20     |
  |                  |--------------->|
  | Create Users     |                |
  |----------------->| INSERT ×6      |
  |                  |--------------->|
  | Create Allergens |                |
  |----------------->| INSERT ×14     |
  |                  |--------------->|
  | Create Categories|                |
  |----------------->| INSERT ×5      |
  |                  |--------------->|
  | Create Subcats   |                |
  |----------------->| INSERT ×10+    |
  |                  |--------------->|
  | Create Products  |                |
  |----------------->| INSERT ×30+    |
  |                  |--------------->|
  | Create Profiles  |                |
  |----------------->| INSERT ×22     |
  |                  |--------------->|
  | Commit           |                |
  |----------------->| COMMIT         |
  |                  |--------------->|
  |   Done           |                |
  |<-----------------|<---------------|
```

## 6. Key Design Patterns

### 6.1 Repository Pattern with Generics

```python
# Pseudocode showing the repository hierarchy
class BaseRepository(Generic[T]):
    model: Type[T]
    session: AsyncSession

    async def get_by_id(id, include_deleted=False) -> T | None
    async def get_all(skip=0, limit=100, include_deleted=False) -> list[T]
    async def create(obj: T) -> T
    async def update(obj: T) -> T
    async def soft_delete(id, user_id=None) -> T
    async def restore(id) -> T

class TenantRepository(BaseRepository[T]):
    tenant_id: int  # Set in constructor
    # ALL queries automatically add WHERE tenant_id = self.tenant_id

class BranchRepository(TenantRepository[T]):
    branch_id: int  # Set in constructor
    # ALL queries add WHERE tenant_id = X AND branch_id = Y
```

### 6.2 FastAPI App Factory Pattern

```python
# rest_api/app/main.py pseudocode
def create_app() -> FastAPI:
    app = FastAPI(title="Buen Sabor API", lifespan=lifespan)
    app.include_router(health_router, prefix="/api/health")
    return app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run migrations + seed
    await run_migrations()
    await run_seed()
    yield
    # Shutdown: close connections
    await engine.dispose()
```

### 6.3 Idempotent Seed Pattern

```python
# Pseudocode for idempotent seeding
async def seed_tenant(session):
    existing = await session.execute(
        select(Tenant).where(Tenant.slug == "buen-sabor")
    )
    if existing.scalar_one_or_none():
        return  # Already seeded
    tenant = Tenant(name="Buen Sabor", slug="buen-sabor")
    session.add(tenant)
    # ... continue with dependent entities
```

## 7. Dockerfile Strategy

### Multi-stage Build (rest_api/Dockerfile)

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /build
COPY shared/ ./shared/
COPY rest_api/pyproject.toml ./rest_api/
RUN pip install --no-cache-dir ./shared ./rest_api

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY shared/ ./shared/
COPY rest_api/ ./rest_api/
COPY alembic/ ./alembic/
COPY alembic.ini .
CMD ["uvicorn", "rest_api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

For development, the `--reload` flag + volume mount enables hot-reload.

## 8. Trade-offs Considered

| Decision | Alternative Considered | Why Rejected |
|----------|----------------------|--------------|
| Row-level tenancy | Schema-per-tenant | Too complex for Alembic, shared queries impossible |
| Integer cents | Decimal column | Serialization overhead, Pydantic conversion noise |
| String enums | PostgreSQL ENUM | ALTER TYPE is migration-hostile |
| Single initial migration | Per-domain migrations | FK cross-domain dependencies, all needed at once |
| asyncpg | psycopg3 async | asyncpg is faster and more mature for async |
| Soft delete everywhere | Physical delete + audit log | Simpler model, legal retention, undo capability |
| No FK on audit columns | FK to users.id | Circular dependency on users table |
| Auto table naming | Manual __tablename__ | Less boilerplate, consistent naming |
| passlib bcrypt | argon2 | bcrypt is battle-tested and simpler to configure |
| pre-commit + ruff | black + isort + flake8 | ruff replaces all three, faster, single tool |
