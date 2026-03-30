# CLAUDE.md

Guidance for Claude Code when working in this repository.
This project is being built **from scratch** using Spec-Driven Development (SDD).

---

## Project Overview

**Integrador** — sistema de gestión para restaurantes (monorepo).

| Component | Port | Description |
|-----------|------|-------------|
| **backend** | 8000 | FastAPI REST API (PostgreSQL, Redis, JWT) |
| **ws_gateway** | 8001 | WebSocket Gateway para eventos en tiempo real |
| **Dashboard** | 5177 | Panel de administración (React 19 + Zustand) |
| **pwaMenu** | 5176 | Menú para clientes PWA (i18n es/en/pt) |
| **pwaWaiter** | 5178 | PWA para mozos (offline-first) |

Contexto completo: ver `openspec/knowledge/` docs.

---

## Orchestrator — Agente Principal

**REGLA CRÍTICA**: El agente orquestador es el punto de entrada para TODAS las tareas, sin excepción.

- Todo prompt del usuario — con o sin comando `/sdd-*` — debe ser procesado primero por el orquestador
- El orquestador DELEGA trabajo a sub-agentes especializados; NUNCA ejecuta código inline
- Tareas pequeñas (fixes, preguntas) → orquestador delega a sub-agente general
- Tareas sustanciales (features, bugs complejos) → orquestador propone SDD o delega por dominio
- El orquestador es el ÚNICO que habla con el usuario; los sub-agentes devuelven resultados al orquestador

**Sin excepciones**: "es un fix chico" no justifica saltear el orquestador.

---

## SDD Workflow

Todo el desarrollo pasa por fases SDD. **No escribir código sin spec aprobada.**

### Knowledge Base (cargar antes de cualquier fase)
`openspec/knowledge/` contiene el contexto destilado del sistema:

| Doc | Contenido |
|-----|-----------|
| `00-roadmap.md` | 16 fases con dependencias y comandos |
| `01-vision-roles.md` | Visión, usuarios, RBAC |
| `02-arquitectura-stack.md` | Arquitectura, stack, puertos, ADRs |
| `03-modelo-datos.md` | Modelo de datos completo (54+ entidades) |
| `04-reglas-dominio.md` | Reglas de negocio, lifecycles |
| `05-seguridad.md` | Auth, JWT, Table Token, middlewares |
| `06-eventos-ws.md` | Catálogo de eventos WebSocket |
| `07-patrones-frontend.md` | React 19, Zustand, i18n, hooks |
| `08-patrones-backend.md` | FastAPI, Domain Services, Clean Architecture |
| `09-sprint-planning.md` | Sprint planning, dependencias, camino crítico, asignación devs |

### Roadmap — 16 fases
Ver `openspec/knowledge/00-roadmap.md` para el detalle completo (fuente de verdad).

| Phase | Nombre | Descripción |
|-------|--------|-------------|
| 1 | `foundation-infra` | Monorepo, Docker, PostgreSQL, Redis, modelos, Alembic, CI |
| 2 | `foundation-auth` | JWT, refresh tokens, RBAC Strategy, multi-tenant, rate limiting |
| 3 | `dashboard-shell` | React 19 + Vite + Zustand shell, auth flow, CRUD reutilizable |
| 4 | `menu-domain` | Alérgenos, perfiles dietéticos, precios por sucursal, API pública |
| 5 | `table-staff-domain` | Sectores, mesas FSM, CRUD staff, asignaciones waiter-sector |
| 6 | `pwa-menu-base` | QR sesión, navegación menú, filtrado alérgenos, i18n, PWA |
| 7 | `realtime-infra` | WS Gateway, auth JWT+HMAC, Redis Pub/Sub, carrito compartido |
| 8 | `order-domain` | Rondas FSM, KitchenTickets, Outbox, Redis Streams, vista cocina |
| 9 | `pwa-waiter` | Auth + gate sector, grilla mesas, comanda, offline, notificaciones |
| 10 | `billing-base` | ServiceCall FSM, Check, división cuenta, propinas |
| 11 | `payment-domain` | Pagos manuales, Mercado Pago, cierre mesa saldo cero |
| 12 | `realtime-resilience` | Circuit breaker, rate limiting Lua, backpressure, reconexión |
| 13 | `recipes-promotions` | Ingredientes, recetas, motor promociones, sección promos |
| 14 | `analytics-audit` | Dashboard estadísticas, exportación CSV, Kanban, auditoría |
| 15 | `pwa-polish` | Workbox, WCAG 2.1 AA, i18n completo, import/export, ayuda |
| 16 | `production-readiness` | CI/CD, Prometheus, logging, security headers, load testing |

### Comandos por fase
```bash
/sdd-new "foundation-infra"     # explore + propose automático
/sdd-ff "foundation-infra"      # spec + design + tasks fast-forward
/sdd-apply "foundation-infra"   # implementación en lotes
/sdd-verify "foundation-infra"  # validación
/sdd-archive "foundation-infra" # cierre
```

---

