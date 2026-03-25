# Sprint Planning — Integrador

> Fuente de verdad para: planificación de sprints, asignación de desarrolladores, camino crítico
> Complementa: `00-roadmap.md` (fases y dependencias), `openspec/changes/*/state.yaml` (estado actual)

---

## a) Grafo de Dependencias

```
Phase 1 (foundation-infra)
  |
  v
Phase 2 (foundation-auth)
  |
  ├──────────────────────────────────────────────────┐
  v                                                  |
Phase 3 (dashboard-shell)                            |
  |                                                  |
  v                                                  |
Phase 4 (menu-domain)                                |
  |                                                  |
  ├──────────────┬──────────────┐                    |
  v              v              v                    |
Phase 5        Phase 6       Phase 13                |
(table-staff)  (pwa-menu)    (recipes-promotions)    |
               |              [independiente         |
               v               desde Phase 4]        |
             Phase 7                                 |
             (realtime-infra)                        |
               |                                     |
               v                                     |
             Phase 8                                 |
             (order-domain)                          |
               |                                     |
               ├──────────────┐                      |
               v              v                      |
             Phase 9        Phase 12                 |
             (pwa-waiter)   (realtime-resilience)    |
               |            [necesita 7, 8, 9]       |
               v                                     |
             Phase 10                                |
             (billing-base)                          |
               |                                     |
               v                                     |
             Phase 11                                |
             (payment-domain)                        |
                                                     |
             Phase 14 (analytics-audit) <────────────┘
             [necesita Phases 1-12]

Phase 15 (pwa-polish)          [necesita 6, 8, 9]
Phase 16 (production-readiness) [necesita TODAS las fases]
```

### Leyenda de dependencias directas

| Phase | Depende de |
|-------|------------|
| 1 `foundation-infra` | Ninguna |
| 2 `foundation-auth` | 1 |
| 3 `dashboard-shell` | 2 |
| 4 `menu-domain` | 3 |
| 5 `table-staff-domain` | 4 |
| 6 `pwa-menu-base` | 4 |
| 7 `realtime-infra` | 6 |
| 8 `order-domain` | 7 |
| 9 `pwa-waiter` | 8 |
| 10 `billing-base` | 9 |
| 11 `payment-domain` | 10 |
| 12 `realtime-resilience` | 7, 8, 9 |
| 13 `recipes-promotions` | 4 |
| 14 `analytics-audit` | 1-12 (todas las fases core) |
| 15 `pwa-polish` | 6, 8, 9 |
| 16 `production-readiness` | Todas |

---

## b) Mapa de Sprints

### Sprint 1 — Fundación
**Prerequisitos**: Ninguno (arranque del proyecto)

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 1 | `foundation-infra` | 37 secciones | CRITICO | No — es la base de todo |

**Foco**: Monorepo, Docker Compose, PostgreSQL + pgvector, Redis, modelos SQLAlchemy, Alembic, seed data.

---

### Sprint 2 — Auth + Seguridad
**Prerequisitos**: Sprint 1 completado

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 2 | `foundation-auth` | 31 secciones | CRITICO | No — bloquea todo lo demás |

**Foco**: JWT, refresh tokens, RBAC Strategy Pattern, multi-tenant middleware, rate limiting, HMAC table tokens.

---

### Sprint 3 — Dashboard + Menú
**Prerequisitos**: Sprint 2 completado

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 3 | `dashboard-shell` | 45 secciones | MEDIO | Secuencial (3 antes de 4, Phase 4 es CRITICO) |
| 4 | `menu-domain` | 58 secciones | CRITICO | Secuencial (4 después de 3) |

**Foco**: Shell del Dashboard con auth flow, patrón CRUD reutilizable. Luego dominio de menú completo con alérgenos y precios por sucursal.

**Gobernanza CRITICO (Phase 4)**: Incluye Allergens (salud/seguridad — 14 alérgenos EU + reacciones cruzadas). Requiere solo análisis — sin código de producción autónomo.

---

### Sprint 4 — Dominio Operativo (PARALELO)
**Prerequisitos**: Sprint 3 completado (Phase 4 terminada)

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 5 | `table-staff-domain` | 72 secciones | CRITICO | SI — Dev A |
| 6 | `pwa-menu-base` | 67 secciones | MEDIO | SI — Dev B |
| 13 | `recipes-promotions` | 24 secciones | BAJO | SI — Dev C |

**Oportunidad de paralelismo**: Las 3 fases dependen solo de Phase 4 y NO entre sí. Pueden asignarse a 3 desarrolladores distintos trabajando en simultáneo.

