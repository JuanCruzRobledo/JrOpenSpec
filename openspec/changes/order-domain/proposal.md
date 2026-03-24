---
sprint: 8
artifact: proposal
status: complete
---

# SDD Proposal — Sprint 8: Rondas, Cocina y Outbox

## Status: APPROVED

## Executive Summary

Sprint 8 delivers the complete order lifecycle for "Buen Sabor": from group confirmation in pwaMenu through kitchen preparation to serving. It implements the Round confirmation voting protocol (5-min timer, quorum requirement, auto-send), a 6-state Round state machine with role-gated transitions, KitchenTicket fragmentation by station with auto-consolidation, the Outbox pattern for guaranteed event delivery, Redis Streams for reliable pub/sub with consumer groups, a broadcast worker pool (10 workers, 5k queue, ~160ms for 400 users), granular WebSocket event routing by role/scope, and kitchen + admin dashboard views.

This sprint bridges the gap between "ordering" and "serving" -- the core value loop of the restaurant.

## 1. Intent

Implement the full order flow from diner group confirmation through kitchen preparation to service delivery, with guaranteed event delivery (outbox pattern), reliable real-time broadcasting (Redis Streams + WebSocket), and purpose-built kitchen and admin dashboard views.

### Key Goals
1. **Group ordering**: Diners in a table session collaboratively build rounds, vote to confirm, and auto-submit after consensus
2. **Kitchen workflow**: Rounds are fragmented into station-specific tickets, with time tracking and priority display
3. **Guaranteed delivery**: Outbox pattern ensures no event is lost between DB commit and message broker
4. **Real-time updates**: Redis Streams with consumer groups, DLQ for failed messages, and a worker pool for WebSocket broadcast
5. **Role-based routing**: Events reach only the relevant users (admin sees all, waiter sees their sector, kitchen sees their station, diners see their table)

## 2. Scope

### In Scope
- **pwaMenu**: RoundConfirmationPanel (voting UI), timer 5min, auto-send 1.5s after last confirm, proponent cancel, sound notifications
- **Backend Round lifecycle**: Price capture on submit, PENDIENTE state, RoundItems with quantities/notes
- **6-state Round machine**: PENDIENTE -> CONFIRMADO -> ENVIADO -> EN_COCINA -> LISTO -> SERVIDO with role-gated transitions
- **KitchenTicket system**: Round fragmentation by station, 4-state ticket machine (PENDIENTE -> EN_PROGRESO -> LISTO -> ENTREGADO), auto-consolidation of Round state from ticket states
- **Kitchen Dashboard** (dashboard app): 2-column layout (new orders / in-progress), card UI with table, qty, elapsed time, >15min red border, detail modal with advance button
- **Admin Orders View** (dashboard app): 4 summary cards, 3-column Kanban + grid with filters
- **Outbox pattern**: `outbox_events` table, atomic write with business data, background processor (PENDING -> PROCESSING -> PUBLISHED), retry policy
- **Redis Streams**: Consumer groups per service, 3 retries then DLQ, reclaim pending >30s
- **Broadcast pool**: 10 workers, 5k message queue, target ~160ms for 400 concurrent users
- **Event routing matrix**: Granular routing by event type, role, and scope (all/sector/table)
- **Sound notifications**: pwaMenu audio alerts for round state changes

### Out of Scope
- Payment processing (Sprint 9+)
- Check splitting and billing (Sprint 9+)
- Waiter PWA (Sprint 10+)
- Recipe/ingredient deduction on kitchen completion
- Analytics and reporting on kitchen times
- Push notifications (web push API) -- only WebSocket + audio
- Horizontal scaling of WebSocket gateway (single instance for MVP)

## 3. Affected Modules

