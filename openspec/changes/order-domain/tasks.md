---
sprint: 8
artifact: tasks
status: complete
---

# SDD Tasks — Sprint 8: Rondas, Cocina y Outbox

## Status: APPROVED

---

## Phase 1: Database Foundation (Enums, Models, Migration)

### Task 1.1: New Enums
**Description**: Add all Sprint 8 enums to the shared enums module.
**Files**:
- `shared/shared/enums.py` — Add: `RoundStatus` (PENDIENTE, CONFIRMADO, ENVIADO, EN_COCINA, LISTO, SERVIDO, CANCELADO), `KitchenTicketStatus` (PENDIENTE, EN_PROGRESO, LISTO, ENTREGADO, CANCELADO), `OutboxEventStatus` (PENDING, PROCESSING, PUBLISHED, DLQ), `OutboxEventType` (ROUND_SUBMITTED, ROUND_CONFIRMED, ROUND_SENT_TO_KITCHEN, ROUND_IN_KITCHEN, ROUND_READY, ROUND_SERVED, ROUND_CANCELLED, KITCHEN_TICKET_CREATED, KITCHEN_TICKET_STARTED, KITCHEN_TICKET_COMPLETED, KITCHEN_TICKET_DELIVERED, KITCHEN_TICKET_CANCELLED, CHECK_REQUESTED, PAYMENT_CREATED, PAYMENT_COMPLETED, PAYMENT_FAILED, SERVICE_CALL_CREATED)
**Acceptance Criteria**:
- All enums defined as `str, Enum` classes
- Values match the spec exactly (RSM-001, KT-004, OBX-001, OBX-020)
- Import works from `shared.enums`

### Task 1.2: Expand Round Model
**Description**: Expand the Round model stub from Sprint 1 with all required fields.
**Files**:
- `shared/shared/models/orders/round.py` — Add columns: `branch_id` (FK), `round_number` (int, not null), `status` (varchar(20), default PENDIENTE), `version` (int, default 1), `cancelled_by` (FK users nullable), `cancelled_at` (timestamp nullable), `cancel_reason` (varchar(500) nullable). Add relationships: `items` (RoundItem), `tickets` (KitchenTicket). Add indexes: `ix_rounds_session_status`, `ix_rounds_branch_status`, `ix_rounds_created_at`. Add constraints: `uq_rounds_session_number`, `ck_round_status`.
**Acceptance Criteria**:
- Model matches the DB schema in Design section 1.1
- Optimistic locking via `version` column with SQLAlchemy `version_id_col` mapper arg
- AuditMixin applied (inherited from Sprint 1 base)
- Relationships use `selectinload` compatible lazy strategy

### Task 1.3: Expand RoundItem Model
**Description**: Expand RoundItem stub with pricing and diner tracking.
**Files**:
- `shared/shared/models/orders/round_item.py` — Add columns: `diner_id` (FK diners, not null), `unit_price_cents` (int, not null), `notes` (varchar(200) nullable). Add constraints: `ck_ri_quantity_positive`, `ck_ri_unit_price_positive`. Add index: `ix_round_items_round`.
**Acceptance Criteria**:
- `unit_price_cents` is immutable after creation (application-level enforcement)
- `diner_id` correctly references `diners.id`
- `quantity > 0` CHECK constraint present

### Task 1.4: Expand KitchenTicket Model
**Description**: Expand KitchenTicket stub with station and timing fields.
**Files**:
- `shared/shared/models/orders/kitchen_ticket.py` — Add columns: `station` (varchar(30), default 'GENERAL'), `started_at` (timestamp nullable), `completed_at` (timestamp nullable), `estimated_prep_time_seconds` (int nullable). Add constraints: `ck_kt_status`. Add indexes: `ix_kt_station_status`, `ix_kt_round`, `ix_kt_created_at`. Add relationship: `items` (via KitchenTicketItem junction).
**Acceptance Criteria**:
- `started_at` set only on PENDIENTE -> EN_PROGRESO transition
- `completed_at` set only on EN_PROGRESO -> LISTO transition
- Station defaults to 'GENERAL'

### Task 1.5: New KitchenTicketItem Model
**Description**: Create junction table between KitchenTicket and RoundItem.
**Files**:
- `shared/shared/models/orders/kitchen_ticket_item.py` — NEW file. Columns: `id` (PK), `kitchen_ticket_id` (FK), `round_item_id` (FK). Constraint: `uq_kti_ticket_item`. Index: `ix_kti_ticket`.
- `shared/shared/models/orders/__init__.py` — Register new model import.
**Acceptance Criteria**:
- Unique constraint prevents duplicate assignments
- CASCADE delete from kitchen_ticket and round_item

