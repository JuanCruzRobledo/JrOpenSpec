# Arquitectura y Stack Tecnológico

> Fuente de verdad para: todas las fases SDD, especialmente foundation-auth, realtime-infra, dashboard, pwa-waiter, pwa-menu

---

## Índice de ADRs

| ADR | Decisión |
|-----|----------|
| [ADR-001](#adr-001-monorepo-con-5-componentes) | Monorepo con 5 componentes |
| [ADR-002](#adr-002-fastapi--sqlalchemy-20) | FastAPI + SQLAlchemy 2.0 |
| [ADR-003](#adr-003-zustand-no-redux-no-context) | Zustand (no Redux, no Context) |
| [ADR-004](#adr-004-jwt--table-token-sin-sessions-server-side) | JWT + Table Token (sin sessions server-side) |
| [ADR-005](#adr-005-redis-pubsub--streams-no-kafka) | Redis Pub/Sub + Streams (no Kafka) |
| [ADR-006](#adr-006-outbox-pattern-para-eventos-críticos) | Outbox pattern para eventos críticos |
| [ADR-007](#adr-007-pwa-no-app-nativa) | PWA (no app nativa) |
| [ADR-008](#adr-008-soft-delete-no-hard-delete) | Soft delete (no hard delete) |
| [ADR-009](#adr-009-strategy-pattern-para-rbac) | Strategy pattern para RBAC |
| [ADR-010](#adr-010-worker-pool-broadcast) | Worker pool broadcast |

> Detalle completo de cada ADR en la sección [Decisiones arquitectónicas](#decisiones-arquitectónicas-adr) al final del documento.

---

## Estructura del monorepo

```
integrador/
├── backend/
│   ├── rest_api/
│   │   ├── core/              # App config, middlewares, CORS
│   │   ├── models/            # 21 archivos SQLAlchemy (54+ tablas)
│   │   ├── routers/           # 48 archivos, 9 grupos
│   │   │   ├── admin/         # 15 routers CRUD
│   │   │   ├── auth/          # Login, refresh, logout
│   │   │   ├── billing/       # Pagos, webhooks
│   │   │   ├── content/       # Recetas, ingredientes, RAG
│   │   │   ├── diner/         # Cart, orders, customer
│   │   │   ├── kitchen/       # Rounds, tickets
│   │   │   ├── public/        # Menu, health (sin auth)
│   │   │   ├── tables/        # Sessions
│   │   │   └── waiter/        # Waiter operations
│   │   ├── services/
│   │   │   ├── domain/        # 14 domain services
│   │   │   ├── crud/          # Repository, soft delete
│   │   │   ├── permissions/   # RBAC Strategy pattern
│   │   │   ├── events/        # Outbox service
│   │   │   └── payments/      # Payment processing
│   │   ├── main.py            # FastAPI entry point
│   │   └── seed.py            # Demo data
│   ├── shared/                # Compartido entre backend + ws_gateway
│   │   ├── config/            # Settings, logging, constants
│   │   ├── security/          # Auth, passwords, blacklist
│   │   ├── infrastructure/    # DB engine, Redis pool, events
│   │   └── utils/             # Exceptions, validators, schemas
│   └── tests/                 # Suite pytest
│
├── Dashboard/                 # React 19 admin SPA (puerto 5177)
├── pwaMenu/                   # React 19 customer PWA (puerto 5176)
├── pwaWaiter/                 # React 19 waiter PWA (puerto 5178)
│
├── ws_gateway/                # WebSocket Gateway (puerto 8001)
│   ├── main.py
│   ├── connection_manager.py  # Orchestrator liviano
│   ├── redis_subscriber.py    # Orchestrator liviano
│   ├── core/
│   │   ├── connection/        # Lifecycle, Broadcaster, Cleanup, Stats
│   │   └── subscriber/        # Event processing
│   └── components/
│       ├── auth/              # JWT + TableToken strategies
│       ├── broadcast/         # Router, strategies (Batch, Adaptive)
│       ├── connection/        # Index, LockManager
│       ├── core/              # Constants, WSCloseCodes
│       ├── events/            # EventRouter, filtering
│       └── rate_limit/        # Lua scripts, per-connection
│
└── devOps/                    # Docker Compose, Grafana
    └── docker-compose.yml
```

### Subproyectos — resumen

| Componente | Puerto | Descripción | Stack |
|------------|--------|-------------|-------|
| **Dashboard** | 5177 | Panel admin, gestión multi-sucursal | React 19 + Zustand + Vite 7.2 |
| **pwaMenu** | 5176 | Menú cliente con pedido colaborativo, i18n (es/en/pt) | React 19 + PWA (Workbox) + i18next |
| **pwaWaiter** | 5178 | PWA mozo, gestión de mesas por sector | React 19 + Zustand + JWT |
| **backend** | 8000 | REST API principal | FastAPI 0.115 + SQLAlchemy 2.0 |
| **ws_gateway** | 8001 | Gateway WebSocket tiempo real | FastAPI WS + Redis Pub/Sub + Streams |

---

## Stack por componente

### Backend (FastAPI)

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| Python | 3.11 | Runtime |
| FastAPI | 0.115 | Framework HTTP + WebSocket |
| SQLAlchemy | 2.0 | ORM (async-compatible) |
| Pydantic | 2 | Validación de schemas |
| PostgreSQL | 16 + pgvector | Base de datos principal |
| Redis | 7 | Cache, Pub/Sub, Streams, token blacklist, rate limiting |
| uvicorn | latest | ASGI server |
| pytest | latest | Suite de tests |
| watchfiles | latest | Hot reload (Windows) |

### Frontend — Dashboard

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| React | 19.2.0 | UI framework |
| React Router | 7.2.0 | Routing (nested bajo Layout) |
| TypeScript | 5.9 (strict) | Tipado estático |
| Vite | 7.2.4 | Build tool + dev server |
| Zustand | 5.0.9 | State management (15 stores con persistencia localStorage) |
| Tailwind CSS | 4 | Estilos |
| Lucide React | latest | Iconos |
| babel-plugin-react-compiler | 1.0.0 | Memoización automática |
| vite-plugin-pwa | 1.2.0 | PWA support |
| Vitest | 4.0 | Testing (100+ tests) |
| eslint-plugin-react-hooks | 7.0.1 | React Compiler lint rules |

**Características específicas:**
- 24+ páginas funcionales, roles ADMIN y MANAGER
- Comunicación: HTTP REST + WebSocket (`/ws/admin`)
- Patterns: `useFormModal`, `useConfirmDialog`, `BroadcastChannel` (multi-tab sync)
- `useActionState` (React 19) para formularios CRUD
- Code splitting con `React.lazy()` en todas las páginas

### Frontend — pwaMenu

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| React | 19.2.0 | UI framework |
| TypeScript | 5.9 | Tipado estático |
| Vite | 7.2 | Build tool |
| Zustand | latest | State management (`tableStore` modular) |
| i18next | latest | i18n — es/en/pt, detección automática |
| Workbox | latest | PWA — CacheFirst (imágenes 30d), NetworkFirst (APIs 5s timeout) |
| babel-plugin-react-compiler | latest | Memoización automática |

**Características específicas:**
- Auth: Table Token (HMAC, 3h) via header `X-Table-Token`
- Carrito colaborativo multi-dispositivo via WebSocket
- Patterns: `useOptimistic` (React 19), `RoundConfirmationPanel`, `useImplicitPreferences`
- `tableStore` modular: `store.ts`, `selectors.ts`, `helpers.ts`, `types.ts`
- TODAS las strings de UI deben usar `t()` — cero hardcoded strings

### Frontend — pwaWaiter

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| React | 19.2.0 | UI framework |
| TypeScript | 5.9 | Tipado estático |
| Vite | 7.2 | Build tool |
| Zustand | latest | State management (3 stores) |
| Vitest | 3.2 | Testing |
| babel-plugin-react-compiler | latest | Memoización automática |

**Características específicas:**
- Auth: JWT + verificación de asignación diaria (`WaiterSectorAssignment`)
- Pre-login flow: selección de sucursal ANTES de autenticarse
- Features: grilla por sector, comanda rápida, push notifications
- Patterns: `RetryQueueStore` (offline-first), sector grouping

### Infraestructura

| Servicio | Puerto | Imagen | Propósito |
|----------|--------|--------|-----------|
| PostgreSQL | 5432 | postgres:16 + pgvector | Base de datos principal |
| Redis | 6380 | redis:7 | Cache, Pub/Sub, Streams, token blacklist, rate limiting |
| pgAdmin | 5050 | dpage/pgadmin4 | GUI administración DB |
| Grafana | — | grafana/grafana | Monitoreo (en `devOps/`) |

---

## Clean Architecture (Backend)

### Capas

```
┌─────────────────────────────────────────────┐
│              ROUTERS (thin controllers)      │
│  - HTTP parsing, validación Pydantic        │
│  - Dependency injection (auth, DB)          │
│  - Construcción de respuesta                │
│  - SIN lógica de negocio                    │
├─────────────────────────────────────────────┤
│           DOMAIN SERVICES                   │
│  - TODA la lógica de negocio                │
│  - CategoryService, ProductService, etc.    │
│  - BaseCRUDService / BranchScopedService    │
│  - Hooks: _validate_create, _after_delete   │
├─────────────────────────────────────────────┤
│             REPOSITORIES                    │
│  - TenantRepository, BranchRepository       │
│  - Auto-filtran por tenant_id/branch_id     │
│  - Eager loading preconfigurado             │
│  - Prevención N+1                           │
├─────────────────────────────────────────────┤
│               MODELS                        │
│  - 54+ clases SQLAlchemy                    │
│  - AuditMixin (soft delete, timestamps)     │
│  - CHECK constraints                        │
│  - 21 archivos por dominio                  │
└─────────────────────────────────────────────┘
```

### Deprecación de CRUDFactory

**CRUDFactory está deprecado.** Para cualquier feature nueva, usar Domain Services:

```python
# Router (thin — delega al service)
@router.get("/categories")
def list_categories(db: Session = Depends(get_db), user: dict = Depends(current_user)):
    ctx = PermissionContext(user)
    service = CategoryService(db)
    return service.list_by_branch(ctx.tenant_id, branch_id)
```

**Domain Services disponibles:**
`CategoryService`, `SubcategoryService`, `BranchService`, `SectorService`, `TableService`,
`ProductService`, `AllergenService`, `StaffService`, `PromotionService`, `RoundService`,
`BillingService`, `DinerService`, `ServiceCallService`, `TicketService`

**Clases base:** `BaseCRUDService[Model, Output]`, `BranchScopedService[Model, Output]`

**Cómo crear un nuevo Domain Service:**
```python
# 1. Crear en rest_api/services/domain/my_entity_service.py
from rest_api.services.base_service import BranchScopedService
from shared.utils.admin_schemas import MyEntityOutput

class MyEntityService(BranchScopedService[MyEntity, MyEntityOutput]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=MyEntity, output_schema=MyEntityOutput, entity_name="Mi Entidad")
    def _validate_create(self, data: dict, tenant_id: int) -> None: ...
    def _after_delete(self, entity_info: dict, user_id: int, user_email: str) -> None: ...
# 2. Exportar en rest_api/services/domain/__init__.py
# 3. Usar en router (mantener el router thin)
```

### Estructura de la API

```
/api/auth/login, /me, /refresh            # Autenticación JWT
/api/public/menu/{slug}                    # Menú público (sin auth)
/api/public/branches                       # Sucursales públicas (sin auth — pwaWaiter pre-login)
/api/tables/{id}/session                   # Sesión por ID numérico
/api/tables/code/{code}/session            # Sesión por código de mesa (ej: "INT-01")
/api/diner/*                               # Operaciones del comensal (auth: X-Table-Token)
/api/customer/*                            # Loyalty del cliente (auth: X-Table-Token)
/api/kitchen/*                             # Operaciones cocina (JWT + rol KITCHEN)
/api/recipes/*                             # CRUD recetas (JWT + KITCHEN/MANAGER/ADMIN)
/api/billing/*                             # Operaciones de pago
/api/waiter/*                              # Operaciones mozo (JWT + rol WAITER)
/api/waiter/tables/{id}/activate           # Activar mesa (crear sesión)
/api/waiter/sessions/{id}/rounds           # Mozo carga ronda para clientes sin teléfono
/api/waiter/sessions/{id}/check            # Mozo solicita cuenta
/api/waiter/payments/manual                # Registrar pago efectivo/tarjeta/transferencia
/api/waiter/tables/{id}/close              # Cerrar mesa post-pago
/api/waiter/branches/{id}/menu             # Menú compacto para comanda rápida (sin imágenes)
/api/admin/*                               # CRUD Dashboard (JWT + RBAC, soporta ?limit=&offset=)
```

---

## WebSocket Gateway — Arquitectura

### Topología del gateway

```
Frontend ──WS──→ WS Gateway (:8001)
                    │
                    ├─← Redis Pub/Sub (subscribe a eventos por branch)
                    ├─← Redis Streams (eventos críticos, at-least-once)
                    └─→ Frontend (broadcast a clientes conectados)
```

### Componentes

- `connection_manager.py` y `redis_subscriber.py` son orchestrators livianos que componen módulos de `core/`
- `components/` contiene arquitectura modular: auth strategies, broadcast router, event router, rate limiter, circuit breaker
- Ambas rutas de import funcionan: `from ws_gateway.components import X` y `from ws_gateway.components.broadcast.router import X`

### Autenticación (Strategy pattern)

| Estrategia | Clientes | Token |
|-----------|---------|-------|
| `JWTAuthStrategy` | Staff (Dashboard, pwaWaiter, Kitchen) | JWT query param `?token=` |
| `TableTokenAuthStrategy` | Comensales (pwaMenu) | HMAC query param `?table_token=` |

### Endpoints WebSocket

```
/ws/waiter?token=JWT    # Notificaciones mozo (filtradas por sector)
/ws/kitchen?token=JWT   # Notificaciones cocina
/ws/diner?table_token=  # Actualizaciones tiempo real del comensal
/ws/admin?token=JWT     # Notificaciones admin (Dashboard)
```

### Broadcast y resiliencia

| Aspecto | Detalle |
|---------|---------|
| Worker pool | 10 workers paralelos, ~160ms para 400 usuarios |
| Fallback | Batch legacy (50 por batch) |
| Circuit breaker | 3 estados: closed / open (30s) / half-open; abre tras 5 fallos |
| Retry | Jitter decorrelacionado para evitar thundering herd |
| Sharded locks | Por branch, orden estricto anti-deadlock |
| Delivery (Pub/Sub) | At-most-once — eventos de baja criticidad |
| Delivery (Streams) | At-least-once con DLQ tras 3 reintentos |

### Outbox Pattern (garantía de entrega para eventos críticos)

```
REST API:
  1. Escribe datos de negocio + OutboxEvent → PostgreSQL (commit atómico)
  2. Procesador background lee OutboxEvent no publicado
  3. Publica en Redis Streams
  4. Marca como publicado

WS Gateway:
  5. StreamConsumer lee de Redis Streams (consumer group)
  6. Broadcast a clientes conectados
  7. ACK del mensaje
  8. Fallos → DLQ tras 3 reintentos
```

| Patrón | Eventos |
|--------|---------|
| Outbox (no se puede perder) | `CHECK_REQUESTED/PAID`, `PAYMENT_*`, `ROUND_SUBMITTED/READY`, `SERVICE_CALL_CREATED` |
| Redis directo (menor latencia) | `ROUND_CONFIRMED/IN_KITCHEN/SERVED`, `CART_*`, `TABLE_*`, `ENTITY_*` |

### Eventos y routing

**Round lifecycle:** `PENDING → CONFIRMED → SUBMITTED → IN_KITCHEN → READY → SERVED`

**Flujo por rol (restricción):**
```
PENDING    → CONFIRMED → SUBMITTED  → IN_KITCHEN → READY    → SERVED
(Comensal)  (Mozo)      (Admin/Mgr)   (Cocina)    (Cocina)   (Staff)
```

La cocina NO ve pedidos en estado PENDING ni CONFIRMED. Solo ve SUBMITTED en adelante.

**Routing de eventos Round:**

| Evento | Admin | Cocina | Mozos | Comensales |
|--------|-------|--------|-------|------------|
| `ROUND_PENDING` | sí | no | sí (toda la branch) | no |
| `ROUND_CONFIRMED` | sí | no | sí | no |
| `ROUND_SUBMITTED` | sí | sí | sí | no |
| `ROUND_IN_KITCHEN`+ | sí | sí | sí | sí |

Filtrado por sector: eventos con `sector_id` solo llegan a mozos asignados. ADMIN/MANAGER reciben todos los eventos de la branch.

**Otros eventos:**
```
Cart:    CART_ITEM_ADDED, CART_ITEM_UPDATED, CART_ITEM_REMOVED, CART_CLEARED
Service: SERVICE_CALL_CREATED, SERVICE_CALL_ACKED, SERVICE_CALL_CLOSED
Billing: CHECK_REQUESTED, CHECK_PAID, PAYMENT_APPROVED, PAYMENT_REJECTED
Tables:  TABLE_SESSION_STARTED, TABLE_CLEARED, TABLE_STATUS_CHANGED
Admin:   ENTITY_CREATED, ENTITY_UPDATED, ENTITY_DELETED, CASCADE_DELETE

Heartbeat: {"type":"ping"} → {"type":"pong"} (intervalo 30s, timeout servidor 60s)
Close codes: 4001 (auth failed), 4003 (forbidden), 4029 (rate limited)
```

---

## Puertos en desarrollo

| Servicio | Puerto |
|----------|--------|
| REST API (backend) | 8000 |
| WebSocket Gateway | 8001 |
| Redis | 6380 |
| PostgreSQL | 5432 |
| pgAdmin | 5050 |
| Dashboard (frontend) | 5177 |
| pwaMenu (frontend) | 5176 |
| pwaWaiter (frontend) | 5178 |

---

## Seguridad — capas en profundidad

```
Layer 1: CORS + Origin Validation
  ↓
Layer 2: Content-Type Validation (POST/PUT/PATCH debe ser JSON o form)
  ↓
Layer 3: Security Headers (CSP, HSTS en prod, X-Frame-Options: DENY, nosniff)
  ↓
Layer 4: Rate Limiting (por IP + por usuario, Lua scripts atómicos)
  ↓
Layer 5: Authentication (JWT 15min / Table Token 3h)
  ↓
Layer 6: Authorization (RBAC via PermissionContext + Strategy)
  ↓
Layer 7: Input Validation (Pydantic + protección SSRF con validate_image_url)
  ↓
Layer 8: Database Constraints (CHECK, UNIQUE, FK)
```

### Autenticación por contexto

| Contexto | Método | Header/Param |
|----------|--------|--------------|
| Dashboard, pwaWaiter | JWT | `Authorization: Bearer {token}` |
| pwaMenu (comensales) | Table Token (HMAC) | `X-Table-Token: {token}` |
| WebSocket | JWT / Table Token | Query param `?token=` |

**Vidas de tokens:** Access 15min | Refresh 7 días (HttpOnly cookie) | Table token 3h

**Refresh strategy:** Dashboard y pwaWaiter renuevan proactivamente cada 14 min. Refresh tokens en HttpOnly cookies (`credentials: 'include'`). Token blacklist en Redis con patrón fail-closed.

### RBAC

| Rol | Crear | Editar | Eliminar |
|-----|-------|--------|---------|
| ADMIN | Todo | Todo | Todo |
| MANAGER | Staff, Tables, Allergens, Promotions (branches propias) | Igual | Ninguno |
| KITCHEN | Ninguno | Ninguno | Ninguno |
| WAITER | Ninguno | Ninguno | Ninguno |

---

## Imports canónicos

```python
# Backend — infraestructura
from shared.infrastructure.db import get_db, SessionLocal, safe_commit
from shared.config.settings import settings
from shared.config.logging import get_logger
from shared.security.auth import current_user_context, verify_jwt
from shared.infrastructure.events import get_redis_pool, publish_event

# Backend — utilidades
from shared.utils.exceptions import NotFoundError, ForbiddenError, ValidationError
from shared.utils.admin_schemas import CategoryOutput, ProductOutput
from shared.config.constants import Roles, RoundStatus, MANAGEMENT_ROLES

# Backend — modelos y servicios
from rest_api.models import Product, Category, Round
from rest_api.services.domain import ProductService, CategoryService
from rest_api.services.crud import TenantRepository, BranchRepository
from rest_api.services.crud.soft_delete import soft_delete
from rest_api.services.permissions import PermissionContext
from rest_api.services.events.outbox_service import write_billing_outbox_event

# WebSocket Gateway
from ws_gateway.components.core.constants import WSCloseCode, WSConstants
from ws_gateway.components.broadcast.router import BroadcastRouter
from ws_gateway.core.connection import ConnectionLifecycle, ConnectionBroadcaster
```

---

## Patrones críticos de frontend

### Zustand — siempre usar selectores

```typescript
// CORRECTO: siempre usar selectores
const items = useStore(selectItems)
const addItem = useStore((s) => s.addItem)

// MAL: nunca desestructurar (causa infinite re-render loops)
// const { items } = useStore()

// CRITICO: referencias estables para arrays fallback
const EMPTY_ARRAY: number[] = []
export const selectBranchIds = (s: State) => s.user?.branch_ids ?? EMPTY_ARRAY

// CRITICO: useShallow para arrays filtrados/computados
import { useShallow } from 'zustand/react/shallow'
const activeItems = useStore(useShallow(state => state.items.filter(i => i.active)))
```

### WebSocket — ref pattern para evitar acumulación de listeners

```typescript
const handleEventRef = useRef(handleEvent)
useEffect(() => { handleEventRef.current = handleEvent })
useEffect(() => {
  const unsubscribe = ws.on('*', (e) => handleEventRef.current(e))
  return unsubscribe
}, [])  // Deps vacíos — suscribirse una sola vez
```

### Conversiones de tipos frontend ↔ backend

```typescript
// IDs: backend = number, frontend = string
const frontendId = String(backendId)
const backendId = parseInt(frontendId, 10)

// Precios: backend = centavos (int), frontend = pesos (float)
const displayPrice = backendCents / 100    // 12550 → 125.50
const backendCents = Math.round(price * 100)

// Estado de sesión: backend UPPERCASE → frontend lowercase
```

---

## Gotchas y edge cases

### Windows — backend

- **StatReload puede fallar en Windows.** El proyecto usa `watchfiles` pero nuevas rutas pueden requerir restart manual del servidor.
- **uvicorn no está en PATH en Windows.** Usar siempre `python -m uvicorn` en lugar de `uvicorn` directo.
- **WS Gateway requiere PYTHONPATH.** Antes de levantar el gateway: `$env:PYTHONPATH = "$PWD\backend"` (PowerShell) o `export PYTHONPATH=$PWD/backend` (bash).

### Autenticación

- **Logout infinite loop.** En `api.ts`, `authAPI.logout()` debe deshabilitar retry en 401. Si no: token expirado → 401 → onTokenExpired → logout() → 401 → bucle infinito. Pasar `false` como tercer argumento a `fetchAPI` para deshabilitar retry.
- **Table codes NO son únicos across branches.** Siempre incluir `branch_slug` al llamar el endpoint de sesión por código.
- **WebSocket desconexión cada ~30s.** Verificar expiración del JWT. El cliente hace ping cada 30s, el servidor tiene timeout de 60s.

### Base de datos

- **Palabras reservadas SQL como nombres de tabla.** Ej: `Check` → usar `__tablename__ = "app_check"`.
- **Comparaciones booleanas en SQLAlchemy.** Usar `.is_(True)` y `.is_(False)`, nunca `== True`.
- **Race conditions.** Para operaciones concurrentes usar `select(...).with_for_update()`.

### Frontend

- **Desestructurar desde Zustand causa re-renders infinitos.** Siempre usar selectores.
- **Arrays filtrados sin `useShallow` causan infinite loops.** Siempre wrappear con `useShallow` cuando se filtra inline en el selector.
- **Async effects con componentes desmontados.** Usar mount guard:
  ```typescript
  useEffect(() => {
    let isMounted = true
    fetchData().then(data => { if (!isMounted) return; setData(data) })
    return () => { isMounted = false }
  }, [])
  ```

### CORS

- Dev usa puertos localhost por defecto. Al agregar nuevos orígenes, actualizar `DEFAULT_CORS_ORIGINS` en `backend/rest_api/main.py` Y en `ws_gateway/components/core/constants.py`.
- `pwaMenu`: `VITE_API_URL` debe incluir el sufijo `/api` (ej: `http://localhost:8000/api`).

### pwaMenu

- **QR scan no actualiza estado de mesa.** Verificar: (1) `VITE_BRANCH_SLUG` en `.env` coincide con DB, (2) `branch_slug` se pasa al endpoint de sesión, (3) WS Gateway está corriendo en :8001.

---

## Decisiones arquitectónicas (ADR)

### ADR-001: Monorepo con 5 componentes
- **Decisión**: Un único repositorio con backend, ws_gateway, Dashboard, pwaMenu y pwaWaiter.
- **Alternativas descartadas**: Polyrepo (un repo por componente), monolito con frontend embebido.
- **Justificación**: El monorepo permite compartir código (shared/), coordinar cambios cross-stack en un solo PR, y mantener coherencia de tipos. A diferencia del monolito, cada componente se despliega de forma independiente con su propio Dockerfile y puerto.

### ADR-002: FastAPI + SQLAlchemy 2.0
- **Decisión**: FastAPI como framework HTTP con SQLAlchemy 2.0 async y asyncpg como driver.
- **Alternativas descartadas**: Django REST Framework (sync, ORM menos flexible), Express.js (perdería tipado Python).
- **Justificación**: FastAPI es async-nativo con Pydantic integrado para validación de schemas. SQLAlchemy 2.0 ofrece `Mapped[]` annotations con tipado fuerte y compatibilidad async completa. asyncpg es el driver PostgreSQL más rápido para Python async.

### ADR-003: Zustand (no Redux, no Context)
- **Decisión**: Zustand como state manager en los 3 frontends.
- **Alternativas descartadas**: Redux Toolkit (demasiado boilerplate para el caso de uso), React Context (re-renders innecesarios sin selectores nativos).
- **Justificación**: Zustand ofrece mínimo boilerplate, selectores eficientes que evitan re-renders, persist middleware para localStorage, y se integra con el React Compiler. Los 15+ stores del Dashboard demuestran que escala sin complejidad adicional.

### ADR-004: JWT + Table Token (sin sessions server-side)
- **Decisión**: JWT para staff (Dashboard, pwaWaiter), HMAC Table Token para comensales (pwaMenu).
- **Alternativas descartadas**: Sessions server-side con cookies (requiere sticky sessions o session store compartido), OAuth2 completo (sobredimensionado para comensales).
- **Justificación**: JWT permite auth stateless sin necesidad de consultar la DB en cada request. El Table Token HMAC es lightweight para comensales que no tienen cuenta — se genera con branch_id + table_id + timestamp y dura 3 horas. Ambos esquemas coexisten con Strategy pattern en el WS Gateway.

### ADR-005: Redis Pub/Sub + Streams (no Kafka)
- **Decisión**: Redis Pub/Sub para eventos de baja criticidad, Redis Streams para eventos críticos (at-least-once).
- **Alternativas descartadas**: Apache Kafka (infraestructura pesada para la escala actual), RabbitMQ (otro servicio a mantener).
- **Justificación**: Redis ya se usa para cache, token blacklist y rate limiting — reutilizarlo para mensajería evita agregar infraestructura. Pub/Sub cubre notificaciones en tiempo real. Streams con consumer groups y DLQ cubren eventos críticos (pagos, pedidos) sin infra adicional.

### ADR-006: Outbox pattern para eventos críticos
- **Decisión**: Eventos críticos (CHECK_PAID, PAYMENT_*, ROUND_SUBMITTED) se escriben como OutboxEvent en PostgreSQL junto al cambio de negocio, y un procesador background los publica a Redis Streams.
- **Alternativas descartadas**: Publicar directo a Redis desde el endpoint (puede fallar después del commit), Change Data Capture con Debezium (infraestructura compleja).
- **Justificación**: El Outbox garantiza atomicidad: el evento se persiste en la misma transacción que el dato de negocio. Si Redis falla, el procesador reintenta. Evita la necesidad de un coordinador distribuido o two-phase commit.

### ADR-007: PWA (no app nativa)
- **Decisión**: Los 3 frontends son Progressive Web Apps, no apps nativas.
- **Alternativas descartadas**: React Native (doble codebase o limitaciones con web), apps nativas iOS/Android (triplicar esfuerzo de desarrollo).
- **Justificación**: Cero fricción de instalación — el comensal escanea un QR y accede al menú sin descargar nada. Un solo codebase web para todos los dispositivos. Workbox para cache offline y push notifications cubren los casos de uso del mozo sin necesidad de app store.

### ADR-008: Soft delete (no hard delete)
- **Decisión**: Todos los modelos usan AuditMixin con `is_active` + `deleted_at` en lugar de DELETE físico.
- **Alternativas descartadas**: Hard delete con tabla de auditoría separada (duplicación de schema), hard delete con triggers (frágil ante migraciones).
- **Justificación**: Los datos de restaurante tienen requisitos legales de retención (facturas, pagos). Soft delete provee audit trail completo, capacidad de restaurar entidades, y previene problemas de cascade. BaseRepository filtra `is_active=True` automáticamente.

### ADR-009: Strategy pattern para RBAC
- **Decisión**: Permisos implementados con Strategy pattern — cada rol tiene su propia estrategia de permisos.
- **Alternativas descartadas**: Decoradores por endpoint (repetitivo, difícil de testear), middleware global con whitelist (inflexible para reglas por recurso).
- **Justificación**: Cada estrategia encapsula las reglas de un rol (ADMIN, MANAGER, KITCHEN, WAITER), es testeable en aislamiento, y composable con mixins. Agregar un nuevo rol es crear una nueva estrategia sin modificar código existente — Open/Closed principle.

### ADR-010: Worker pool broadcast
- **Decisión**: Pool de 10 workers paralelos para broadcast de eventos WebSocket.
- **Alternativas descartadas**: Broadcast secuencial (4000ms para 400 usuarios), broadcast con asyncio.gather sin pool (sin control de concurrencia).
- **Justificación**: El broadcast secuencial escala linealmente con los usuarios conectados — inaceptable para tiempo real. El worker pool distribuye las conexiones entre workers paralelos con sharded locks por branch, logrando ~160ms para 400 usuarios (25x mejora). Fallback a batch legacy en caso de fallo del pool.

---

## Escalabilidad

| Dimensión | Estrategia | Capacidad |
|-----------|-----------|-----------|
| Usuarios concurrentes | Worker pool 10 workers + sharded locks | 400–600 por instancia |
| Broadcast latency | Parallel batch (Adaptive/Fixed strategy) | ~160ms para 400 usuarios |
| Redis operaciones | Connection pool singleton, Lua scripts atómicos | Miles ops/s |
| DB queries | Eager loading, índices, connection pooling | Prevención N+1 |
| Horizontal scaling | Múltiples WS Gateway instancias comparten Redis | Escala lineal |
| Resiliencia | Circuit breaker (5 fallos → open 30s) + retry con jitter | Auto-recovery |