| Module | Impact | Description |
|--------|--------|-------------|
| `shared/models/orders/` | **MODIFY** | Expand Round, RoundItem, KitchenTicket models from Sprint 1 stubs |
| `shared/models/` | **NEW** | Add OutboxEvent model |
| `shared/enums.py` | **MODIFY** | Add RoundStatus, KitchenTicketStatus, OutboxEventStatus, OutboxEventType enums |
| `rest_api/app/routers/` | **NEW** | rounds.py, kitchen.py routers |
| `rest_api/app/services/` | **NEW** | round_service.py, kitchen_service.py, outbox_service.py |
| `rest_api/app/repositories/` | **NEW** | round_repo.py, kitchen_ticket_repo.py, outbox_repo.py |
| `ws_gateway/` | **MAJOR** | Full implementation: connection manager, Redis Streams consumer, broadcast pool, event router |
| `pwa_menu/` | **MODIFY** | RoundConfirmationPanel, voting logic, sound notifications, WebSocket integration |
| `dashboard/` | **MODIFY** | Kitchen dashboard view, admin orders Kanban view |
| `alembic/versions/` | **NEW** | Migration for outbox_events table, Round/RoundItem/KitchenTicket column additions |

## 4. Approach

### 4.1 Round Confirmation Protocol (pwaMenu)
The proponent (diner who initiates the round) triggers a confirmation vote. All diners in the table session see a RoundConfirmationPanel with each diner's vote status. A 5-minute timer starts -- if quorum (all diners) isn't reached, the round auto-cancels. Once all diners vote YES, a 1.5-second countdown starts before auto-submission (giving time for last-second changes). The proponent can cancel the entire round at any point before submission.

### 4.2 Round State Machine
Six states with explicit role guards per transition:
- PENDIENTE: Created when diners submit. Prices captured from branch_products at this moment.
- CONFIRMADO: Waiter acknowledges the round (role: waiter)
- ENVIADO: Admin/manager sends to kitchen (role: admin, manager)
- EN_COCINA: At least one KitchenTicket moves to EN_PROGRESO (automatic)
- LISTO: All KitchenTickets for this round reach LISTO (automatic consolidation)
- SERVIDO: Waiter marks as delivered to table (role: waiter)
- Cancellation: Allowed before SERVIDO by admin/manager only.

### 4.3 KitchenTicket Fragmentation
When a round enters ENVIADO, it's fragmented into KitchenTickets grouped by kitchen station (derived from product.station or category.default_station). Each ticket contains the items for that station. Ticket states auto-consolidate into Round state: if ANY ticket is EN_PROGRESO -> Round is EN_COCINA; when ALL tickets are LISTO -> Round is LISTO.

### 4.4 Outbox Pattern
Business operations (round state transitions, kitchen ticket updates) write an OutboxEvent row in the SAME transaction as the business data change. A background asyncio task polls for PENDING events, moves them to PROCESSING, publishes to Redis Streams, then marks PUBLISHED. If publish fails 3 times -> DLQ status. This guarantees at-least-once delivery without distributed transactions.

### 4.5 Redis Streams + Broadcast
Redis Streams with consumer groups per service (ws-gateway-group, kitchen-display-group, etc.). Messages claimed by a consumer must be ACKed within 30s or they're reclaimed by another consumer. After 3 delivery attempts -> DLQ stream. The WS Gateway has a broadcast worker pool: 10 goroutine-style asyncio workers consuming from an internal asyncio.Queue (capacity 5k). Each worker resolves target WebSocket connections from the event routing matrix and sends the payload. Target: ~160ms p95 for 400 concurrent users.

