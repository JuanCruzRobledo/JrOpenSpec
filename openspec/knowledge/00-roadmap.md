# Roadmap de Implementación — 16 Fases
> Fuente de verdad para: planificación de implementación, dependencias entre fases

## Orden de implementación

### Capa de Fundación (Phases 1-2)
Base técnica completa antes de cualquier feature.

| Phase | Nombre | Descripción |
|-------|--------|-------------|
| 1 | foundation-infra | Monorepo, Docker Compose, PostgreSQL 16+pgvector, Redis 7, 52+ modelos SQLAlchemy por dominio, AuditMixin, TenantScoped repos, Alembic, health checks, seed data, CI base |
| 2 | foundation-auth | JWT access+refresh tokens, rotación + detección de reuso, Redis blacklist fail-closed, RBAC Strategy Pattern (5 roles), multi-tenant middleware, rate limiting, brute-force protection, HMAC table tokens |

### Capa de Dominio (Phases 3-8)
Primera capa de valor entregable.

| Phase | Nombre | Descripción |
|-------|--------|-------------|
| 3 | dashboard-shell | React 19 + Vite + Zustand shell, auth flow con refresh proactivo, sidebar + header + branch selector, patrón CRUD reutilizable (sucursales, categorías, subcategorías, productos) |
| 4 | menu-domain | Alérgenos EU 14 + custom + cross-reactions, perfiles dietéticos/sabor/textura, precios por sucursal, batch price update, badges/seals, API pública con cache Redis 5min |
| 5 | table-staff-domain | Sectores + mesas (FSM 6 estados, grilla visual, creación batch), CRUD de personal con RBAC, asignaciones waiter-sector por turno |
| 6 | pwa-menu-base | pwaMenu: QR→sesión (HMAC 3h), navegación menú 3 niveles, filtrado alérgenos (3 modos strictness), i18n es/en/pt, PWA + Workbox, offline fallback |
| 7 | realtime-infra | WebSocket Gateway (:8001, 4 endpoints por rol), auth JWT+HMAC, connection manager (sharded locks, 1000 conn max), Redis Pub/Sub channels, carrito compartido con optimistic updates |
| 8 | order-domain | Rondas (FSM 6 estados + protocolo de confirmación grupal 5min), KitchenTickets por estación (FSM 4 estados), Outbox pattern, Redis Streams + consumer groups + DLQ, broadcast pool (10 workers, 5k queue), vista cocina + admin Kanban |

### Capa de Aplicación (Phases 9-12)

| Phase | Nombre | Descripción |
|-------|--------|-------------|
| 9 | pwa-waiter | pwaWaiter completo: auth + gate de sector, grilla de mesas (WS + 60s polling fallback), comanda rápida (split-panel), offline (IndexedDB + retry queue), notificaciones browser, 5 niveles de animación, PWA manifest |
| 10 | billing-base | ServiceCall (FSM ACTIVA→RECONOCIDA→CERRADA + outbox), UIs en pwaMenu/pwaWaiter, generación de Check (idempotente), vista factura itemizada, división de cuenta (3 métodos), propinas con distribución proporcional |
| 11 | payment-domain | Pagos manuales (SELECT FOR UPDATE + FIFO allocation), integración Mercado Pago (preference + webhooks + circuit breaker 5-fail/30s), flujo de pago pwaMenu, cierre y liberación de mesa con verificación saldo cero |
| 12 | realtime-resilience | Circuit breaker Redis (CLOSED→OPEN→SEMI_OPEN), rate limiting Lua sliding window (20 msg/s), backpressure queues (5k cap), reconexión exponencial pwaMenu/pwaWaiter (50 intentos), graceful shutdown, BroadcastChannel Dashboard, métricas Prometheus |

### Capa Avanzada (Phases 13-16)
Diferenciadores competitivos post-MVP.

