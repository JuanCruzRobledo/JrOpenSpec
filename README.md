# Integrador — Sistema de Gestion para Restaurantes

Sistema de gestion integral para restaurantes multi-sucursal. Monorepo con backend, gateway WebSocket y tres frontends (Dashboard admin, PWA para clientes, PWA para mozos).

## Stack Tecnologico

| Componente | Tecnologia | Puerto |
|------------|-----------|--------|
| **backend** | FastAPI 0.115 + SQLAlchemy 2.0 + PostgreSQL 16 | 8000 |
| **ws_gateway** | FastAPI WS + Redis Pub/Sub + Streams | 8001 |
| **Dashboard** | React 19 + Zustand + Vite 7.2 | 5177 |
| **pwaMenu** | React 19 + i18next + Workbox (PWA) | 5176 |
| **pwaWaiter** | React 19 + Zustand + JWT (PWA) | 5178 |
| **PostgreSQL** | postgres:16 + pgvector | 5432 |
| **Redis** | redis:7-alpine | 6380 |

## Pre-requisitos

- Node.js 20+
- Python 3.12+
- Docker & Docker Compose
- PostgreSQL 16 (via Docker)
- Redis 7 (via Docker)

## Quick Start

```bash
# 1. Clonar el repositorio
git clone <repo-url> integrador
cd integrador

# 2. Configurar variables de entorno
cp env.example .env
# Editar .env con tus valores locales

# 3. Levantar infraestructura con Docker
docker compose up -d postgres redis

# 4. Instalar dependencias del backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -e ../shared
pip install -r requirements.txt

# 5. Correr migraciones
cd ..
alembic upgrade head

# 6. Seed de datos demo
python -m rest_api.seed

# 7. Levantar backend
python -m uvicorn rest_api.main:app --reload --port 8000

# 8. Levantar WS Gateway (otra terminal)
export PYTHONPATH=$PWD/backend
python -m uvicorn ws_gateway.main:app --reload --port 8001

# 9. Instalar y levantar frontends (cada uno en su terminal)
cd Dashboard && npm install && npm run dev
cd pwaMenu && npm install && npm run dev
cd pwaWaiter && npm install && npm run dev

# 10. Correr tests
cd backend && pytest
cd Dashboard && npm test
```

## Estructura del Proyecto

```
integrador/
├── backend/              # FastAPI REST API
│   ├── rest_api/         # App principal (routers, services, models)
│   └── shared/           # Modulos compartidos (config, DB, auth, utils)
├── ws_gateway/           # WebSocket Gateway (tiempo real)
├── Dashboard/            # Panel de administracion (React 19 + Zustand)
├── pwaMenu/              # Menu para clientes PWA (i18n es/en/pt)
├── pwaWaiter/            # PWA para mozos (offline-first)
├── devOps/               # Docker Compose, Grafana
├── openspec/             # Especificaciones SDD
│   ├── knowledge/        # Documentacion destilada del sistema
│   └── changes/          # Artefactos por fase (proposal, spec, design, tasks)
├── alembic/              # Migraciones de base de datos
├── docker-compose.yml
└── .env.example
```

## Documentacion

La documentacion tecnica esta en `openspec/knowledge/`:

| Documento | Contenido |
|-----------|-----------|
| `00-roadmap.md` | 16 fases del roadmap con dependencias |
| `01-vision-roles.md` | Vision del producto, usuarios, RBAC |
| `02-arquitectura-stack.md` | Arquitectura, stack, puertos, ADRs |
| `03-modelo-datos.md` | Modelo de datos completo (54+ entidades) |
| `04-reglas-dominio.md` | Reglas de negocio, lifecycles |
| `05-seguridad.md` | Auth, JWT, Table Token, middlewares |
| `06-eventos-ws.md` | Catalogo de eventos WebSocket |
| `07-patrones-frontend.md` | React 19, Zustand, i18n, hooks |
| `08-patrones-backend.md` | FastAPI, Domain Services, Clean Architecture |
| `09-sprint-planning.md` | Sprint planning, dependencias, camino critico |

## Workflow de Desarrollo

El proyecto usa **Spec-Driven Development (SDD)**: toda feature pasa por fases de especificacion antes de escribir codigo.

```
explore → propose → spec → design → tasks → apply → verify → archive
```

### Estrategia de branches
- Naming: `feature/{phase-name}/{descripcion}`
- PRs requieren revision humana para fases con gobernanza CRITICO o ALTO
- Correr tests antes de pushear

### Niveles de gobernanza

| Nivel | Dominios | Accion |
|-------|---------|--------|
| CRITICO | Auth, Billing, Allergens, Staff | Solo analisis — sin codigo de produccion |
| ALTO | Products, WebSocket, Rate Limiting | Proponer + esperar revision humana |
| MEDIO | Orders, Kitchen, Waiter, Tables, Customer | Implementar con checkpoints |
| BAJO | Categories, Sectors, Recipes, Ingredients | Autonomia total si pasan los tests |

## Variables de Entorno

Ver `env.example` en la raiz del proyecto. Cada componente frontend usa variables Vite (`VITE_API_URL`, `VITE_WS_URL`, etc.) definidas en su propio `.env`.

### Variables principales

| Variable | Descripcion | Ejemplo |
|----------|------------|---------|
| `DATABASE_URL` | Conexion PostgreSQL (asyncpg) | `postgresql+asyncpg://user:pass@localhost:5432/integrador` |
| `REDIS_URL` | Conexion Redis | `redis://localhost:6380/0` |
| `JWT_SECRET` | Secreto para firmar tokens JWT | (generar con `openssl rand -hex 32`) |
| `TABLE_TOKEN_SECRET` | Secreto HMAC para table tokens | (generar con `openssl rand -hex 32`) |
| `ENVIRONMENT` | Entorno de ejecucion | `dev` / `staging` / `prod` |
| `VITE_API_URL` | URL del backend (frontends) | `http://localhost:8000/api` |
| `VITE_WS_URL` | URL del WS Gateway (frontends) | `ws://localhost:8001` |
