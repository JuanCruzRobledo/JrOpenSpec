# Roadmap de Implementación — 11 Fases
> Fuente de verdad para: planificación de implementación, dependencias entre fases

## Orden de implementación

### Backend First (Phases 1-7)
Ningún frontend puede existir sin API.

| Phase | Nombre | Descripción |
|-------|--------|-------------|
| 1 | foundation-auth | JWT, refresh tokens, User, UserBranchRole, RBAC |
| 2 | tenant-branch-core | Tenant, Branch, multi-tenant structure |
| 3 | menu-domain | Category → Subcategory → Product → Allergen → Ingredient |
| 4 | table-session-domain | BranchSector → Table → TableSession → Diner → ServiceCall |
| 5 | order-domain | Round → RoundItem → KitchenTicket (full lifecycle) |
| 6 | billing-domain | Check → Charge → Payment → Allocation (FIFO) |
| 7 | realtime-infra | WS Gateway + Outbox pattern + Redis Streams |

### Frontend (Phases 8-10)
Dependen de phases 1-7 completadas.

| Phase | Nombre | Descripción |
|-------|--------|-------------|
| 8 | pwa-waiter | pwaWaiter completo (pre-login flow, offline-first) |
| 9 | pwa-menu | pwaMenu (i18n, collaborative cart, payment) |
| 10 | dashboard | Dashboard Admin (todas las secciones CRUD) |

### Features Avanzadas (Phase 11)
Depende de todo lo anterior.

| Phase | Nombre | Descripción |
|-------|--------|-------------|
| 11 | advanced-features | Customer loyalty, recipes, promotions, statistics |

## Dependencias

```
Phase 1 (auth) → Phase 2 (tenant/branch) → Phase 3 (menu)
                                          → Phase 4 (tables) → Phase 5 (orders) → Phase 6 (billing)
Phase 7 (realtime) puede correr en paralelo con Phase 6
Phases 8-10 dependen de Phases 1-7
Phase 11 depende de todo
```

## Comandos por fase

```bash
/sdd-new "foundation-auth"     # → explore + propose automático
/sdd-ff "foundation-auth"      # → spec + design + tasks fast-forward
/sdd-apply "foundation-auth"   # → implementación en lotes
/sdd-verify "foundation-auth"  # → validación
/sdd-archive "foundation-auth" # → cierre
```

## Instrucción para sdd-explore de cada fase

Cada explore debe incluir:
```
Leé los siguientes docs de knowledge base antes de explorar:
- openspec/knowledge/01-vision-roles.md
- openspec/knowledge/02-arquitectura-stack.md
- openspec/knowledge/03-modelo-datos.md
- openspec/knowledge/04-reglas-dominio.md
- [los específicos del dominio]
```

## Knowledge base por fase

| Phase | Knowledge docs relevantes |
|-------|--------------------------|
| foundation-auth | 01, 02, 05 (seguridad) |
| tenant-branch-core | 01, 02, 03 |
| menu-domain | 03, 04, 08 (patrones backend) |
| table-session-domain | 03, 04, 06 (WS events) |
| order-domain | 03, 04, 06, 08 |
| billing-domain | 03, 04, 08 |
| realtime-infra | 06, 02 |
| pwa-waiter | 01, 04, 05, 06, 07 (patrones frontend) |
| pwa-menu | 01, 04, 06, 07 |
| dashboard | 01, 04, 07, 08 |
| advanced-features | todos |