**Gobernanza CRITICO (Phase 5)**: Incluye Staff (seguridad — RBAC, permisos, asignaciones waiter-sector). Requiere solo análisis — sin código de producción autónomo.

---

### Sprint 5 — Real-Time
**Prerequisitos**: Sprint 4, Phase 6 (`pwa-menu-base`) completada

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 7 | `realtime-infra` | 45 secciones | ALTO | No — bloquea orders y resiliencia |

**Foco**: WS Gateway completo, auth JWT+HMAC, connection manager, Redis Pub/Sub, carrito compartido.

---

### Sprint 6 — Pedidos
**Prerequisitos**: Sprint 5 completado

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 8 | `order-domain` | 58 secciones | MEDIO | No — bloquea pwa-waiter y billing |

**Foco**: Rondas FSM, KitchenTickets, Outbox pattern, Redis Streams + consumer groups, vista cocina Kanban.

---

### Sprint 7 — Apps de Campo (PARALELO)
**Prerequisitos**: Sprint 6 completado

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 9 | `pwa-waiter` | 37 secciones | MEDIO | SI — Dev A (frontend) |
| 12 | `realtime-resilience` | 29 secciones | ALTO | SI — Dev B (backend/infra) |

**Oportunidad de paralelismo**: `pwa-waiter` es frontend puro, `realtime-resilience` es backend/infra. Pueden trabajarse en paralelo por devs con distintas especialidades.

**Nota**: Phase 12 necesita 7, 8 y 9. Sin embargo, el grueso de 12 (circuit breaker, rate limiting, backpressure) puede desarrollarse contra 7+8 mientras 9 está en progreso, con integración final al cerrar el sprint.

---

### Sprint 8 — Facturación + Pagos (SECUENCIAL)
**Prerequisitos**: Sprint 7, Phase 9 completada

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 10 | `billing-base` | 23 secciones | CRITICO | Secuencial (10 antes de 11) |
| 11 | `payment-domain` | 24 secciones | CRITICO | Secuencial (11 después de 10) |

**Foco**: ServiceCall FSM, Check idempotente, división de cuenta, propinas. Luego pagos manuales, Mercado Pago, cierre de mesa.

**Gobernanza CRITICO**: Requiere revisión humana exhaustiva. Solo análisis y propuestas, sin código de producción autónomo.

---

### Sprint 9 — Analíticas + Auditoría
**Prerequisitos**: Sprints 1-8 completados (Phases 1-12)

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 14 | `analytics-audit` | 23 secciones | MEDIO | SI — puede correr con Sprint 10 |

**Foco**: Dashboard estadísticas de ventas, exportación CSV, Kanban órdenes, auditoría con snapshots JSONB.

---

### Sprint 10 — Pulido PWA
**Prerequisitos**: Phases 6, 8, 9 completadas

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 15 | `pwa-polish` | 25 secciones | BAJO | SI — puede correr con Sprint 9 |

**Oportunidad de paralelismo con Sprint 9**: `analytics-audit` es backend/Dashboard, `pwa-polish` es PWAs. Devs distintos pueden trabajar ambos en simultáneo.

---

### Sprint 11 — Producción
**Prerequisitos**: TODAS las fases anteriores completadas

| Phase | Directorio | Complejidad (headers) | Gobernanza | Paralelizable |
|-------|-----------|----------------------|------------|---------------|
| 16 | `production-readiness` | 25 secciones | ALTO | No — cierre del proyecto |

**Foco**: CI/CD, Prometheus, logging estructurado, security headers, load testing k6, runbook operacional.

---

## c) Guía de Asignación de Desarrolladores

### Modelo mínimo: 2 desarrolladores

| Dev | Perfil | Fases asignadas |
|-----|--------|-----------------|
| **Dev Backend** | Python, FastAPI, SQLAlchemy, Redis | 1, 2, 4 (backend), 5 (backend), 7, 8, 10, 11, 12, 14, 16 |
| **Dev Frontend** | React 19, Zustand, PWA, TypeScript | 3, 4 (frontend), 5 (frontend), 6, 9, 13, 15 |

### Modelo óptimo: 3 desarrolladores

| Dev | Perfil | Fases asignadas |
|-----|--------|-----------------|
| **Dev Backend** | Python, FastAPI, DB, Redis | 1, 2, 7, 8 (backend), 10, 11, 12, 16 |
| **Dev Frontend** | React 19, Zustand, PWA | 3, 6, 9, 13, 15 |
| **Dev Fullstack** | Ambos perfiles | 4, 5, 8 (frontend), 14 |