### Task 1.6: New OutboxEvent Model
**Description**: Create the outbox_events table model.
**Files**:
- `shared/shared/models/outbox/__init__.py` — NEW package init.
- `shared/shared/models/outbox/outbox_event.py` — NEW. Columns per OBX-001: `id`, `event_type`, `aggregate_type`, `aggregate_id`, `payload` (JSONB), `status` (default PENDING), `tenant_id`, `branch_id`, `retry_count` (default 0), `error_message`, `created_at`, `processed_at`, `published_at`. Indexes: `ix_outbox_pending` (partial), `ix_outbox_processing` (partial), `ix_outbox_aggregate`, `ix_outbox_branch`.
- `shared/shared/models/__init__.py` — Register OutboxEvent import.
**Acceptance Criteria**:
- JSONB type used for payload column (SQLAlchemy `JSONB`)
- Partial indexes on status for PENDING and PROCESSING (per design)
- No AuditMixin -- outbox is infra, not business entity

### Task 1.7: Add kitchen_station to Product
**Description**: Add kitchen_station column to existing Product model.
**Files**:
- `shared/shared/models/catalog/product.py` — Add column: `kitchen_station` (varchar(30), default 'GENERAL', not null).
**Acceptance Criteria**:
- Default value is 'GENERAL'
- Existing products get 'GENERAL' via migration default

### Task 1.8: Alembic Migration
**Description**: Generate and verify the migration for all Sprint 8 schema changes.
**Files**:
- `alembic/versions/XXX_sprint8_rounds_kitchen_outbox.py` — Auto-generated + manual review. Must handle: expand rounds table, expand round_items, expand kitchen_tickets, new kitchen_ticket_items, new outbox_events, add product.kitchen_station.
**Acceptance Criteria**:
- `alembic upgrade head` succeeds
- `alembic downgrade -1` reverts cleanly
- All indexes and constraints created
- Partial indexes use `postgresql_where` clause in SQLAlchemy Index

---

## Phase 2: Backend Services — Round State Machine

### Task 2.1: Outbox Service (Helper)
**Description**: Create a helper service for writing OutboxEvents atomically with business data.
**Files**:
- `rest_api/app/services/outbox_service.py` — Class `OutboxService` with method `create_event(session, event_type, aggregate_type, aggregate_id, payload, tenant_id, branch_id) -> OutboxEvent`. This method creates and adds an OutboxEvent to the given session (NOT committed -- caller commits the whole TX).
**Acceptance Criteria**:
- Event is added to session, not committed (OBX-002 compliance)
- Payload is serialized as dict (JSONB-compatible)
- Returns the created OutboxEvent instance for testing

### Task 2.2: Round Repository
**Description**: Create Round-specific repository with state machine queries.
**Files**:
- `shared/shared/repositories/round_repo.py` — Class `RoundRepository(BranchRepository[Round])` with methods:
  - `get_by_id_for_update(id) -> Round` — SELECT FOR UPDATE
  - `get_next_round_number(session_id) -> int` — MAX(round_number) + 1
  - `get_by_session(session_id, status?) -> list[Round]`
  - `get_by_branch_with_filters(status?, date_from?, date_to?, table_id?, waiter_id?, page, page_size) -> (list[Round], total)`
  - `get_summary(branch_id) -> dict` — Aggregate counts by status
**Acceptance Criteria**:
- All queries filter by tenant_id (inherited from BranchRepository)
- `get_by_id_for_update` uses `with_for_update()` for pessimistic locking
- Pagination returns tuple of (items, total_count)

### Task 2.3: Round Service (State Machine)
**Description**: Core Round business logic including state machine and price capture.
**Files**:
- `rest_api/app/services/round_service.py` — Class `RoundService` with methods:
  - `create_round(session_id, items: list[CreateRoundItemDTO]) -> Round` — Validates session active, captures prices from branch_products, assigns round_number, creates Round + RoundItems + OutboxEvent in single TX
  - `transition(round_id, action, user_id, user_role, reason?) -> Round` — Validates transition per RSM-002, checks role authorization, updates status, writes OutboxEvent. On "send": calls `_fragment_into_tickets()`. On "cancel": cascades to tickets per RSM-006.
  - `_fragment_into_tickets(round, session) -> list[KitchenTicket]` — Groups RoundItems by product.kitchen_station, creates KitchenTickets + KitchenTicketItems + OutboxEvents.
  - `_validate_transition(current_status, action, role) -> new_status` — Pure function, returns new status or raises InvalidTransitionError
  - `_check_sector_authorization(user_id, round) -> bool` — Verifies waiter is assigned to round's table's sector
**Acceptance Criteria**:
- Price capture: `unit_price_cents` taken from `branch_products.price_override_cents ?? products.base_price_cents` at creation time (RND-007)
- Optimistic locking: `version` incremented on every transition. StaleDataError if concurrent (RSM-008)
- Role validation: waiter can only confirm/serve rounds in their sector; admin/manager can do everything
- Fragmentation creates correct junction records (KitchenTicketItem)
- ALL mutations write OutboxEvent in the same transaction (OBX-002)
- Cancel from EN_COCINA cascades to non-terminal tickets (RSM-006)

