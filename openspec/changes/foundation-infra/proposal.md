---
change: foundation-infra
phase: 1
artifact: proposal
source: sdd-otro/sprint-1-infra
date: 2026-03-23
status: approved
---

# SDD Proposal: Sprint 1 — Infraestructura y Modelo de Datos

## 1. Intent

Establecer la base técnica completa del sistema "Buen Sabor": monorepo estructurado, entorno containerizado con Docker Compose, base de datos PostgreSQL 16 con pgvector poblada con seed data, cache Redis 7, los 52+ modelos SQLAlchemy organizados por dominio, repositorios base con filtrado multi-tenant, migraciones Alembic, health checks, y pipeline CI mínimo. Al completar este sprint, cualquier desarrollador (humano o AI) puede clonar el repo, hacer `docker compose up`, y tener un entorno funcional con datos de prueba listos para desarrollar features.

## 2. Scope

### In Scope
- Estructura de directorios del monorepo (rest_api/, ws_gateway/, shared/, pwa_menu/, pwa_waiter/, dashboard/)
- Docker Compose con servicios: PostgreSQL 16 (pgvector), Redis 7, API (:8000), Gateway (:8001)
- Infraestructura de base de datos: engine async, session management, safe_commit
- AuditMixin universal (created_at, updated_at, deleted_at, created_by, updated_by, deleted_by, is_active)
- 52+ modelos SQLAlchemy organizados por dominio (10 dominios)
- Migraciones Alembic (initial migration)
- TenantRepository y BranchRepository con filtrado automático por tenant_id
- Health checks: GET /api/health/live y GET /api/health/ready
- Seed data: tenant "Buen Sabor", sucursal con 3 sectores, usuarios prueba, categorías, productos, 14 alérgenos EU
- CI base: ruff (linting), mypy (type checking), pre-commit hooks

### Out of Scope
- Autenticación/autorización (JWT, RBAC) — Sprint 2
- WebSocket Gateway funcional — Sprint 3
- PWAs (menu, waiter, dashboard) — Sprints posteriores
- Deployment a Kubernetes — Post-MVP
- Tests unitarios/integración — se agregan junto con features
- Endpoints de negocio (CRUD de productos, pedidos, etc.)

## 3. Affected Modules

| Module | Impact | Description |
|--------|--------|-------------|
| `shared/` | **NEW** | Infraestructura DB, modelos, mixins, repositorios base |
| `rest_api/` | **NEW** | Aplicación FastAPI, health checks, configuración |
| `ws_gateway/` | **STUB** | Solo estructura de directorio y Dockerfile |
| `pwa_menu/` | **STUB** | Solo estructura de directorio |
| `pwa_waiter/` | **STUB** | Solo estructura de directorio |
| `dashboard/` | **STUB** | Solo estructura de directorio |
| Root | **NEW** | Docker Compose, pyproject.toml, pre-commit config, alembic.ini |

## 4. Approach

### 4.1 Monorepo Structure
Estructura flat con shared/ como paquete Python instalable en modo editable (`pip install -e shared/`). Cada servicio backend (rest_api, ws_gateway) importa shared. Los frontends son proyectos independientes con su propio package.json.

### 4.2 Database Layer
- SQLAlchemy 2.0 con asyncpg como driver async
- AsyncSession con scoped session factory
- `safe_commit()` como wrapper que maneja IntegrityError, rollback automático
- Declarative base con AuditMixin aplicado a TODOS los modelos
- Nomenclatura de tablas: snake_case plural (ej: `users`, `branch_products`)

### 4.3 Multi-Tenant Isolation
- Aislamiento a nivel de fila: TODAS las tablas con tenant relevance tienen `tenant_id` NOT NULL
- BaseRepository con `_apply_tenant_filter()` automático
- NO se usa schema-per-tenant (complejidad excesiva para el MVP)

### 4.4 Model Organization
Modelos agrupados en submódulos por dominio bajo `shared/models/`:
- `core/` — Tenant, Branch, User, UserBranchRole
- `catalog/` — Category, Subcategory, Product, BranchProduct, ProductAllergen, Allergen
- `profiles/` — CookingMethod, FlavorProfile, TextureProfile, CuisineType
- `ingredients/` — IngredientGroup, Ingredient, SubIngredient
- `room/` — Sector, Table, TableSession, Diner
- `orders/` — Round, RoundItem, KitchenTicket
- `billing/` — Check, Charge, Allocation, Payment
- `services/` — ServiceCall, WaiterSectorAssignment
- `marketing/` — Promotion, PromotionProduct, Badge, Seal
- `recipes/` — Recipe, RecipeIngredient, RecipeStep

### 4.5 Docker Strategy
- Multi-stage Dockerfile para API (builder + runtime)
- Docker Compose con health checks nativos en todos los servicios
- Volúmenes persistentes para PostgreSQL y Redis
- Network interna `buen-sabor-net`

### 4.6 CI Pipeline
- pre-commit hooks: ruff format, ruff check, mypy
- GitHub Actions (futuro): lint + type check en PRs

## 5. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| 52+ modelos con relaciones complejas generan migraciones frágiles | Alta | Media | Una sola migración initial; tests de migración up/down |
| AuditMixin en todas las tablas agrega overhead en writes | Baja | Baja | Los campos audit son opcionales (nullable created_by etc.) excepto timestamps |
| pgvector extension no disponible en PostgreSQL base | Media | Alta | Usar imagen `pgvector/pgvector:pg16` en Docker |
| Modelos definidos sin features pueden cambiar mucho | Media | Media | Alembic autogenerate facilita cambios; modelos diseñados desde specs completos |
| Dependencia circular entre modelos de distintos dominios | Media | Alta | Usar `relationship(back_populates=...)` con lazy loading; string references para FK |
| shared/ como paquete editable puede causar problemas de import | Baja | Media | Configurar correctamente pyproject.toml con paquetes y usar importaciones absolutas |

## 6. Rollback Plan

- **Docker**: `docker compose down -v` destruye todo el entorno
- **Database**: `alembic downgrade base` revierte todas las migraciones
- **Code**: Revert del commit/PR que introduce el sprint
- **Partial rollback**: No aplica — este sprint es atómico (infraestructura base)

## 7. Success Criteria

1. `docker compose up` levanta todos los servicios sin errores
2. `GET /api/health/live` responde 200
3. `GET /api/health/ready` responde 200 (confirma conexión a DB y Redis)
4. Base de datos tiene todas las tablas creadas con seed data
5. `ruff check` y `mypy` pasan sin errores
6. Alembic migration up/down funciona sin errores

## 8. Estimated Effort

- **Total**: 8-12 sesiones de AI agent
- **Fase 1** (Infra): 2-3 sesiones (monorepo, Docker, DB setup)
- **Fase 2** (Modelos): 3-4 sesiones (52+ modelos, relaciones, migraciones)
- **Fase 3** (Repos + Health): 1-2 sesiones
- **Fase 4** (Seed + CI): 2-3 sesiones
