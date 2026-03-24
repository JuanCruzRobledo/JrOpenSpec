---
sprint: 8
artifact: spec
status: complete
---

# SDD Spec — Sprint 8: Rondas, Cocina y Outbox

## Status: APPROVED

---

## 1. Requirements (RFC 2119)

### 1.1 Round Confirmation Protocol (pwaMenu)

- **RND-001**: The system MUST provide a `RoundConfirmationPanel` component that displays all diners in the current table session with their vote status (pending/confirmed/declined).
- **RND-002**: The proponent (diner who initiated the round) MUST be able to cancel the round at any point before submission.
- **RND-003**: A 5-minute server-side timer MUST start when the confirmation panel opens. If quorum (all diners vote YES) is not reached within 5 minutes, the round MUST be auto-cancelled with reason `TIMEOUT`.
- **RND-004**: The server MUST track the timer. The client MAY display a countdown but MUST NOT be the source of truth for timeout.
- **RND-005**: Once all diners vote YES, a 1.5-second auto-send countdown MUST start. After 1.5 seconds, the round MUST be automatically submitted to the backend.
- **RND-006**: During the 1.5-second countdown, any diner MUST be able to retract their vote, which cancels the auto-send and resets to the voting state.
- **RND-007**: When a round is submitted, the system MUST capture the current `price_cents` from `branch_products` for each item and store it as `unit_price_cents` on `RoundItem`. This price is immutable after capture.
- **RND-008**: Each `RoundItem` MUST store: `product_id`, `quantity`, `unit_price_cents`, `notes` (optional, max 200 chars), `diner_id` (who ordered it).
- **RND-009**: The system MUST assign an auto-incrementing `round_number` per `table_session` (starting at 1).
- **RND-010**: The system MUST emit a sound notification on the proponent's device when all votes are collected.
- **RND-011**: The system SHOULD display a toast notification to all diners when the round is successfully submitted.

### 1.2 Round State Machine

- **RSM-001**: A Round MUST have exactly one of these states: `PENDIENTE`, `CONFIRMADO`, `ENVIADO`, `EN_COCINA`, `LISTO`, `SERVIDO`, `CANCELADO`.
- **RSM-002**: The state machine MUST enforce the following transitions:

| From | To | Trigger | Allowed Roles | Guard |
|------|----|---------|---------------|-------|
| PENDIENTE | CONFIRMADO | Waiter acknowledges | waiter | Round belongs to waiter's assigned sector |
| PENDIENTE | CANCELADO | Cancel | admin, manager | Before SERVIDO |
| CONFIRMADO | ENVIADO | Send to kitchen | admin, manager | -- |
| CONFIRMADO | CANCELADO | Cancel | admin, manager | Before SERVIDO |
| ENVIADO | EN_COCINA | Auto (first ticket starts) | system | At least 1 KitchenTicket transitions to EN_PROGRESO |
| ENVIADO | CANCELADO | Cancel | admin, manager | Before SERVIDO |
| EN_COCINA | LISTO | Auto (all tickets done) | system | ALL KitchenTickets for this round are LISTO |
| EN_COCINA | CANCELADO | Cancel | admin, manager | Before SERVIDO |
| LISTO | SERVIDO | Waiter delivers | waiter | Round belongs to waiter's assigned sector |
| LISTO | CANCELADO | Cancel | admin, manager | Before SERVIDO |

- **RSM-003**: Any transition NOT listed above MUST be rejected with HTTP 422 and error code `INVALID_TRANSITION`.
- **RSM-004**: The `CANCELADO` state MUST store a `cancelled_by` (user_id) and `cancelled_at` (timestamp) and `cancel_reason` (string, max 500 chars).
- **RSM-005**: Cancellation MUST be allowed from any state EXCEPT `SERVIDO` and `CANCELADO`, and MUST be restricted to `admin` or `manager` roles.
- **RSM-006**: When a Round is cancelled from `EN_COCINA`, all associated KitchenTickets in non-terminal states (not ENTREGADO) MUST be cancelled too.
- **RSM-007**: Each state transition MUST generate an OutboxEvent with the appropriate event type.
- **RSM-008**: The system MUST use optimistic locking (version column) on Round to prevent concurrent state transitions.

