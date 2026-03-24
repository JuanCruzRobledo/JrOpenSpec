---
sprint: 10
artifact: proposal
status: complete
---

# Proposal: Llamados de Servicio y Facturacin Base

## Intent

Implement a full service call system enabling diners to request waiter attention with typed calls (recharge, check, complaint, other) and build the billing foundation allowing diners to request their check with itemized detail and tip/splitting options.

## Scope

### In Scope
- Backend ServiceCall entity with state machine (ACTIVA → RECONOCIDA → CERRADA)
- Service call CRUD with sector filtering and audit trail
- Outbox event SERVICE_CALL_CREATED for real-time propagation
- pwaMenu: call waiter button with type selector and visual feedback
- pwaWaiter: real-time service call reception with Priority 1 animation, sound, notification
- Deduplication buffer (100 IDs) in pwaWaiter for duplicate WebSocket messages
- Check/bill generation: POST /api/sessions/{id}/check (idempotent)
- Check entity totalizing all rounds into a single bill
- Table state transition to PAGO on check request
- Outbox event CHECK_REQUESTED
- pwaMenu: request check button with itemized view (items per round, subtotals, total)
- Bill splitting: equal division, by consumption, custom assignment
- Tip presets (0%, 10%, 15%, 20%) with proportional distribution across split charges

### Out of Scope
- Payment processing (Sprint 11)
- Mercado Pago integration (Sprint 11)
- Table close/release flow (Sprint 11)
- Receipt generation / fiscal invoicing

## Modules

| Module | Description |
|--------|-------------|
| `service-calls-backend` | ServiceCall model, endpoints, state machine, outbox |
| `service-calls-pwamenu` | Diner-facing call waiter UI |
| `service-calls-pwawaiter` | Waiter-facing call reception and management |
| `billing-backend` | Check model, generation endpoint, totalization |
| `billing-pwamenu` | Check request UI, itemized view, split/tip |

## Approach

1. **Backend ServiceCall** entity + state machine + sector-filtered queries + outbox integration
2. **pwaMenu call UI** — button, type selector modal, status feedback
3. **pwaWaiter call reception** — WebSocket handler, dedup buffer, Priority 1 animation trigger, notification
4. **pwaWaiter call management** — acknowledge and close actions in table detail modal
5. **Backend Check** entity + idempotent generation endpoint + round totalization
6. **pwaMenu check request** — button, itemized round-by-round view, subtotals
7. **pwaMenu splitting** — three split methods + tip with presets and proportional distribution

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Duplicate WebSocket messages causing multiple alerts | High — annoying UX | 100-ID dedup ring buffer in pwaWaiter |
| Idempotency issues on check generation (double-tap) | Medium — duplicate checks | Idempotent endpoint: return existing check if session already has one |
| Tip calculation rounding errors on uneven splits | Low — financial discrepancy | Round to 2 decimals, assign remainder to last charge |
| Outbox event delivery delay | Medium — stale waiter view | WebSocket delivers event directly; outbox is for external consumers |
| Complex split UI confusing diners | Medium — abandoned flow | Default to equal split, progressive disclosure for advanced options |

## Rollback

- ServiceCall is a new entity — rollback by dropping table and removing endpoints
- Check generation is additive — no existing data affected
- pwaMenu/pwaWaiter changes are frontend-only, rollback by redeploying previous container
- Outbox events are append-only; old consumers ignore unknown event types