| Phase | Nombre | Descripción |
|-------|--------|-------------|
| 13 | recipes-promotions | Catálogo de ingredientes (grupos/sub-ingredientes), fichas técnicas de recetas (tiempos, costo, alérgenos, sensorial), motor de promociones (4 tipos predefinidos + custom, reglas temporales, multi-sucursal), sección promos en pwaMenu |
| 14 | analytics-audit | Dashboard de estadísticas de ventas (5 cards, Chart.js, top 10 productos), exportación CSV, Kanban órdenes admin (real-time), auditoría (snapshots JSONB before/after, restauración soft-deletes) |
| 15 | pwa-polish | Workbox por PWA (estrategias diferenciadas), WCAG 2.1 AA en los 3 PWAs, i18n completo pwaMenu (todo via `t()`), import/export JSON en Dashboard, botón de ayuda contextual, refinamiento toasts, animaciones de producción |
| 16 | production-readiness | GitHub Actions CI/CD (lint/test/build/staging auto/prod con approval gate), Prometheus instrumentation, logging JSON estructurado, security headers (CSP/HSTS/XFO/XCTO), protección SSRF, auditoría de seguridad, load testing k6 (400-600 users), runbook operacional |

## Dependencias

```
Phase 1 (foundation-infra)
  └─→ Phase 2 (foundation-auth)
        ├─→ Phase 3 (dashboard-shell)
        │     └─→ Phase 4 (menu-domain)
        │           ├─→ Phase 5 (table-staff-domain)  [paralelo con Phase 6]
        │           ├─→ Phase 6 (pwa-menu-base)
        │           │     └─→ Phase 7 (realtime-infra)
        │           │           └─→ Phase 8 (order-domain)
        │           │                 ├─→ Phase 9 (pwa-waiter)
        │           │                 │     └─→ Phase 10 (billing-base)
        │           │                 │           └─→ Phase 11 (payment-domain)
        │           │                 └─→ Phase 12 (realtime-resilience) [necesita 7, 8, 9]
        │           └─→ Phase 13 (recipes-promotions) [puede correr desde Phase 4]
        └─→ Phase 14 (analytics-audit) [necesita 1-12]

Phase 15 (pwa-polish) [necesita 6, 8, 9]
Phase 16 (production-readiness) [necesita todo]
```

## Comandos por fase

```bash
/sdd-new "foundation-infra"       # → explore + propose automático
/sdd-ff "foundation-infra"        # → spec + design + tasks fast-forward
/sdd-apply "foundation-infra"     # → implementación en lotes
/sdd-verify "foundation-infra"    # → validación
/sdd-archive "foundation-infra"   # → cierre
```

## Knowledge base por fase

| Phase | Nombre | Knowledge docs relevantes |
|-------|--------|--------------------------|
| 1 | foundation-infra | 02 (arquitectura-stack), 03 (modelo-datos) |
| 2 | foundation-auth | 01 (vision-roles), 02, 05 (seguridad) |
| 3 | dashboard-shell | 01, 02, 07 (patrones-frontend) |
| 4 | menu-domain | 03, 04 (reglas-dominio), 08 (patrones-backend) |
| 5 | table-staff-domain | 01, 03, 04, 08 |
| 6 | pwa-menu-base | 01, 04, 06 (eventos-ws), 07 |
| 7 | realtime-infra | 02, 06, 08 |
| 8 | order-domain | 03, 04, 06, 08 |
| 9 | pwa-waiter | 01, 04, 05 (seguridad), 06, 07 |
| 10 | billing-base | 03, 04, 06, 07, 08 |
| 11 | payment-domain | 03, 04, 05, 08 |
| 12 | realtime-resilience | 02, 06, 08 |
| 13 | recipes-promotions | 03, 04, 08 |
| 14 | analytics-audit | 01, 03, 04, 08 |
| 15 | pwa-polish | 01, 06, 07 |
| 16 | production-readiness | 02, 05, 08 |

## Instrucción para sdd-explore de cada fase

Cada explore debe incluir:
```
Leé los siguientes docs de knowledge base antes de explorar:
- openspec/knowledge/01-vision-roles.md
- openspec/knowledge/02-arquitectura-stack.md
- openspec/knowledge/03-modelo-datos.md
- openspec/knowledge/04-reglas-dominio.md
- [los específicos del dominio según tabla anterior]
```