### 1.3 KitchenTicket State Machine

- **KT-001**: When a Round transitions to `ENVIADO`, the system MUST fragment it into KitchenTickets grouped by `station`. The station is derived from `product.kitchen_station` (new field, default `GENERAL`).
- **KT-002**: Each KitchenTicket MUST contain: `round_id`, `station` (string), `status`, `started_at` (nullable), `completed_at` (nullable), `estimated_prep_time_seconds` (nullable).
- **KT-003**: Each KitchenTicket MUST have associated KitchenTicketItems (junction: `kitchen_ticket_id`, `round_item_id`).
- **KT-004**: A KitchenTicket MUST have exactly one of these states: `PENDIENTE`, `EN_PROGRESO`, `LISTO`, `ENTREGADO`, `CANCELADO`.
- **KT-005**: The KitchenTicket state machine MUST enforce:

| From | To | Trigger | Guard |
|------|----|---------|-------|
| PENDIENTE | EN_PROGRESO | Kitchen staff starts | Sets `started_at = now()` |
| EN_PROGRESO | LISTO | Kitchen staff completes | Sets `completed_at = now()` |
| LISTO | ENTREGADO | System (when Round -> SERVIDO) | Auto-cascades |
| Any non-terminal | CANCELADO | System (when Round cancelled) | Cascades from Round |

- **KT-006**: When ANY KitchenTicket for a Round transitions to `EN_PROGRESO`, the system MUST auto-transition the Round to `EN_COCINA` (if currently `ENVIADO`).
- **KT-007**: When ALL KitchenTickets for a Round reach `LISTO` (or `CANCELADO`), the system MUST auto-transition the Round to `LISTO`.
- **KT-008**: Auto-consolidation MUST use `SELECT ... FOR UPDATE` on the Round row to prevent race conditions when multiple tickets complete simultaneously.
- **KT-009**: Each KitchenTicket state transition MUST generate an OutboxEvent.
- **KT-010**: If a product has no `kitchen_station` defined, it MUST default to `GENERAL` station.

### 1.4 Outbox Pattern

- **OBX-001**: The system MUST have an `outbox_events` table with columns: `id` (SERIAL PK), `event_type` (string, NOT NULL), `aggregate_type` (string, NOT NULL -- e.g., 'Round', 'KitchenTicket'), `aggregate_id` (integer, NOT NULL), `payload` (JSONB, NOT NULL), `status` (string, NOT NULL, default 'PENDING'), `created_at` (timestamp, NOT NULL, default now()), `processed_at` (timestamp, nullable), `published_at` (timestamp, nullable), `retry_count` (integer, default 0), `error_message` (text, nullable), `tenant_id` (integer, NOT NULL), `branch_id` (integer, NOT NULL).
- **OBX-002**: OutboxEvent rows MUST be written in the SAME database transaction as the business data change. This is NON-NEGOTIABLE -- it's the entire point of the outbox pattern.
- **OBX-003**: The outbox processor MUST be an asyncio background task that runs within the `rest_api` process (not a separate service for MVP).
- **OBX-004**: The processor MUST poll for `status = 'PENDING'` events ordered by `created_at ASC`, with a batch size of 50.
- **OBX-005**: Processing steps: (1) Set status to `PROCESSING` + `processed_at = now()`, (2) Publish to Redis Stream, (3) Set status to `PUBLISHED` + `published_at = now()`. Steps 1 and 3 are separate DB transactions.
- **OBX-006**: If publishing to Redis fails, the processor MUST increment `retry_count` and set `error_message`. After 3 failures, the status MUST be set to `DLQ`.
- **OBX-007**: The processor MUST poll every 100ms (configurable via `OUTBOX_POLL_INTERVAL_MS` env var).
- **OBX-008**: Events in `DLQ` status MUST NOT be retried automatically. They require manual intervention or an admin endpoint to retry.
- **OBX-009**: The system SHOULD archive (delete or move to archive table) `PUBLISHED` events older than 7 days.
- **OBX-010**: The outbox processor MUST be idempotent: if it crashes mid-processing, events in `PROCESSING` status for >60s MUST be reset to `PENDING` on restart (stale processing recovery).