### Task 2.4: Round Pydantic Schemas
**Description**: Request/response schemas for Round endpoints.
**Files**:
- `rest_api/app/schemas/round_schemas.py` — Classes:
  - `CreateRoundItemRequest(product_id: int, quantity: int, notes: str | None, diner_id: int)`
  - `CreateRoundRequest(session_id: int, items: list[CreateRoundItemRequest])`
  - `RoundTransitionRequest(action: Literal["confirm","send","serve","cancel"], reason: str | None)`
  - `RoundItemResponse(id, product_id, product_name, diner_id, diner_name, quantity, unit_price_cents, notes)`
  - `KitchenTicketBriefResponse(id, station, status, started_at, completed_at)`
  - `RoundResponse(id, round_number, session_id, status, items, tickets, created_at, updated_at)`
  - `RoundListResponse(items: list[RoundResponse], total, page, page_size)`
**Acceptance Criteria**:
- All response schemas use `model_config = ConfigDict(from_attributes=True)`
- Validation: `quantity > 0`, `notes` max 200 chars, `reason` max 500 chars
- Action literal matches exactly: confirm, send, serve, cancel

### Task 2.5: Round Router
**Description**: REST endpoints for Round management.
**Files**:
- `rest_api/app/routers/rounds.py` — Endpoints:
  - `POST /api/rounds` — Create round (API-001)
  - `PATCH /api/rounds/{round_id}/transition` — State transition (API-002)
  - `GET /api/rounds` — List with filters (API-003)
  - `GET /api/rounds/{round_id}` — Get single round with items/tickets (API-004)
- `rest_api/app/main.py` — Register router.
**Acceptance Criteria**:
- All endpoints require JWT auth (dependency from Sprint 2)
- POST returns 201
- PATCH returns 200 on success, 422 on invalid transition, 403 on unauthorized role
- GET supports query params: session_id, status, page, page_size
- Consistent error response format: `{ detail: string, code: string }`

---

## Phase 3: Backend Services — Kitchen Tickets

### Task 3.1: KitchenTicket Repository
**Description**: Repository for kitchen ticket queries.
**Files**:
- `shared/shared/repositories/kitchen_ticket_repo.py` — Class `KitchenTicketRepository` with methods:
  - `get_by_id_for_update(id) -> KitchenTicket`
  - `get_by_round(round_id) -> list[KitchenTicket]`
  - `get_by_station_and_status(station?, status?, page, page_size) -> (list, total)`
  - `get_dashboard_data(branch_id, station?) -> dict` — Aggregated counts + ticket lists for dashboard
  - `get_non_terminal_by_round(round_id) -> list[KitchenTicket]` — For cascade cancel
**Acceptance Criteria**:
- Dashboard query returns: pending_count, in_progress_count, completed_today, avg_prep_time_seconds
- Elapsed time calculated as `now() - created_at` for pending, `now() - started_at` for in_progress
- Results include joined data: table_number, sector_name (via round -> session -> table -> sector)

### Task 3.2: Kitchen Service (Auto-Consolidation)
**Description**: Kitchen ticket state transitions with automatic Round consolidation.
**Files**:
- `rest_api/app/services/kitchen_service.py` — Class `KitchenService` with methods:
  - `transition_ticket(ticket_id, action, user_id) -> KitchenTicket` — Validates transition per KT-005, sets timestamps, writes OutboxEvent. After transition, calls `_check_round_consolidation()`.
  - `_check_round_consolidation(round_id, session) -> Round | None` — SELECT FOR UPDATE on Round. If any ticket EN_PROGRESO and round is ENVIADO -> Round EN_COCINA. If all tickets LISTO/CANCELADO and round is EN_COCINA -> Round LISTO. Returns updated Round (or None if no change). Writes OutboxEvent for round transition.
  - `cancel_tickets_for_round(round_id, session)` — Called by RoundService on cancel. Sets all non-terminal tickets to CANCELADO.
**Acceptance Criteria**:
- `started_at` set ONLY on PENDIENTE -> EN_PROGRESO (KT-005)
- `completed_at` set ONLY on EN_PROGRESO -> LISTO (KT-005)
- Consolidation uses SELECT FOR UPDATE (KT-008) to prevent race condition (Scenario 13)
- Consolidation correctly handles mixed states (some LISTO, some CANCELADO = Round LISTO)
- All transitions write OutboxEvent in same TX

### Task 3.3: Kitchen Pydantic Schemas
**Description**: Schemas for kitchen endpoints.
**Files**:
- `rest_api/app/schemas/kitchen_schemas.py` — Classes:
  - `KitchenTicketTransitionRequest(action: Literal["start", "complete"])`
  - `KitchenTicketItemResponse(id, product_name, quantity, notes)`
  - `KitchenTicketResponse(id, round_id, station, status, items, table_number, sector_name, created_at, started_at, completed_at, elapsed_seconds)`
  - `KitchenTicketListResponse(items, total)`
  - `KitchenDashboardResponse(pending_count, in_progress_count, completed_today, avg_prep_time_seconds, tickets: { pending: list, in_progress: list })`
**Acceptance Criteria**:
- `elapsed_seconds` computed server-side, not stored
- Response includes denormalized table_number and sector_name