### Ventanas de paralelismo (oportunidades clave)

| Sprint | Fases paralelas | Devs necesarios | Ahorro estimado |
|--------|----------------|-----------------|-----------------|
| Sprint 4 | 5 + 6 + 13 | 2-3 | ~40% del sprint |
| Sprint 7 | 9 + 12 | 2 | ~30% del sprint |
| Sprint 9+10 | 14 + 15 | 2 | ~50% (corren juntos) |

### Fases que BLOQUEAN a otras (no paralelizables)

| Phase | Bloquea | Impacto |
|-------|---------|---------|
| 1 `foundation-infra` | TODO el proyecto | Critico |
| 2 `foundation-auth` | TODO excepto Phase 1 | Critico |
| 3 `dashboard-shell` | Phase 4 y cascada | Alto |
| 4 `menu-domain` | Phases 5, 6, 13 | Alto |
| 7 `realtime-infra` | Phases 8, 12 | Alto |
| 8 `order-domain` | Phases 9, 10, 11, 12, 15 | Muy Alto |

---

## d) Camino Crítico

La cadena más larga de dependencias secuenciales determina la duración mínima del proyecto:

```
1 → 2 → 3 → 4 → 6 → 7 → 8 → 9 → 10 → 11
```

**10 fases en serie** = duración mínima del proyecto.

| # | Phase | Nombre |
|---|-------|--------|
| 1 | 1 | `foundation-infra` |
| 2 | 2 | `foundation-auth` |
| 3 | 3 | `dashboard-shell` |
| 4 | 4 | `menu-domain` |
| 5 | 6 | `pwa-menu-base` |
| 6 | 7 | `realtime-infra` |
| 7 | 8 | `order-domain` |
| 8 | 9 | `pwa-waiter` |
| 9 | 10 | `billing-base` |
| 10 | 11 | `payment-domain` |

**Fases fuera del camino crítico** (pueden absorber retrasos sin afectar la fecha final):
- Phase 5 (`table-staff-domain`) — paralela a 6
- Phase 12 (`realtime-resilience`) — paralela a 9
- Phase 13 (`recipes-promotions`) — paralela a 5+6
- Phase 14 (`analytics-audit`) — después del core, paralela a 15
- Phase 15 (`pwa-polish`) — paralela a 14
- Phase 16 (`production-readiness`) — solo al final

---

## e) Dashboard de Estado

> Actualizado desde `openspec/changes/*/state.yaml` — 2026-03-25

| Phase | Nombre | Directorio | Estado | Artefactos SDD | Próxima acción |
|-------|--------|-----------|--------|---------------|----------------|
| 1 | foundation-infra | `openspec/changes/foundation-infra/` | ready-for-implementation | proposal, spec, design, tasks: DONE | `/sdd-apply "foundation-infra"` |
| 2 | foundation-auth | `openspec/changes/foundation-auth/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 1 |
| 3 | dashboard-shell | `openspec/changes/dashboard-shell/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 2 |
| 4 | menu-domain | `openspec/changes/menu-domain/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 3 |
| 5 | table-staff-domain | `openspec/changes/table-staff-domain/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 4 |
| 6 | pwa-menu-base | `openspec/changes/pwa-menu-base/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 4 |
| 7 | realtime-infra | `openspec/changes/realtime-infra/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 6 |
| 8 | order-domain | `openspec/changes/order-domain/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 7 |
| 9 | pwa-waiter | `openspec/changes/pwa-waiter/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 8 |
| 10 | billing-base | `openspec/changes/billing-base/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 9 |
| 11 | payment-domain | `openspec/changes/payment-domain/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 10 |
| 12 | realtime-resilience | `openspec/changes/realtime-resilience/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phases 7, 8, 9 |
| 13 | recipes-promotions | `openspec/changes/recipes-promotions/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phase 4 |
| 14 | analytics-audit | `openspec/changes/analytics-audit/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phases 1-12 |
| 15 | pwa-polish | `openspec/changes/pwa-polish/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar Phases 6, 8, 9 |
| 16 | production-readiness | `openspec/changes/production-readiness/` | ready-for-implementation | proposal, spec, design, tasks: DONE | Esperar TODAS |

**Resumen**: Las 16 fases tienen todos los artefactos SDD completos (proposal, spec, design, tasks). Ninguna fase ha comenzado implementación (`apply: pending` en todas). La primera acción es `/sdd-apply "foundation-infra"`.