### 1.5 Outbox Event Types

- **OBX-020**: The system MUST support the following event types:

| Event Type | Aggregate | When |
|-----------|-----------|------|
| `ROUND_SUBMITTED` | Round | Round created (PENDIENTE) |
| `ROUND_CONFIRMED` | Round | PENDIENTE -> CONFIRMADO |
| `ROUND_SENT_TO_KITCHEN` | Round | CONFIRMADO -> ENVIADO |
| `ROUND_IN_KITCHEN` | Round | ENVIADO -> EN_COCINA (auto) |
| `ROUND_READY` | Round | EN_COCINA -> LISTO (auto) |
| `ROUND_SERVED` | Round | LISTO -> SERVIDO |
| `ROUND_CANCELLED` | Round | Any -> CANCELADO |
| `KITCHEN_TICKET_CREATED` | KitchenTicket | Ticket created on fragmentation |
| `KITCHEN_TICKET_STARTED` | KitchenTicket | PENDIENTE -> EN_PROGRESO |
| `KITCHEN_TICKET_COMPLETED` | KitchenTicket | EN_PROGRESO -> LISTO |
| `KITCHEN_TICKET_DELIVERED` | KitchenTicket | LISTO -> ENTREGADO |
| `KITCHEN_TICKET_CANCELLED` | KitchenTicket | Any -> CANCELADO |
| `CHECK_REQUESTED` | Check | (future sprint, reserved) |
| `PAYMENT_CREATED` | Payment | (future sprint, reserved) |
| `PAYMENT_COMPLETED` | Payment | (future sprint, reserved) |
| `PAYMENT_FAILED` | Payment | (future sprint, reserved) |
| `SERVICE_CALL_CREATED` | ServiceCall | (future sprint, reserved) |

### 1.6 Redis Streams Spec

- **RS-001**: The system MUST use a single Redis Stream per branch: key `stream:branch:{branch_id}:events`.
- **RS-002**: Each stream entry MUST contain: `event_type`, `aggregate_type`, `aggregate_id`, `payload` (JSON string), `tenant_id`, `branch_id`, `timestamp`.
- **RS-003**: The WS Gateway MUST create a consumer group `ws-gateway-group` on each branch stream.
- **RS-004**: Each WS Gateway instance MUST have a unique consumer name: `ws-gw-{instance_id}`.
- **RS-005**: Consumers MUST acknowledge (XACK) messages after successful broadcast to all target WebSocket connections.
- **RS-006**: If a consumer fails to ACK within 30 seconds, another consumer in the group MUST reclaim the message via XAUTOCLAIM.
- **RS-007**: After 3 delivery attempts (tracked via delivery count in pending entries list), the message MUST be moved to a DLQ stream: `dlq:branch:{branch_id}:events`.
- **RS-008**: The WS Gateway MUST process stream entries in order per branch. Out-of-order delivery MUST NOT occur for the same aggregate.
- **RS-009**: XREADGROUP MUST use `BLOCK 5000` (5 second blocking read) to reduce polling overhead.
- **RS-010**: On startup, the WS Gateway MUST reclaim any pending messages older than 30s (XAUTOCLAIM) before starting normal consumption.

### 1.7 WebSocket Broadcast Spec