### Task 3.4: Kitchen Router
**Description**: REST endpoints for kitchen operations.
**Files**:
- `rest_api/app/routers/kitchen.py` — Endpoints:
  - `GET /api/kitchen/tickets` — List tickets (API-010)
  - `PATCH /api/kitchen/tickets/{ticket_id}/transition` — Advance ticket (API-011)
  - `GET /api/kitchen/dashboard` — Dashboard data (API-012)
- `rest_api/app/main.py` — Register router.
**Acceptance Criteria**:
- Tickets filterable by station and status
- Transition returns 200 on success, 422 on invalid transition
- Dashboard returns aggregated data for the kitchen display
- Auth: kitchen, admin, manager roles only

### Task 3.5: Admin Orders Router
**Description**: REST endpoints for admin order management.
**Files**:
- `rest_api/app/routers/admin_orders.py` — Endpoints:
  - `GET /api/admin/orders/summary` — Summary cards (API-020)
  - `GET /api/admin/orders` — Filterable orders list (API-021)
- `rest_api/app/schemas/admin_order_schemas.py` — Schemas:
  - `OrdersSummaryResponse(pending, in_kitchen, ready, total_today, avg_time_seconds)`
  - `AdminOrdersListResponse(items, total, page, page_size)`
- `rest_api/app/main.py` — Register router.
**Acceptance Criteria**:
- Summary: real-time counts for current day
- List: filterable by status, date_from, date_to, table_id, waiter_id
- Pagination with page + page_size
- Auth: admin, manager roles only

---

## Phase 4: Outbox Processor

### Task 4.1: Outbox Processor Implementation
**Description**: Background asyncio task that polls outbox and publishes to Redis Streams.
**Files**:
- `rest_api/app/services/outbox_processor.py` — Class `OutboxProcessor` with:
  - `start()` — Creates asyncio tasks for poll_loop and recovery_loop
  - `stop()` — Graceful shutdown
  - `_poll_loop()` — Every 100ms, process batch of 50 PENDING events
  - `_process_batch()` — SELECT FOR UPDATE SKIP LOCKED, set PROCESSING, XADD to Redis, set PUBLISHED (or retry/DLQ on failure)
  - `_recovery_loop()` — Every 60s, reset PROCESSING events older than 60s to PENDING
**Acceptance Criteria**:
- Uses `SELECT ... FOR UPDATE SKIP LOCKED` (safe for concurrent processors)
- Publishes to `stream:branch:{branch_id}:events` with fields: outbox_id, event_type, aggregate_type, aggregate_id, payload, tenant_id, branch_id
- Retry: increment retry_count on failure, DLQ after 3 (OBX-006)
- Recovery: stale PROCESSING (>60s) reset to PENDING (OBX-010)
- Poll interval configurable via `OUTBOX_POLL_INTERVAL_MS` env var (OBX-007)
- Graceful shutdown: finish current batch, don't start new

### Task 4.2: Outbox Repository
**Description**: Database operations for outbox events.
**Files**:
- `shared/shared/repositories/outbox_repo.py` — Class `OutboxRepository` with:
  - `get_pending_batch(limit=50) -> list[OutboxEvent]` — FOR UPDATE SKIP LOCKED
  - `mark_processing(events)` — Bulk update
  - `mark_published(event)` — Single update
  - `mark_failed(event, error_message)` — Increment retry, DLQ if >= 3
  - `recover_stale(cutoff_seconds=60)` — Reset stale PROCESSING to PENDING
  - `archive_old(days=7)` — Delete PUBLISHED events older than N days
**Acceptance Criteria**:
- All operations are session-scoped (caller manages TX)
- Batch operations use bulk update where possible
- Archive returns count of deleted events

### Task 4.3: Register Outbox Processor in Lifespan
**Description**: Start/stop the outbox processor with the FastAPI app lifecycle.
**Files**:
- `rest_api/app/main.py` — Modify lifespan to:
  - On startup: create OutboxProcessor, call `await processor.start()`
  - On shutdown: call `await processor.stop()`
**Acceptance Criteria**:
- Processor starts after migrations and seed
- Processor stops gracefully on SIGTERM
- Processor uses the same session factory and Redis client as the app

---

## Phase 5: WebSocket Gateway + Redis Streams Consumer

### Task 5.1: WebSocket Connection Model
**Description**: Dataclass for WebSocket connection metadata.
**Files**:
- `ws_gateway/models.py` — Dataclass `WebSocketConnection` with fields: `id` (uuid), `websocket` (WebSocket), `user_id`, `tenant_id`, `branch_id`, `role`, `sector_id` (nullable), `table_session_id` (nullable), `station` (nullable), `connected_at`.
**Acceptance Criteria**:
- All fields needed for routing are present
- `id` generated on creation (uuid4)

### Task 5.2: Connection Registry
**Description**: Multi-indexed registry for fast WebSocket lookup.
**Files**:
- `ws_gateway/connection_registry.py` — Class `ConnectionRegistry` with methods per Design section 5.2: `register()`, `unregister()`, `get_by_role()`, `get_by_sector()`, `get_by_session()`, `get_by_station()`, `get_admins_and_managers()`, `get_all_waiters()`, `connection_count()`.
**Acceptance Criteria**:
- Thread-safe (asyncio lock for mutations)
- O(1) lookup per index
- Cleanup on unregister removes from ALL indexes
- `connection_count()` returns total for health endpoint