## Project Skills

Skills especializados en `.agent/skills/`. Se cargan automáticamente por contexto:

| Contexto | Skill |
|---------|-------|
| Crear página CRUD en Dashboard | `dashboard-crud-page` |
| Crear o modificar Zustand store | `zustand-store-pattern` |
| Crear formularios (cualquier frontend) | `react19-form-pattern` |
| Crear endpoint o service en backend | `fastapi-domain-service` |
| Agregar HelpButton a Dashboard | `help-system-content` |
| Conectar componente a WebSocket | `ws-frontend-subscription` |

### Jerarquía de Skills

**Regla**: Los skills de proyecto (`.agent/skills/`) tienen precedencia sobre los globales (`~/.claude/skills/`) cuando hay solapamiento funcional.

#### Skills con solapamiento (proyecto gana)

| Dominio | Proyecto (`.agent/skills/`) | Global (`~/.claude/skills/`) | Precedencia |
|---------|---------------------------|------------------------------|-------------|
| FastAPI / backend | `fastapi-domain-service`, `fastapi-code-review` | `fastapi-clean-arch` | Proyecto |
| Zustand / React | `zustand-store-pattern`, `react19-form-pattern` | `react19-zustand` | Proyecto |
| WebSocket frontend | `ws-frontend-subscription` | `websocket-gateway` | Proyecto |
| Redis | `redis-best-practices` | `redis-patterns` | Proyecto |
| PWA | `pwa-development` | `pwa-workbox` | Proyecto |
| Clean Architecture | `clean-architecture` | `fastapi-clean-arch` | Proyecto |

#### Skills exclusivos de proyecto

| Skill | Propósito |
|-------|-----------|
| `dashboard-crud-page` | Páginas CRUD del Dashboard |
| `help-system-content` | HelpButton contextual |
| `agile-product-owner` | Historias de usuario, sprint planning |
| `interface-design` | Diseño de interfaces (no marketing) |
| `vercel-react-best-practices` | Optimización React/Next.js |
| `websocket-engineer` | Sistemas real-time bidireccionales |

#### Skills exclusivos globales

| Skill | Propósito |
|-------|-----------|
| `sdd-*` (8 skills) | Fases del workflow SDD |
| `skill-creator` | Creación de nuevos skills |
| `skill-registry` | Registro centralizado de skills |
| `branch-pr`, `issue-creation` | Workflows GitHub |
| `jwt-auth-rbac` | Auth JWT y RBAC |
| `sqlalchemy-multitenant` | Modelos multi-tenant |
| `tailwind-dark-theme` | Sistema de diseño Tailwind |
| `go-testing` | Tests Go / Bubbletea (no aplica a este proyecto) |

---

## Convenciones

- **Idioma UI**: Español
- **Comentarios de código**: Inglés
- **Tema**: Naranja (#f97316) como accent
- **Precios**: Almacenados en centavos (12550 = $125.50)
- **IDs**: `crypto.randomUUID()` en frontend, BigInteger en backend
- **Frontend**: camelCase | **Backend**: snake_case
- **Logging**: Logger centralizado — nunca `console.*` ni `print()`

### Conversiones Frontend ↔ Backend
```typescript
// IDs: backend number → frontend string
const frontendId = String(backendId)
const backendId = parseInt(frontendId, 10)

// Precios: backend cents → frontend pesos
const display = backendCents / 100    // 12550 → 125.50
const toBackend = Math.round(price * 100)

// Status: backend UPPERCASE → frontend lowercase
```

---

## Reglas Críticas

### Backend
- **Routers THIN**: solo `Depends` + `PermissionContext` + llamada al service. Cero lógica.
- **CRUDFactory DEPRECADO** — usar Domain Services siempre
- Siempre `safe_commit(db)` — nunca `db.commit()` directo
- SQLAlchemy boolean: `.is_(True)` — nunca `== True`
- `with_for_update()` para operaciones de billing y rounds (race conditions)

### Frontend
- **NUNCA destructurar Zustand**: `const { items } = useStore()` causa infinite re-renders
- Siempre selectors: `const items = useStore(selectItems)`
- `useShallow` para arrays filtrados/computed desde el store
- React 19: `useActionState` para formularios (no useState + handlers)
- HelpButton **obligatorio** en todas las páginas de Dashboard

### WebSocket
- Patrón ref para suscripciones — previene acumulación de listeners
- Empty deps array en el effect de suscripción — suscribirse una sola vez
- pwaMenu: cero strings hardcodeados — todo via `t()`

---

## Governance

| Nivel | Dominios | Acción |
|-------|---------|--------|
| CRITICO | Auth, Billing, Allergens, Staff | Solo análisis — sin código de producción |
| ALTO | Products, WebSocket, Rate Limiting | Proponer + esperar revisión humana |
| MEDIO | Orders, Kitchen, Waiter, Tables, Customer | Implementar con checkpoints |
| BAJO | Categories, Sectors, Recipes, Ingredients | Autonomía total si pasan los tests |