- **BC-001**: The WS Gateway MUST maintain a connection registry mapping: `branch_id -> role -> scope -> Set[WebSocket]`.
- **BC-002**: The broadcast pool MUST have 10 worker coroutines consuming from an `asyncio.Queue(maxsize=5000)`.
- **BC-003**: When the queue is full, the producer MUST log a warning and drop the oldest message (not block).
- **BC-004**: Each worker MUST: (1) Dequeue a broadcast task, (2) Resolve target connections from the routing matrix, (3) Send JSON payload to each connection, (4) Handle disconnected sockets gracefully (remove from registry, don't crash).
- **BC-005**: The broadcast target latency MUST be <200ms p95 for 400 concurrent WebSocket connections.
- **BC-006**: The WS Gateway MUST expose a `/ws/health` endpoint returning connection count, queue depth, and worker status.
- **BC-007**: Each WebSocket connection MUST authenticate via JWT token passed as query parameter: `ws://host:8001/ws?token={jwt}`.
- **BC-008**: On connection, the gateway MUST decode the JWT, extract `user_id`, `tenant_id`, `branch_id`, `role`, and register the connection in the appropriate registry slot.
- **BC-009**: On disconnect, the connection MUST be removed from the registry within 1 second.
- **BC-010**: The gateway MUST send a periodic ping (every 30s) to detect stale connections. Connections that don't respond within 10s MUST be terminated.

### 1.8 Event Routing Matrix

- **RT-001**: The system MUST route events according to this matrix:

| Event Type | Recipients | Scope |
|-----------|-----------|-------|
| `ROUND_SUBMITTED` | admin, manager, all waiters | branch-wide |
| `ROUND_CONFIRMED` | admin, manager, sector waiters | sector of table |
| `ROUND_SENT_TO_KITCHEN` | admin, manager, kitchen, sector waiters, diners at table | sector + table |
| `ROUND_IN_KITCHEN` | admin, manager, kitchen, sector waiters, diners at table | sector + table |
| `ROUND_READY` | admin, manager, kitchen, sector waiters, diners at table | sector + table |
| `ROUND_SERVED` | admin, manager, sector waiters, diners at table | sector + table |
| `ROUND_CANCELLED` | admin, manager, kitchen (if was EN_COCINA), sector waiters, diners at table | sector + table |
| `KITCHEN_TICKET_CREATED` | admin, manager, kitchen (target station) | station |
| `KITCHEN_TICKET_STARTED` | admin, manager, kitchen (target station) | station |
| `KITCHEN_TICKET_COMPLETED` | admin, manager, kitchen (all), sector waiters | station + sector |
| `KITCHEN_TICKET_DELIVERED` | admin, manager | branch-wide |
| `KITCHEN_TICKET_CANCELLED` | admin, manager, kitchen (target station) | station |

- **RT-002**: "kitchen" role connections MUST be filterable by station. Kitchen displays register with a station parameter on connect.
- **RT-003**: "sector waiters" means waiters with active `WaiterSectorAssignment` for the sector containing the relevant table.
- **RT-004**: "diners at table" means WebSocket connections from the pwaMenu app associated with the current `TableSession`.

### 1.9 API Contracts

#### 1.9.1 Round Endpoints

- **API-001**: `POST /api/rounds` -- Create a new round for a table session.
  - Request body: `{ session_id: int, items: [{ product_id: int, quantity: int, notes?: string, diner_id: int }] }`
  - Response: `201 { id, round_number, session_id, status: "PENDIENTE", items: [...], created_at }`
  - Auth: Any authenticated diner in the session
  - Side effects: Captures prices, writes OutboxEvent(ROUND_SUBMITTED)

- **API-002**: `PATCH /api/rounds/{round_id}/transition` -- Transition round state.
  - Request body: `{ action: "confirm" | "send" | "serve" | "cancel", reason?: string }`
  - Response: `200 { id, status, updated_at }`
  - Auth: Role-gated per transition table (RSM-002)
  - Side effects: Writes OutboxEvent for the transition. On "send": creates KitchenTickets.

- **API-003**: `GET /api/rounds?session_id={id}&status={status}` -- List rounds with filters.
  - Response: `200 { items: [...], total, page, page_size }`
  - Auth: waiter (own sector), admin/manager (all), diner (own session)

- **API-004**: `GET /api/rounds/{round_id}` -- Get round with items and ticket status.
  - Response: `200 { id, round_number, status, items: [...], tickets: [...], created_at, updated_at }`
  - Auth: Same as API-003

#### 1.9.2 Kitchen Endpoints

- **API-010**: `GET /api/kitchen/tickets?station={station}&status={status}` -- List tickets for kitchen display.
  - Response: `200 { items: [{ id, round_id, station, status, items: [...], table_number, sector_name, created_at, started_at, elapsed_seconds }], total }`
  - Auth: kitchen, admin, manager

- **API-011**: `PATCH /api/kitchen/tickets/{ticket_id}/transition` -- Advance ticket state.
  - Request body: `{ action: "start" | "complete" }`
  - Response: `200 { id, status, started_at, completed_at }`
  - Auth: kitchen (own station), admin, manager
  - Side effects: Writes OutboxEvent. Auto-consolidates Round state (KT-006, KT-007).

- **API-012**: `GET /api/kitchen/dashboard` -- Aggregated dashboard data.
  - Response: `200 { pending_count, in_progress_count, completed_today, avg_prep_time_seconds, tickets: { pending: [...], in_progress: [...] } }`
  - Auth: kitchen, admin, manager

#### 1.9.3 Admin Orders Endpoints

- **API-020**: `GET /api/admin/orders/summary` -- Summary cards data.
  - Response: `200 { pending: int, in_kitchen: int, ready: int, total_today: int, avg_time_seconds: int }`
  - Auth: admin, manager

- **API-021**: `GET /api/admin/orders?status={status}&date_from={}&date_to={}&table_id={}&waiter_id={}&page={}&page_size={}` -- Filterable orders list.
  - Response: `200 { items: [...], total, page, page_size }`
  - Auth: admin, manager

#### 1.9.4 Round Confirmation (WebSocket Events)

- **WS-001**: `round:vote_request` -- Server -> diners at table. Payload: `{ round_id, proponent_id, items: [...], votes: { diner_id: status }, expires_at }`.
- **WS-002**: `round:vote` -- Client -> Server. Payload: `{ round_id, vote: "yes" | "no" | "retract" }`.
- **WS-003**: `round:vote_update` -- Server -> diners at table. Payload: `{ round_id, votes: { diner_id: status }, all_confirmed: bool, auto_send_at?: timestamp }`.
- **WS-004**: `round:submitted` -- Server -> diners at table. Payload: `{ round_id, round_number, status }`.
- **WS-005**: `round:cancelled` -- Server -> diners at table. Payload: `{ round_id, reason, cancelled_by }`.
- **WS-006**: `round:timeout` -- Server -> diners at table. Payload: `{ round_id, reason: "TIMEOUT" }`.

### 1.10 Confirmation Voting Protocol (Detailed)

- **VP-001**: When a diner taps "Confirm Round", the client sends a WebSocket message to the server initiating the vote.
- **VP-002**: The server creates a VotingSession (in-memory, Redis-backed) with: `round_id`, `proponent_id`, `diner_ids` (from TableSession), `votes: {}`, `expires_at: now() + 5min`, `status: VOTING`.
- **VP-003**: The server broadcasts `round:vote_request` to all diners in the table session.
- **VP-004**: Each diner's vote is recorded. When a diner votes YES, the server broadcasts `round:vote_update`.
- **VP-005**: If all diners vote YES: set `auto_send_at = now() + 1.5s`, broadcast `round:vote_update` with `all_confirmed: true, auto_send_at`.
- **VP-006**: During the 1.5s window, if any diner sends `vote: "retract"`, cancel the auto-send, remove their YES vote, broadcast updated state.
- **VP-007**: After 1.5s with all confirmed: submit round via API-001, broadcast `round:submitted`, delete VotingSession.
- **VP-008**: If timer expires (5min): cancel VotingSession, broadcast `round:timeout`, do NOT create a Round in DB.
- **VP-009**: If proponent sends cancel: cancel VotingSession, broadcast `round:cancelled`, do NOT create a Round in DB.
- **VP-010**: VotingSession data MUST be stored in Redis with TTL 6min (5min + 1min buffer): key `vote:{branch_id}:{table_session_id}:{round_draft_id}`.

### 1.11 Sound Notifications

- **SND-001**: pwaMenu MUST play an audio cue when receiving `round:vote_request` (if user is not the proponent).
- **SND-002**: pwaMenu MUST play a success audio cue when receiving `round:submitted`.
- **SND-003**: pwaMenu MUST play an alert audio cue when receiving `round:timeout` or `round:cancelled`.
- **SND-004**: Audio playback MUST respect the browser's autoplay policy. The app MUST request audio permission on first user interaction.
- **SND-005**: The kitchen dashboard MUST play an audio alert when a new ticket appears (KITCHEN_TICKET_CREATED event).

---

## 2. Scenarios (Given/When/Then)

### Scenario 1: Happy Path — Full Round Lifecycle
```
GIVEN a TableSession with 3 diners (Alice proponent, Bob, Carol)
  AND Alice has added 2 beers and 1 pizza to the round draft
WHEN Alice taps "Confirm Round"
THEN the server creates a VotingSession with expires_at = now() + 5min
  AND all 3 diners receive round:vote_request with item details
  AND Alice's vote is auto-YES (proponent)

WHEN Bob votes YES and then Carol votes YES
THEN after Carol's vote, auto_send_at = now() + 1.5s
  AND all diners receive round:vote_update with all_confirmed: true

WHEN 1.5 seconds elapse without retraction
THEN the system creates a Round with status PENDIENTE
  AND RoundItems capture current branch_product prices
  AND OutboxEvent(ROUND_SUBMITTED) is written atomically
  AND all diners receive round:submitted
  AND admin + all waiters receive ROUND_SUBMITTED via WebSocket
```

### Scenario 2: Vote Timeout
```
GIVEN a VotingSession with 3 diners, 1 has not voted
WHEN 5 minutes elapse
THEN the VotingSession is cancelled
  AND all diners receive round:timeout
  AND no Round is created in the database
```

### Scenario 3: Proponent Cancels
```
GIVEN an active VotingSession
WHEN the proponent sends cancel
THEN the VotingSession is cancelled
  AND all diners receive round:cancelled with reason "Proponent cancelled"
  AND no Round is created in the database
```

### Scenario 4: Vote Retraction During Auto-Send
```
GIVEN all diners have voted YES and auto_send_at is set
WHEN Bob retracts his vote within 1.5s
THEN auto_send_at is cleared
  AND Bob's vote is removed
  AND all diners receive round:vote_update with all_confirmed: false
  AND voting continues normally
```

### Scenario 5: Waiter Confirms Round
```
GIVEN a Round in PENDIENTE with round_number 1 for table 5 in sector "Salon"
  AND waiter Juan is assigned to sector "Salon"
WHEN Juan sends PATCH /api/rounds/{id}/transition { action: "confirm" }
THEN the Round transitions to CONFIRMADO
  AND OutboxEvent(ROUND_CONFIRMED) is written
  AND admin + sector waiters receive ROUND_CONFIRMED via WebSocket
```

### Scenario 6: Kitchen Ticket Fragmentation
```
GIVEN a Round in CONFIRMADO with items: 2x Beer (station: BAR), 1x Pizza (station: HORNO), 1x Salad (station: FRIA)
WHEN admin sends PATCH /api/rounds/{id}/transition { action: "send" }
THEN the Round transitions to ENVIADO
  AND 3 KitchenTickets are created:
    - Ticket A: station BAR, items [2x Beer]
    - Ticket B: station HORNO, items [1x Pizza]
    - Ticket C: station FRIA, items [1x Salad]
  AND OutboxEvent(ROUND_SENT_TO_KITCHEN) + 3x OutboxEvent(KITCHEN_TICKET_CREATED) are written
```

### Scenario 7: Auto-Consolidation to EN_COCINA
```
GIVEN a Round in ENVIADO with 3 KitchenTickets all in PENDIENTE
WHEN kitchen staff starts Ticket A (BAR)
THEN Ticket A -> EN_PROGRESO, started_at = now()
  AND Round auto-transitions to EN_COCINA
  AND OutboxEvent(KITCHEN_TICKET_STARTED) + OutboxEvent(ROUND_IN_KITCHEN) written
```

### Scenario 8: Auto-Consolidation to LISTO
```
GIVEN a Round in EN_COCINA with 3 KitchenTickets
  AND Tickets A and B are LISTO, Ticket C is EN_PROGRESO
WHEN kitchen staff completes Ticket C
THEN Ticket C -> LISTO, completed_at = now()
  AND Round auto-transitions to LISTO (all tickets LISTO)
  AND OutboxEvent(KITCHEN_TICKET_COMPLETED) + OutboxEvent(ROUND_READY) written
  AND admin + kitchen + sector waiters + diners receive notifications
```

### Scenario 9: Round Cancellation During Kitchen
```
GIVEN a Round in EN_COCINA with Ticket A (LISTO) and Ticket B (EN_PROGRESO)
WHEN admin cancels the round with reason "Client left"
THEN Round -> CANCELADO, cancelled_by = admin_id, cancel_reason = "Client left"
  AND Ticket B -> CANCELADO (Ticket A stays LISTO -- already completed)
  AND OutboxEvent(ROUND_CANCELLED) + OutboxEvent(KITCHEN_TICKET_CANCELLED) written
```

### Scenario 10: Outbox Processor Recovery
```
GIVEN an OutboxEvent in PROCESSING status with processed_at older than 60 seconds
WHEN the outbox processor starts (or runs its recovery check)
THEN the event's status is reset to PENDING
  AND the event is re-processed in the next polling cycle
```

### Scenario 11: Redis Streams DLQ
```
GIVEN a message in Redis Stream with delivery count = 3
WHEN a consumer attempts to claim it via XAUTOCLAIM
THEN the message is moved to the DLQ stream dlq:branch:{id}:events
  AND the message is acknowledged in the original stream
  AND the system logs a warning with the message details
```

### Scenario 12: Kitchen Dashboard — Urgency
```
GIVEN a KitchenTicket in EN_PROGRESO with started_at > 15 minutes ago
WHEN the kitchen dashboard renders the ticket card
THEN the card MUST have a red border (CSS class urgency-high)
  AND the elapsed time badge MUST show in red
```

### Scenario 13: Concurrent Ticket Completion Race
```
GIVEN a Round with 2 KitchenTickets, both EN_PROGRESO
WHEN both kitchen stations complete their ticket simultaneously
THEN only ONE consolidation check succeeds (SELECT FOR UPDATE prevents race)
  AND the Round transitions to LISTO exactly once
  AND exactly one ROUND_READY OutboxEvent is written
```

### Scenario 14: Unauthorized Transition
```
GIVEN a Round in PENDIENTE
WHEN a diner (not waiter) sends PATCH /api/rounds/{id}/transition { action: "confirm" }
THEN the system returns 403 Forbidden with error "Insufficient role for this transition"
  AND the Round state is unchanged
```

### Scenario 15: Broadcast Performance
```
GIVEN 400 concurrent WebSocket connections across 1 branch
WHEN an OutboxEvent is published to Redis Streams
THEN all target connections receive the event within 200ms (p95)
  AND the broadcast pool queue depth stays below 1000 during steady state
```