### Task 5.3: Event Router
**Description**: Routes events to target connections based on the routing matrix.
**Files**:
- `ws_gateway/event_router.py` — Class `EventRouter` with: `ROUTING_TABLE` (dict mapping event_type to resolver function), `resolve(event_type, payload, registry) -> set[WebSocketConnection]`. Implements routing per RT-001 through RT-004.
**Acceptance Criteria**:
- Each event type maps to the correct set of connections per the routing matrix (Spec 1.8)
- Payload contains `sector_id`, `table_session_id`, `station` for scoped routing
- Unknown event types return empty set (no crash)
- `RoutingContext` helper provides: `admins_managers()`, `all_waiters()`, `sector_waiters()`, `kitchen_all()`, `kitchen_station()`, `table_diners()`, `kitchen_if_was_in_kitchen()`

### Task 5.4: Broadcast Worker Pool
**Description**: 10-worker asyncio pool for sending WebSocket messages.
**Files**:
- `ws_gateway/broadcast_pool.py` — Class `BroadcastPool` with:
  - `__init__(num_workers=10, queue_size=5000)`
  - `start()` — Creates N worker tasks
  - `stop()` — Drains queue, cancels workers
  - `enqueue(connections: set, payload: dict)` — Put BroadcastTask on queue. If full, log warning and drop oldest.
  - `_worker(worker_id)` — Loop: dequeue task, send payload to each connection, handle disconnect (remove from registry)
  - `queue_depth` property — For health check
  - `stats` property — Messages sent, errors, dropped