### 4.6 Event Routing Matrix
Each event type has a routing rule defining who receives it:
- ROUND_PENDING -> admin + all mozos (broadcast to all waiters in branch)
- ROUND_CONFIRMED -> admin + sector mozos (only waiters assigned to that table's sector)
- ROUND_SUBMITTED/EN_COCINA/LISTO -> admin + kitchen + sector mozos + diners at table
- KITCHEN_TICKET_* -> admin + kitchen station workers
- Sound notifications triggered client-side based on event type relevance to the user's role.

### 4.7 Kitchen Dashboard
Two-column layout in the dashboard app:
- Column 1 "Nuevos": Tickets in PENDIENTE state, sorted by creation time
- Column 2 "En Preparacion": Tickets in EN_PROGRESO, sorted by elapsed time (oldest first)
- Each card shows: table number, quantity of items, elapsed time badge
- Cards with >15min elapsed time get a red border (urgency indicator)
- Click on card opens modal with full ticket detail (items, quantities, notes) and an "Avanzar" button to move to next state

### 4.8 Admin Orders View
- 4 summary cards at top: Pendientes, En Cocina, Listos, Total Hoy (with counts)
- 3-column Kanban: Pendientes | En Cocina | Listos
- Below Kanban: Grid/table view with all rounds, filterable by status, date range, table, waiter
- Each Kanban card shows: round #, table, items count, elapsed time, waiter name

## 5. Dependencies on Previous Sprints

| Dependency | Sprint | Status |
|-----------|--------|--------|
| Table, Sector, TableSession, Diner models | Sprint 1 | Defined |
| Round, RoundItem, KitchenTicket model stubs | Sprint 1 | Defined (need expansion) |
| Product, BranchProduct (for price capture) | Sprint 4 | Defined |
| User, UserBranchRole (for role guards) | Sprint 2 | Defined |
| WebSocket Gateway stub | Sprint 1 | Stub only |
| Dashboard shell + routing | Sprint 3 | Defined |
| JWT auth + RBAC | Sprint 2 | Defined |

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Outbox processor lag causes stale kitchen display | Medium | High | Processor polls every 100ms; Redis Streams provides sub-second delivery once published |
| WebSocket broadcast bottleneck at 400 users | Medium | High | Worker pool with 10 workers + 5k queue; load test before deploy |
| Race condition on concurrent round confirmation votes | High | Medium | Optimistic locking (version column) on Round; last-write-wins for individual votes |
| KitchenTicket auto-consolidation race when multiple stations finish simultaneously | Medium | Medium | Use SELECT FOR UPDATE on Round row when consolidating ticket states |
| Redis Streams consumer crashes lose messages | Low | High | Consumer groups with pending list; reclaim after 30s; DLQ after 3 attempts |
| 5-minute timer drift across clients | Medium | Low | Server-side timer with WebSocket ping; client timer is display-only |
| Station assignment missing on products | Medium | Medium | Default to "GENERAL" station; admin can reassign. Validate on product creation. |
| Outbox table grows unbounded | Medium | Low | Archive published events older than 7 days via cron job |

## 7. Rollback Plan

- **Database**: Alembic downgrade removes outbox_events table and reverts Round/RoundItem/KitchenTicket changes
- **WebSocket Gateway**: Disable Redis Streams consumer; gateway reverts to stub
- **Frontend**: Feature flag `ENABLE_ROUNDS` gates Round confirmation UI; kitchen dashboard behind route guard
- **Outbox processor**: Stop background task; events remain in DB for retry when re-enabled
- **Partial rollback**: Each subsystem (outbox, kitchen tickets, broadcast) can be disabled independently

## 8. Success Criteria

1. Diner can create a round, all table diners vote, round auto-submits after 1.5s consensus delay
2. Round flows through all 6 states with correct role enforcement
3. Kitchen sees tickets fragmented by station with real-time updates
4. Outbox guarantees: no event lost between DB commit and Redis Streams publish
5. WebSocket broadcast reaches 400 concurrent users in <200ms p95
6. Admin Kanban view shows real-time round progression
7. >15min tickets show red urgency border in kitchen view
8. DLQ captures messages that fail 3 delivery attempts
9. Sound notifications play on relevant state changes in pwaMenu

## 9. Estimated Effort

- **Total**: 14-18 AI agent sessions
- **Phase 1** (DB + Enums + Models): 2 sessions
- **Phase 2** (Round service + state machine): 2-3 sessions
- **Phase 3** (KitchenTicket service + fragmentation): 2 sessions
- **Phase 4** (Outbox pattern): 2 sessions
- **Phase 5** (Redis Streams + WS Gateway): 3-4 sessions
- **Phase 6** (Kitchen Dashboard): 2 sessions
- **Phase 7** (Admin Orders View): 1-2 sessions
- **Phase 8** (pwaMenu Round Confirmation + Sound): 2 sessions
