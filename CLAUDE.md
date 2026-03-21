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

## SDD Workflow

Todo el desarrollo pasa por fases SDD. **No escribir código sin spec aprobada.**

### Knowledge Base (cargar antes de cualquier fase)
`openspec/knowledge/` contiene el contexto destilado del sistema:

| Doc | Contenido |
|-----|-----------|
| `00-roadmap.md` | 11 fases con dependencias y comandos |
| `01-vision-roles.md` | Visión, usuarios, RBAC |
| `02-arquitectura-stack.md` | Arquitectura, stack, puertos, ADRs |
| `03-modelo-datos.md` | Modelo de datos completo (54+ entidades) |
| `04-reglas-dominio.md` | Reglas de negocio, lifecycles |
| `05-seguridad.md` | Auth, JWT, Table Token, middlewares |
| `06-eventos-ws.md` | Catálogo de eventos WebSocket |
| `07-patrones-frontend.md` | React 19, Zustand, i18n, hooks |
| `08-patrones-backend.md` | FastAPI, Domain Services, Clean Architecture |

### Roadmap — 11 fases
Ver `openspec/knowledge/00-roadmap.md` para el detalle completo.

```
Phase 1:  foundation-auth           (JWT, User, RBAC)
Phase 2:  tenant-branch-core        (Tenant, Branch, multi-tenant)
Phase 3:  menu-domain               (Category → Product → Allergen)
Phase 4:  table-session-domain      (Sector → Table → Session → Diner)
Phase 5:  order-domain              (Round → RoundItem → KitchenTicket)
Phase 6:  billing-domain            (Check → Payment → Allocation FIFO)
Phase 7:  realtime-infra            (WS Gateway + Outbox + Redis Streams)
Phase 8:  pwa-waiter                (pwaWaiter completo)
Phase 9:  pwa-menu                  (pwaMenu con i18n y carrito colaborativo)
Phase 10: dashboard                 (Dashboard Admin — todas las secciones)
Phase 11: advanced-features         (Customer loyalty, recipes, promotions)
```

### Comandos por fase
```bash
/sdd-new "foundation-auth"     # explore + propose automático
/sdd-ff "foundation-auth"      # spec + design + tasks fast-forward
/sdd-apply "foundation-auth"   # implementación en lotes
/sdd-verify "foundation-auth"  # validación
/sdd-archive "foundation-auth" # cierre
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