**Acceptance Criteria**:
- 10 workers (configurable via `WS_BROADCAST_WORKERS` env var)
- Queue maxsize 5000 (configurable via `WS_BROADCAST_QUEUE_SIZE`)
- Disconnected sockets caught per-connection (don't fail entire batch)
- Metrics tracked: total_sent, total_errors, total_dropped, queue_depth

### Task 5.5: Redis Streams Consumer
**Description**: Consumes from branch event streams and routes to broadcast pool.
**Files**:
- `ws_gateway/stream_consumer.py` — Class `StreamConsumer` with:
  - `__init__(redis, registry, router, pool, instance_id)`
  - `start(branch_ids: list[int])` — For each branch: ensure consumer group exists, reclaim pending, start consumer loop
  - `stop()` — Graceful shutdown
  - `_consumer_loop(branch_id)` — XREADGROUP BLOCK 5000, process entries, XACK on success
  - `_reclaim_loop(branch_id)` — Every 15s, XAUTOCLAIM pending >30s, DLQ if delivery_count >= 3
  - `_process_entry(entry)` — Parse payload, resolve connections via router, enqueue to broadcast pool
**Acceptance Criteria**:
- Consumer group: `ws-gateway-group` (RS-003)
- Consumer name: `ws-gw-{instance_id}` (RS-004)
- XREADGROUP with BLOCK 5000, COUNT 10 (RS-009)
- XACK after successful routing (RS-005)
- Reclaim pending >30s via XAUTOCLAIM (RS-006)
- DLQ after 3 delivery attempts (RS-007): XADD to `dlq:branch:{id}:events`
- On startup: reclaim before consuming (RS-010)

### Task 5.6: Voting Manager
**Description**: Manages round confirmation voting via Redis and WebSocket.
**Files**:
- `ws_gateway/voting_manager.py` — Class `VotingManager` with:
  - `initiate_vote(branch_id, session_id, draft_id, proponent_id, diner_ids, items)` — Create Redis key with TTL 6min, auto-vote proponent, broadcast vote_request
  - `handle_vote(branch_id, session_id, draft_id, diner_id, vote)` — Update Redis, broadcast vote_update. If all YES: set auto_send_at, schedule auto-send task
  - `handle_retract(branch_id, session_id, draft_id, diner_id)` — Remove vote, cancel auto-send if pending
  - `handle_cancel(branch_id, session_id, draft_id, proponent_id)` — Only proponent can cancel, broadcast cancelled
  - `_auto_send(branch_id, session_id, draft_id)` — After 1.5s delay, POST /api/rounds internally
  - `_check_timeout()` — Background task checking for expired voting sessions
**Acceptance Criteria**:
- Redis key format: `vote:{branch_id}:{session_id}:{draft_id}` with TTL 6min (VP-010)
- Only proponent can cancel (VP-009)
- Retract during 1.5s window cancels auto-send (VP-006)
- Timeout broadcasts `round:timeout` (VP-008)
- Auto-send calls REST API internally to create the Round (VP-007)
- Server-side timer is source of truth (RND-004)

### Task 5.7: WebSocket Gateway Main
**Description**: Full WS Gateway implementation with FastAPI/Starlette WebSocket.
**Files**:
- `ws_gateway/main.py` — Full implementation:
  - WebSocket endpoint: `/ws?token={jwt}`
  - On connect: decode JWT, extract user metadata, register in ConnectionRegistry
  - On message: route to VotingManager (vote events) or ignore
  - On disconnect: unregister from ConnectionRegistry
  - Ping/pong: every 30s, terminate stale after 10s (BC-010)
  - Startup: create Registry, Router, Pool, Consumer, VotingManager; start all
  - Shutdown: stop all gracefully
- `ws_gateway/health.py` — `/ws/health` endpoint returning: connection_count, queue_depth, worker_stats, consumer_status
**Acceptance Criteria**:
- JWT validation on connect (BC-007)
- Connection metadata extracted from JWT: user_id, tenant_id, branch_id, role (BC-008)
- Additional metadata from query params: sector_id, table_session_id, station
- Disconnect cleanup within 1s (BC-009)
- Periodic ping every 30s (BC-010)
- Health endpoint returns useful diagnostics (BC-006)

---

## Phase 6: Kitchen Dashboard (Frontend)

### Task 6.1: Kitchen Zustand Store
**Description**: State management for kitchen dashboard.
**Files**:
- `dashboard/src/stores/kitchenStore.ts` — Per Design section 9.1. State: tickets (Record), selectedStation, selectedTicketId, isMuted. Actions: setTickets, upsertTicket, removeTicket, setSelectedStation, setSelectedTicket, toggleMute. Selectors: usePendingTickets, useInProgressTickets (individual selectors per React 19 convention).
**Acceptance Criteria**:
- Individual selectors (NOT `useStore(s => s.property)` pattern -- causes infinite loops in React 19)
- Tickets normalized as Record<id, ticket>
- Computed lists derived in selectors, not stored
- Station filter applied in selectors

### Task 6.2: Kitchen API Service
**Description**: API client for kitchen endpoints.
**Files**:
- `dashboard/src/services/kitchenApi.ts` — Functions: `fetchTickets(station?, status?)`, `fetchDashboard()`, `transitionTicket(ticketId, action)`. Uses existing API client from Sprint 3 (with auth header).
**Acceptance Criteria**:
- All functions return typed responses (KitchenTicketResponse, etc.)
- Error handling consistent with Sprint 3 patterns
- Base URL from environment config

### Task 6.3: Kitchen WebSocket Hook
**Description**: Hook for real-time kitchen ticket updates.
**Files**:
- `dashboard/src/hooks/useKitchenTickets.ts` — Hook that: connects to WS gateway, listens for KITCHEN_TICKET_* events, calls kitchenStore.upsertTicket/removeTicket on event. On mount: fetch initial data via API. On unmount: disconnect.
**Acceptance Criteria**:
- Combines REST (initial load) + WebSocket (real-time updates)
- Reconnection logic with exponential backoff
- Updates Zustand store on each event
- Cleans up on unmount

### Task 6.4: KitchenTicketCard Component
**Description**: Card component for ticket display in columns.
**Files**:
- `dashboard/src/components/kitchen/KitchenTicketCard.tsx` — Displays: table number (badge), item count, elapsed time. Red border if >15min (Scenario 12). onClick opens modal. Elapsed time updates every second (setInterval or requestAnimationFrame).
**Acceptance Criteria**:
- Red border class applied when elapsed > 900 seconds (15min)
- Elapsed time formatted as MM:SS
- Live-updating timer (not static)
- Accessible: proper ARIA labels

### Task 6.5: KitchenTicketModal Component
**Description**: Detail modal with ticket items and advance button.
**Files**:
- `dashboard/src/components/kitchen/KitchenTicketModal.tsx` — Shows: station, table, round #, item list (product, qty, notes), live elapsed timer, "Avanzar" button. Button label: "Iniciar" (if PENDIENTE) or "Completar" (if EN_PROGRESO). Calls transitionTicket API on click.
**Acceptance Criteria**:
- Button disabled during API call (loading state)
- Optimistic update: immediately update store, rollback on error
- Closes modal on successful transition
- Shows error toast on failure

### Task 6.6: KitchenColumn and KitchenHeader Components
**Description**: Layout components for the kitchen dashboard.
**Files**:
- `dashboard/src/components/kitchen/KitchenColumn.tsx` — Renders list of KitchenTicketCards. Title prop, empty state message.
- `dashboard/src/components/kitchen/KitchenHeader.tsx` — StationSelector dropdown, ConnectionStatus indicator, SoundToggle button.
- `dashboard/src/components/kitchen/StationSelector.tsx` — Dropdown with "Todas" + available stations from tickets.
- `dashboard/src/components/kitchen/KitchenAudioManager.tsx` — Hidden component that plays audio on KITCHEN_TICKET_CREATED event (SND-005). Respects isMuted from store.
**Acceptance Criteria**:
- StationSelector derives options from actual ticket data (not hardcoded)
- ConnectionStatus shows green/red dot based on WebSocket state
- SoundToggle persists preference in localStorage

### Task 6.7: KitchenDashboardPage
**Description**: Page component assembling all kitchen dashboard pieces.
**Files**:
- `dashboard/src/pages/KitchenDashboardPage.tsx` — Assembles: KitchenHeader, two KitchenColumns (Nuevos/En Preparacion), KitchenTicketModal, KitchenAudioManager. Uses useKitchenTickets hook for data.
- Dashboard router — Add route `/kitchen` pointing to KitchenDashboardPage. Route guard: kitchen, admin, manager roles.
**Acceptance Criteria**:
- Two-column responsive layout (flex, wrap on mobile)
- Cards sorted: Nuevos by created_at ASC, En Preparacion by started_at ASC (oldest first)
- Page title: "Cocina" or "Kitchen"
- Route protected by role guard

---

## Phase 7: Admin Orders View (Frontend)

### Task 7.1: Orders Zustand Store
**Description**: State management for admin orders view.
**Files**:
- `dashboard/src/stores/ordersStore.ts` — Per Design section 9.2. State: rounds, summary, filters, viewMode, selectedRoundId, pagination. Actions: setRounds, upsertRound, setSummary, setFilters, setViewMode, setSelectedRound, setPage.
**Acceptance Criteria**:
- Individual selectors (React 19 convention)
- Rounds normalized as Record<id, Round>
- Filters: { status, dateFrom, dateTo, tableId, waiterId }

### Task 7.2: Admin Orders API Service
**Description**: API client for admin order endpoints.
**Files**:
- `dashboard/src/services/adminOrdersApi.ts` — Functions: `fetchSummary()`, `fetchOrders(filters, page, pageSize)`, `transitionRound(roundId, action, reason?)`.
**Acceptance Criteria**:
- Query string built from non-null filter values
- Typed responses

### Task 7.3: Admin Orders WebSocket Hook
**Description**: Hook for real-time order updates.
**Files**:
- `dashboard/src/hooks/useAdminOrders.ts` — Hook that: connects WS, listens for ROUND_* events, updates ordersStore. On mount: fetch initial summary + orders.
**Acceptance Criteria**:
- Summary cards update on each round event
- Kanban and grid update on round state change

### Task 7.4: OrdersSummaryCards Component
**Description**: Top summary cards row.
**Files**:
- `dashboard/src/components/orders/OrdersSummaryCards.tsx` — 4 cards in grid: Pendientes (yellow), En Cocina (blue), Listos (green), Total Hoy (gray). Each shows count + icon.
- `dashboard/src/components/orders/SummaryCard.tsx` — Reusable card: title, count, icon, color.
**Acceptance Criteria**:
- Cards update in real-time via WebSocket
- Responsive: 2x2 on mobile, 4x1 on desktop

### Task 7.5: OrdersKanban Component
**Description**: 3-column Kanban board for rounds.
**Files**:
- `dashboard/src/components/orders/OrdersKanban.tsx` — 3 columns: Pendientes (PENDIENTE+CONFIRMADO), En Cocina (ENVIADO+EN_COCINA), Listos (LISTO).
- `dashboard/src/components/orders/KanbanColumn.tsx` — Column with title, count badge, list of RoundCards.
- `dashboard/src/components/orders/RoundCard.tsx` — Card: round #, table, items count, elapsed time, waiter name. onClick opens RoundDetailModal.
**Acceptance Criteria**:
- Columns map multiple statuses (PENDIENTE+CONFIRMADO in first column)
- Cards sorted by created_at ASC within each column
- Smooth transitions when cards move between columns (via key on round.id)

### Task 7.6: OrdersGrid Component
**Description**: Table/grid view with filters.
**Files**:
- `dashboard/src/components/orders/OrdersGrid.tsx` — Data table with columns: #, Mesa, Items, Estado, Mozo, Tiempo, Acciones.
- `dashboard/src/components/orders/FilterBar.tsx` — Filters: StatusFilter (multi-select), DateRangeFilter, TableFilter, WaiterFilter. Debounced (300ms) filter changes trigger API refetch.
**Acceptance Criteria**:
- Sortable columns (at least by time and status)
- Pagination controls
- Filter changes debounced, not on every keystroke
- Empty state message

### Task 7.7: RoundDetailModal and AdminOrdersPage
**Description**: Modal for round details and page assembly.
**Files**:
- `dashboard/src/components/orders/RoundDetailModal.tsx` — Shows: round header, item list (product, qty, price, diner, notes), ticket status per station, action buttons (Confirmar/Enviar/Cancelar -- role-gated).
- `dashboard/src/pages/AdminOrdersPage.tsx` — Assembles: OrdersSummaryCards, ViewToggle, OrdersKanban or OrdersGrid (based on viewMode), RoundDetailModal. Uses useAdminOrders hook.
- Dashboard router — Add route `/orders` with admin/manager guard.
**Acceptance Criteria**:
- Action buttons visible based on current user role and round status
- Cancel requires reason input (modal within modal or inline form)
- Route: `/orders`, protected by admin/manager role guard

---

## Phase 8: pwaMenu Round Confirmation + Sound

### Task 8.1: Round Zustand Store (pwaMenu)
**Description**: State management for round voting in pwaMenu.
**Files**:
- `pwa_menu/src/stores/roundStore.ts` — Per Design section 9.3. State: currentVote, rounds, isSubmitting. Actions: setVotingSession, updateVotes, setRounds, upsertRound, setSubmitting, clearVoting.
**Acceptance Criteria**:
- VotingSession tracks all vote states per diner
- autoSendAt used for countdown display
- Individual Zustand selectors

### Task 8.2: Round API Service (pwaMenu)
**Description**: API client for round endpoints from pwaMenu.
**Files**:
- `pwa_menu/src/services/roundApi.ts` — Functions: `fetchRounds(sessionId)`, `createRound(sessionId, items)`. Note: round creation is done server-side by VotingManager after auto-send.
**Acceptance Criteria**:
- Uses pwaMenu's existing API client with table token auth
- Typed responses

### Task 8.3: Voting WebSocket Hook
**Description**: Hook managing the voting protocol over WebSocket.
**Files**:
- `pwa_menu/src/hooks/useVoting.ts` — Hook that:
  - Sends `initiate_vote` message with items and diner list
  - Listens for `round:vote_request`, `round:vote_update`, `round:submitted`, `round:cancelled`, `round:timeout`
  - Updates roundStore on each event
  - Provides actions: `vote(yes/no)`, `retract()`, `cancelRound()`
**Acceptance Criteria**:
- Handles all 6 WebSocket event types (WS-001 through WS-006)
- Updates VotingSession state in store on each event
- Triggers sound notifications via useSound hook
- Cleanup on unmount

### Task 8.4: useSound Hook
**Description**: Audio playback hook for sound notifications.
**Files**:
- `pwa_menu/src/hooks/useSound.ts` — Hook that: preloads audio files on mount, exposes `play(soundName)` function, handles browser autoplay policy (request permission on first interaction), respects mute preference.
- `pwa_menu/src/assets/sounds/vote-request.mp3` — NEW audio file
- `pwa_menu/src/assets/sounds/round-submitted.mp3` — NEW audio file
- `pwa_menu/src/assets/sounds/alert.mp3` — NEW audio file
**Acceptance Criteria**:
- Uses Web Audio API for low-latency playback (SND-004)
- Falls back to HTMLAudioElement if Web Audio not available
- Preloads all sounds on first user interaction
- Mute preference persisted in localStorage

### Task 8.5: RoundConfirmationPanel Component
**Description**: The main voting UI shown to all diners.
**Files**:
- `pwa_menu/src/components/round/RoundConfirmationPanel.tsx` — Bottom sheet modal per Design section 7.3. Shows: timer (5min countdown), voter list with status icons, item summary, auto-send countdown bar, action buttons.
- `pwa_menu/src/components/round/VoterList.tsx` — List of VoterRow components.
- `pwa_menu/src/components/round/VoterRow.tsx` — Diner avatar, name, vote status icon.
- `pwa_menu/src/components/round/AutoSendCountdown.tsx` — Progress bar showing 1.5s countdown when all confirmed.
- `pwa_menu/src/components/round/ItemSummary.tsx` — Collapsible list of items with total.
**Acceptance Criteria**:
- Timer counts down from 5:00, server-side authoritative (client display only)
- Vote status icons: pending (hourglass), confirmed (checkmark), declined (X)
- Auto-send countdown: animated progress bar, 1.5 seconds
- Proponent sees "Cancelar Ronda" button; others see "Confirmo" / "Cancelar mi voto"
- Panel dismisses on round:submitted or round:cancelled or round:timeout
- Responsive mobile-first design

### Task 8.6: Sound Integration
**Description**: Wire sound notifications into the voting and round state flows.
**Files**:
- `pwa_menu/src/components/shared/SoundManager.tsx` — Hidden component that subscribes to roundStore and plays sounds: vote-request on round:vote_request (if not proponent, SND-001), round-submitted on round:submitted (SND-002), alert on round:timeout or round:cancelled (SND-003).
**Acceptance Criteria**:
- Sounds play ONLY for the correct events per SND-001 through SND-003
- No sound for proponent on vote_request (they initiated it)
- Respects mute toggle

---

## Phase Summary

| Phase | Tasks | Key Deliverable |
|-------|-------|----------------|
| 1. DB Foundation | 1.1-1.8 | Models, enums, migration |
| 2. Round State Machine | 2.1-2.5 | Round CRUD + transitions + price capture |
| 3. Kitchen Tickets | 3.1-3.5 | Ticket transitions + auto-consolidation + admin orders |
| 4. Outbox Processor | 4.1-4.3 | Background processor + retry + DLQ |
| 5. WS Gateway | 5.1-5.7 | Full gateway: registry, router, pool, consumer, voting |
| 6. Kitchen Dashboard | 6.1-6.7 | Real-time kitchen display |
| 7. Admin Orders | 7.1-7.7 | Kanban + grid admin view |
| 8. pwaMenu Rounds | 8.1-8.6 | Voting protocol + confirmation panel + sounds |

**Total tasks: 35**
**Estimated sessions: 14-18**
**Total new/modified files: ~65**
