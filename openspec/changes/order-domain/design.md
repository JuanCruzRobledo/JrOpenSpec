---
sprint: 8
artifact: design
status: complete
---

# SDD Design — Sprint 8: Rondas, Cocina y Outbox

## Status: APPROVED

---

## 1. Database Schema

### 1.1 Modified Tables

#### rounds (expand from Sprint 1 stub)
```sql
CREATE TABLE rounds (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    session_id INTEGER NOT NULL REFERENCES table_sessions(id),
    round_number INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    version INTEGER NOT NULL DEFAULT 1,          -- optimistic locking
    cancelled_by INTEGER REFERENCES users(id),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancel_reason VARCHAR(500),
    created_by INTEGER,                          -- audit (no FK per ADR-004)
    updated_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_rounds_session_number UNIQUE (session_id, round_number),
    CONSTRAINT ck_round_status CHECK (status IN ('PENDIENTE','CONFIRMADO','ENVIADO','EN_COCINA','LISTO','SERVIDO','CANCELADO'))
);

CREATE INDEX ix_rounds_session_status ON rounds(session_id, status);
CREATE INDEX ix_rounds_branch_status ON rounds(branch_id, status);
CREATE INDEX ix_rounds_created_at ON rounds(branch_id, created_at DESC);
```

#### round_items (expand from Sprint 1 stub)
```sql
CREATE TABLE round_items (
    id SERIAL PRIMARY KEY,
    round_id INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    diner_id INTEGER NOT NULL REFERENCES diners(id),
    quantity INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL,           -- captured at submission time
    notes VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_ri_quantity_positive CHECK (quantity > 0),
    CONSTRAINT ck_ri_unit_price_positive CHECK (unit_price_cents >= 0)
);

CREATE INDEX ix_round_items_round ON round_items(round_id);
```

#### kitchen_tickets (expand from Sprint 1 stub)
```sql
CREATE TABLE kitchen_tickets (
    id SERIAL PRIMARY KEY,
    round_id INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
    station VARCHAR(30) NOT NULL DEFAULT 'GENERAL',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_prep_time_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_kt_status CHECK (status IN ('PENDIENTE','EN_PROGRESO','LISTO','ENTREGADO','CANCELADO'))
);

CREATE INDEX ix_kt_station_status ON kitchen_tickets(station, status);
CREATE INDEX ix_kt_round ON kitchen_tickets(round_id);
CREATE INDEX ix_kt_created_at ON kitchen_tickets(created_at DESC);
```

#### kitchen_ticket_items (NEW junction table)
```sql
CREATE TABLE kitchen_ticket_items (
    id SERIAL PRIMARY KEY,
    kitchen_ticket_id INTEGER NOT NULL REFERENCES kitchen_tickets(id) ON DELETE CASCADE,
    round_item_id INTEGER NOT NULL REFERENCES round_items(id) ON DELETE CASCADE,

    CONSTRAINT uq_kti_ticket_item UNIQUE (kitchen_ticket_id, round_item_id)
);

CREATE INDEX ix_kti_ticket ON kitchen_ticket_items(kitchen_ticket_id);
```

### 1.2 New Tables

#### outbox_events
```sql
CREATE TABLE outbox_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    aggregate_type VARCHAR(30) NOT NULL,
    aggregate_id INTEGER NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT ck_outbox_status CHECK (status IN ('PENDING','PROCESSING','PUBLISHED','DLQ'))
);

CREATE INDEX ix_outbox_pending ON outbox_events(status, created_at ASC) WHERE status = 'PENDING';
CREATE INDEX ix_outbox_processing ON outbox_events(status, processed_at) WHERE status = 'PROCESSING';
CREATE INDEX ix_outbox_aggregate ON outbox_events(aggregate_type, aggregate_id);
CREATE INDEX ix_outbox_branch ON outbox_events(branch_id, created_at DESC);
```

### 1.3 Column Addition to Existing Tables

#### products -- add kitchen_station
```sql
ALTER TABLE products ADD COLUMN kitchen_station VARCHAR(30) NOT NULL DEFAULT 'GENERAL';
```

---

## 2. State Machine Diagrams

### 2.1 Round State Machine
```
                    ┌──────────────────────────────────────────────┐
                    │              CANCELADO                        │
                    │  (admin/manager, any state except SERVIDO)    │
                    └──────────────────────────────────────────────┘
                          ▲     ▲     ▲     ▲     ▲
                          │     │     │     │     │
    ┌──────────┐    ┌─────┴────┐  ┌──┴─────┐  ┌──┴───────┐  ┌──┴─────┐  ┌──────────┐
    │PENDIENTE │───►│CONFIRMADO│─►│ENVIADO  │─►│EN_COCINA │─►│ LISTO  │─►│ SERVIDO  │
    │          │    │          │  │         │  │          │  │        │  │          │
    │(submit)  │    │(waiter)  │  │(admin/  │  │(auto:    │  │(auto:  │  │(waiter)  │
    │          │    │          │  │ mgr)    │  │ 1st      │  │ all    │  │          │
    └──────────┘    └──────────┘  └─────────┘  │ ticket   │  │tickets │  └──────────┘
                                               │ starts)  │  │ done)  │
                                               └──────────┘  └────────┘
```

### 2.2 KitchenTicket State Machine
```
    ┌──────────┐     ┌───────────┐     ┌───────┐     ┌──────────┐
    │PENDIENTE │────►│EN_PROGRESO│────►│ LISTO │────►│ENTREGADO │
    │          │     │           │     │       │     │          │
    │(created) │     │(kitchen   │     │(kitch.│     │(auto:    │
    │          │     │ starts)   │     │ done) │     │round     │
    └────┬─────┘     └─────┬─────┘     └───┬───┘     │served)   │
         │                 │               │         └──────────┘
         │                 │               │
         ▼                 ▼               │
    ┌──────────────────────────────────────┘
    │  CANCELADO (cascade from Round cancellation)
    └──────────────────────────────────────
```

### 2.3 Outbox Event Lifecycle
```
    ┌─────────┐     ┌────────────┐     ┌───────────┐
    │ PENDING │────►│ PROCESSING │────►│ PUBLISHED │
    │         │     │            │     │           │
    └─────────┘     └──────┬─────┘     └───────────┘
         ▲                 │
         │                 │ (fail, retry < 3)
         └─────────────────┘
                           │
                           │ (fail, retry >= 3)
                           ▼
                      ┌─────────┐
                      │   DLQ   │
                      └─────────┘

    Recovery: PROCESSING + processed_at > 60s ago -> reset to PENDING
```

---

## 3. Outbox Processor Design

### 3.1 Architecture
```
rest_api process
├── FastAPI (uvicorn)
│   ├── Business endpoints (write OutboxEvent in same TX)
│   └── ...
└── Background Task (asyncio.create_task on startup)
    └── OutboxProcessor
        ├── poll_loop() -- every 100ms
        │   ├── SELECT ... WHERE status='PENDING' ORDER BY created_at LIMIT 50
        │   ├── For each event:
        │   │   ├── UPDATE status='PROCESSING', processed_at=now()
        │   │   ├── XADD to Redis Stream
        │   │   ├── On success: UPDATE status='PUBLISHED', published_at=now()
        │   │   └── On fail: INCREMENT retry_count, SET error_message
        │   │       └── If retry_count >= 3: SET status='DLQ'
        │   └── Commit batch
        └── recovery_loop() -- every 60s
            └── UPDATE status='PENDING' WHERE status='PROCESSING' AND processed_at < now()-60s
```

### 3.2 Idempotency
- Each OutboxEvent has a unique `id`. The Redis Stream entry includes `outbox_id` in the payload.
- Consumers can deduplicate by tracking processed `outbox_id` values (in a Redis SET with TTL 24h).
- The outbox processor uses `SELECT ... FOR UPDATE SKIP LOCKED` to prevent multiple processor instances from picking up the same event.

### 3.3 Code Structure
```python
# rest_api/app/services/outbox_processor.py

class OutboxProcessor:
    def __init__(self, session_factory, redis_client, poll_interval_ms=100):
        self._session_factory = session_factory
        self._redis = redis_client
        self._poll_interval = poll_interval_ms / 1000
        self._running = False

    async def start(self):
        self._running = True
        asyncio.create_task(self._poll_loop())
        asyncio.create_task(self._recovery_loop())

    async def stop(self):
        self._running = False

    async def _poll_loop(self):
        while self._running:
            await self._process_batch()
            await asyncio.sleep(self._poll_interval)

    async def _process_batch(self):
        async with self._session_factory() as session:
            events = await session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.status == 'PENDING')
                .order_by(OutboxEvent.created_at)
                .limit(50)
                .with_for_update(skip_locked=True)
            )
            for event in events.scalars():
                event.status = 'PROCESSING'
                event.processed_at = utc_now()
            await session.commit()

        for event in events_list:
            try:
                stream_key = f"stream:branch:{event.branch_id}:events"
                await self._redis.xadd(stream_key, {
                    'outbox_id': str(event.id),
                    'event_type': event.event_type,
                    'aggregate_type': event.aggregate_type,
                    'aggregate_id': str(event.aggregate_id),
                    'payload': json.dumps(event.payload),
                    'tenant_id': str(event.tenant_id),
                    'branch_id': str(event.branch_id),
                })
                async with self._session_factory() as session:
                    event.status = 'PUBLISHED'
                    event.published_at = utc_now()
                    await session.merge(event)
                    await session.commit()
            except Exception as e:
                async with self._session_factory() as session:
                    event.retry_count += 1
                    event.error_message = str(e)
                    if event.retry_count >= 3:
                        event.status = 'DLQ'
                    else:
                        event.status = 'PENDING'
                    await session.merge(event)
                    await session.commit()

    async def _recovery_loop(self):
        while self._running:
            async with self._session_factory() as session:
                cutoff = utc_now() - timedelta(seconds=60)
                await session.execute(
                    update(OutboxEvent)
                    .where(OutboxEvent.status == 'PROCESSING')
                    .where(OutboxEvent.processed_at < cutoff)
                    .values(status='PENDING')
                )
                await session.commit()
            await asyncio.sleep(60)
```

---

## 4. Redis Streams Topology

### 4.1 Stream Layout
```
Redis
├── stream:branch:1:events          -- Main event stream for branch 1
│   └── Consumer Group: ws-gateway-group
│       ├── Consumer: ws-gw-instance-1
│       └── Consumer: ws-gw-instance-2 (future scaling)
├── stream:branch:2:events          -- Main event stream for branch 2
│   └── Consumer Group: ws-gateway-group
│       └── Consumer: ws-gw-instance-1
├── dlq:branch:1:events             -- DLQ for branch 1
├── dlq:branch:2:events             -- DLQ for branch 2
├── vote:{branch_id}:{session_id}:{draft_id}  -- Voting sessions (TTL 6min)
└── outbox:dedup:{outbox_id}        -- Dedup set (TTL 24h)
```

### 4.2 Consumer Group Lifecycle
```
1. On WS Gateway startup:
   a. For each active branch:
      - XGROUP CREATE stream:branch:{id}:events ws-gateway-group $ MKSTREAM
        ($ = start from new messages; use 0 for replay-all on first deploy)
      - XAUTOCLAIM stream:branch:{id}:events ws-gateway-group {consumer} 30000 0-0
        (reclaim pending messages older than 30s)
   b. Start consumer loop per branch stream

2. Consumer loop (per branch):
   while running:
     entries = XREADGROUP GROUP ws-gateway-group {consumer}
                BLOCK 5000 COUNT 10
                STREAMS stream:branch:{id}:events >
     for entry in entries:
       try:
         route_and_broadcast(entry)
         XACK stream:branch:{id}:events ws-gateway-group entry.id
       except:
         # Will be reclaimed after 30s by XAUTOCLAIM
         log.error(...)

3. Reclaim loop (every 15s):
   pending = XAUTOCLAIM stream:branch:{id}:events ws-gateway-group {consumer} 30000 0-0
   for entry in pending:
     delivery_count = XPENDING_ENTRY ... delivery_count
     if delivery_count >= 3:
       XADD dlq:branch:{id}:events * {entry.fields}
       XACK stream:branch:{id}:events ws-gateway-group entry.id
     else:
       route_and_broadcast(entry)
       XACK ...
```

---

## 5. Broadcast Worker Pool Architecture

### 5.1 Architecture Diagram
```
Redis Stream Consumer
        │
        ▼
  ┌─────────────┐
  │ Event Router │  -- Resolves target connections from routing matrix
  │             │
  └──────┬──────┘
         │ BroadcastTask(connections, payload)
         ▼
  ┌──────────────────────────────────────┐
  │       asyncio.Queue(maxsize=5000)     │
  └──────────────────────────────────────┘
         │  │  │  │  │  │  │  │  │  │
         ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼
  ┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐
  │W1││W2││W3││W4││W5││W6││W7││W8││W9││W10│   -- 10 asyncio workers
  └──┘└──┘└──┘└──┘└──┘└──┘└──┘└──┘└──┘└──┘
         │
         ▼
  WebSocket connections (send JSON payload)
```

### 5.2 Connection Registry
```python
# ws_gateway/connection_registry.py

class ConnectionRegistry:
    """Thread-safe registry of WebSocket connections organized for fast routing."""

    def __init__(self):
        # branch_id -> role -> connections
        self._by_role: dict[int, dict[str, set[WebSocketConnection]]] = defaultdict(lambda: defaultdict(set))
        # branch_id -> sector_id -> role -> connections
        self._by_sector: dict[int, dict[int, dict[str, set[WebSocketConnection]]]] = ...
        # table_session_id -> connections (diners)
        self._by_session: dict[int, set[WebSocketConnection]] = defaultdict(set)
        # station -> connections (kitchen displays)
        self._by_station: dict[str, set[WebSocketConnection]] = defaultdict(set)
        # connection_id -> WebSocketConnection (for cleanup)
        self._all: dict[str, WebSocketConnection] = {}

    def register(self, conn: WebSocketConnection):
        """Add connection to all relevant indexes."""
        self._all[conn.id] = conn
        self._by_role[conn.branch_id][conn.role].add(conn)
        if conn.sector_id:
            self._by_sector[conn.branch_id][conn.sector_id][conn.role].add(conn)
        if conn.table_session_id:
            self._by_session[conn.table_session_id].add(conn)
        if conn.station:
            self._by_station[conn.station].add(conn)

    def unregister(self, conn_id: str):
        """Remove from all indexes. O(1) per index."""
        conn = self._all.pop(conn_id, None)
        if conn:
            self._by_role[conn.branch_id][conn.role].discard(conn)
            # ... remove from all indexes

    def get_by_role(self, branch_id: int, role: str) -> set[WebSocketConnection]: ...
    def get_by_sector(self, branch_id: int, sector_id: int, role: str) -> set[WebSocketConnection]: ...
    def get_by_session(self, table_session_id: int) -> set[WebSocketConnection]: ...
    def get_by_station(self, station: str) -> set[WebSocketConnection]: ...
    def get_admins_and_managers(self, branch_id: int) -> set[WebSocketConnection]:
        return self._by_role[branch_id]['admin'] | self._by_role[branch_id]['manager']
```

### 5.3 Event Router
```python
# ws_gateway/event_router.py

class EventRouter:
    """Resolves which connections should receive a given event."""

    ROUTING_TABLE = {
        'ROUND_SUBMITTED': lambda ctx: (
            ctx.admins_managers()
            | ctx.all_waiters()
        ),
        'ROUND_CONFIRMED': lambda ctx: (
            ctx.admins_managers()
            | ctx.sector_waiters()
        ),
        'ROUND_SENT_TO_KITCHEN': lambda ctx: (
            ctx.admins_managers()
            | ctx.kitchen_all()
            | ctx.sector_waiters()
            | ctx.table_diners()
        ),
        'ROUND_IN_KITCHEN': lambda ctx: (
            ctx.admins_managers()
            | ctx.kitchen_all()
            | ctx.sector_waiters()
            | ctx.table_diners()
        ),
        'ROUND_READY': lambda ctx: (
            ctx.admins_managers()
            | ctx.kitchen_all()
            | ctx.sector_waiters()
            | ctx.table_diners()
        ),
        'ROUND_SERVED': lambda ctx: (
            ctx.admins_managers()
            | ctx.sector_waiters()
            | ctx.table_diners()
        ),
        'ROUND_CANCELLED': lambda ctx: (
            ctx.admins_managers()
            | ctx.kitchen_if_was_in_kitchen()
            | ctx.sector_waiters()
            | ctx.table_diners()
        ),
        'KITCHEN_TICKET_CREATED': lambda ctx: (
            ctx.admins_managers()
            | ctx.kitchen_station()
        ),
        'KITCHEN_TICKET_STARTED': lambda ctx: (
            ctx.admins_managers()
            | ctx.kitchen_station()
        ),
        'KITCHEN_TICKET_COMPLETED': lambda ctx: (
            ctx.admins_managers()
            | ctx.kitchen_all()
            | ctx.sector_waiters()
        ),
        'KITCHEN_TICKET_DELIVERED': lambda ctx: (
            ctx.admins_managers()
        ),
        'KITCHEN_TICKET_CANCELLED': lambda ctx: (
            ctx.admins_managers()
            | ctx.kitchen_station()
        ),
    }

    def resolve(self, event_type: str, payload: dict, registry: ConnectionRegistry) -> set[WebSocketConnection]:
        resolver = self.ROUTING_TABLE.get(event_type)
        if not resolver:
            return set()
        ctx = RoutingContext(payload=payload, registry=registry)
        return resolver(ctx)
```

---

## 6. Sequence Diagrams

### 6.1 End-to-End Order Flow
```
Diner(pwaMenu)    WS Gateway    REST API     Database    Outbox Proc.   Redis Stream   Kitchen Display
   │                  │            │            │             │              │               │
   │ vote:confirm     │            │            │             │              │               │
   │─────────────────►│            │            │             │              │               │
   │                  │ broadcast vote_request  │             │              │               │
   │◄─────────────────│            │            │             │              │               │
   │                  │            │            │             │              │               │
   │ [all vote YES, 1.5s elapses] │            │             │              │               │
   │                  │            │            │             │              │               │
   │                  │ POST /api/rounds        │             │              │               │
   │                  │───────────►│            │             │              │               │
   │                  │            │ BEGIN TX   │             │              │               │
   │                  │            │──────────►│             │              │               │
   │                  │            │ INSERT Round (PENDIENTE) │              │               │
   │                  │            │ INSERT RoundItems        │              │               │
   │                  │            │ INSERT OutboxEvent       │              │               │
   │                  │            │ COMMIT    │             │              │               │
   │                  │            │──────────►│             │              │               │
   │                  │            │◄──────────│             │              │               │
   │                  │            │            │             │              │               │
   │                  │            │            │  poll 100ms │              │               │
   │                  │            │            │◄────────────│              │               │
   │                  │            │            │  PROCESSING │              │               │
   │                  │            │            │────────────►│              │               │
   │                  │            │            │             │ XADD         │               │
   │                  │            │            │             │─────────────►│               │
   │                  │            │            │             │ PUBLISHED    │               │
   │                  │            │            │◄────────────│              │               │
   │                  │            │            │             │              │               │
   │                  │            │            │             │   XREADGROUP │               │
   │                  │◄───────────│────────────│─────────────│──────────────│               │
   │                  │ route ROUND_SUBMITTED   │             │              │               │
   │                  │ -> admin + waiters      │             │              │               │
   │◄─────────────────│            │            │             │              │               │
   │                  │            │            │             │              │               │
   │ [waiter confirms, admin sends to kitchen]  │             │              │               │
   │                  │            │            │             │              │               │
   │                  │ PATCH /rounds/{id}/transition {send}  │              │               │
   │                  │───────────►│            │             │              │               │
   │                  │            │ BEGIN TX   │             │              │               │
   │                  │            │ UPDATE Round -> ENVIADO  │              │               │
   │                  │            │ INSERT KitchenTickets    │              │               │
   │                  │            │ INSERT OutboxEvents (4+) │              │               │
   │                  │            │ COMMIT    │             │              │               │
   │                  │            │            │             │              │               │
   │                  │            │            │ [outbox publishes]         │               │
   │                  │            │            │             │─────────────►│               │
   │                  │            │            │             │              │  XREADGROUP   │
   │                  │            │            │             │              │──────────────►│
   │                  │            │            │             │              │ TICKET_CREATED│
   │                  │            │            │             │              │               │
   │                  │            │            │             │              │  [kitchen     │
   │                  │            │            │             │              │   starts &    │
   │                  │            │            │             │              │   completes]  │
   │                  │            │            │             │              │               │
   │  [ROUND_READY broadcast to diners]        │             │              │               │
   │◄─────────────────│            │            │             │              │               │
```

### 6.2 Outbox Processing Sequence
```
OutboxProcessor         Database               Redis
    │                      │                      │
    │ SELECT WHERE PENDING │                      │
    │ FOR UPDATE SKIP LOCKED                      │
    │─────────────────────►│                      │
    │   events[]           │                      │
    │◄─────────────────────│                      │
    │                      │                      │
    │ UPDATE -> PROCESSING │                      │
    │─────────────────────►│                      │
    │   COMMIT             │                      │
    │─────────────────────►│                      │
    │                      │                      │
    │ loop each event:     │                      │
    │   XADD stream:branch:{id}:events            │
    │──────────────────────────────────────────────►
    │   OK (entry_id)      │                      │
    │◄─────────────────────────────────────────────│
    │                      │                      │
    │ UPDATE -> PUBLISHED  │                      │
    │─────────────────────►│                      │
    │   COMMIT             │                      │
    │─────────────────────►│                      │
    │                      │                      │
    │ [If XADD fails]     │                      │
    │   retry_count += 1   │                      │
    │   if >= 3: DLQ       │                      │
    │   else: PENDING      │                      │
    │─────────────────────►│                      │
```

### 6.3 KitchenTicket Lifecycle (Auto-Consolidation)
```
Kitchen Staff     REST API          Database               Redis (via Outbox)
    │                │                  │                      │
    │ PATCH ticket/1/transition {start} │                      │
    │───────────────►│                  │                      │
    │                │ BEGIN TX         │                      │
    │                │ SELECT ticket FOR UPDATE                │
    │                │─────────────────►│                      │
    │                │ UPDATE ticket -> EN_PROGRESO            │
    │                │ SET started_at = now()                  │
    │                │─────────────────►│                      │
    │                │                  │                      │
    │                │ SELECT round FOR UPDATE                 │
    │                │─────────────────►│                      │
    │                │ [round was ENVIADO, ticket started]     │
    │                │ UPDATE round -> EN_COCINA               │
    │                │─────────────────►│                      │
    │                │                  │                      │
    │                │ INSERT OutboxEvent(TICKET_STARTED)      │
    │                │ INSERT OutboxEvent(ROUND_IN_KITCHEN)    │
    │                │ COMMIT           │                      │
    │                │─────────────────►│                      │
    │                │                  │                      │
    │  200 OK        │                  │                      │
    │◄───────────────│                  │                      │
    │                │                  │   [outbox publishes] │
    │                │                  │─────────────────────►│
    │                │                  │                      │
    │ ... later: PATCH ticket/1/transition {complete}          │
    │───────────────►│                  │                      │
    │                │ BEGIN TX         │                      │
    │                │ UPDATE ticket -> LISTO, completed_at    │
    │                │ SELECT round FOR UPDATE                 │
    │                │ SELECT ALL tickets WHERE round_id = X   │
    │                │─────────────────►│                      │
    │                │ [all tickets LISTO? -> round -> LISTO]  │
    │                │ UPDATE round -> LISTO                   │
    │                │ INSERT OutboxEvent(TICKET_COMPLETED)    │
    │                │ INSERT OutboxEvent(ROUND_READY)         │
    │                │ COMMIT           │                      │
    │                │─────────────────►│                      │
```

### 6.4 Round Confirmation Voting
```
Diner A (proponent)   WS Gateway (Redis-backed)   Diner B         Diner C
    │                        │                        │               │
    │ ws:initiate_vote       │                        │               │
    │───────────────────────►│                        │               │
    │                        │ Create VotingSession   │               │
    │                        │ in Redis (TTL 6min)    │               │
    │                        │ Auto-vote A = YES      │               │
    │                        │                        │               │
    │ round:vote_request     │ round:vote_request     │ round:vote_req│
    │◄───────────────────────│───────────────────────►│──────────────►│
    │                        │                        │               │
    │                        │ ws:vote {yes}          │               │
    │                        │◄───────────────────────│               │
    │                        │ Update Redis           │               │
    │ round:vote_update      │ round:vote_update      │ round:vote_upd│
    │◄───────────────────────│───────────────────────►│──────────────►│
    │                        │                        │               │
    │                        │                    ws:vote {yes}       │
    │                        │◄──────────────────────────────────────│
    │                        │ ALL YES -> set auto_send_at           │
    │ vote_update            │ vote_update             │ vote_update  │
    │ {all_confirmed: true,  │ {auto_send_at: +1.5s}  │              │
    │  auto_send_at: ...}    │                         │              │
    │◄───────────────────────│────────────────────────►│─────────────►│
    │                        │                         │              │
    │        [1.5s elapses, no retraction]             │              │
    │                        │                         │              │
    │                        │ POST /api/rounds (internal)            │
    │                        │─────────────►REST API   │              │
    │                        │ 201 Created  │          │              │
    │                        │◄─────────────│          │              │
    │ round:submitted        │ round:submitted         │ submitted    │
    │◄───────────────────────│────────────────────────►│─────────────►│
```

---

## 7. Component Trees (Frontend)

### 7.1 Kitchen Dashboard (dashboard app)
```
KitchenDashboardPage
├── KitchenHeader
│   ├── StationSelector (dropdown: ALL / BAR / HORNO / FRIA / GENERAL)
│   ├── ConnectionStatus (WebSocket indicator)
│   └── SoundToggle (mute/unmute button)
├── KitchenColumns (flex row)
│   ├── KitchenColumn (title="Nuevos", status=PENDIENTE)
│   │   └── KitchenTicketCard[] (mapped from tickets)
│   │       ├── TableBadge (mesa #)
│   │       ├── ItemCount (qty items)
│   │       ├── ElapsedTime (badge, red if >15min)
│   │       └── onClick -> open KitchenTicketModal
│   └── KitchenColumn (title="En Preparacion", status=EN_PROGRESO)
│       └── KitchenTicketCard[] (sorted by elapsed time DESC)
├── KitchenTicketModal (overlay)
│   ├── TicketHeader (station, table, round #)
│   ├── TicketItemList
│   │   └── TicketItem[] (product name, qty, notes)
│   ├── ElapsedTimer (live updating)
│   └── AdvanceButton ("Iniciar" | "Completar" based on status)
└── KitchenAudioManager (hidden, plays sounds on new tickets)
```

### 7.2 Admin Orders View (dashboard app)
```
AdminOrdersPage
├── OrdersSummaryCards (grid 4 cols)
│   ├── SummaryCard (title="Pendientes", count, icon, color=yellow)
│   ├── SummaryCard (title="En Cocina", count, icon, color=blue)
│   ├── SummaryCard (title="Listos", count, icon, color=green)
│   └── SummaryCard (title="Total Hoy", count, icon, color=gray)
├── ViewToggle (Kanban | Grid)
├── [if Kanban]
│   └── OrdersKanban (flex row)
│       ├── KanbanColumn (title="Pendientes", statuses=[PENDIENTE, CONFIRMADO])
│       │   └── RoundCard[] (round #, table, items, time, waiter)
│       ├── KanbanColumn (title="En Cocina", statuses=[ENVIADO, EN_COCINA])
│       │   └── RoundCard[]
│       └── KanbanColumn (title="Listos", statuses=[LISTO])
│           └── RoundCard[]
├── [if Grid]
│   └── OrdersGrid
│       ├── FilterBar
│       │   ├── StatusFilter (multi-select)
│       │   ├── DateRangeFilter
│       │   ├── TableFilter (dropdown)
│       │   └── WaiterFilter (dropdown)
│       └── DataTable (columns: #, Mesa, Items, Estado, Mozo, Tiempo, Acciones)
└── RoundDetailModal
    ├── RoundHeader (round #, table, session, status badge)
    ├── RoundItemList (product, qty, price, diner, notes)
    ├── TicketStatusList (per-station ticket progress)
    └── ActionButtons (Confirmar | Enviar | Cancelar -- role-gated)
```

### 7.3 RoundConfirmationPanel (pwaMenu)
```
RoundConfirmationPanel (bottom sheet / modal)
├── ConfirmationHeader
│   ├── Title ("Confirmar Ronda")
│   └── TimerBadge (countdown from 5:00)
├── VoterList
│   └── VoterRow[] (for each diner)
│       ├── DinerAvatar
│       ├── DinerName
│       └── VoteStatus (icon: pending / confirmed / declined)
├── ItemSummary (collapsible)
│   └── ItemRow[] (product, qty, price)
│   └── TotalRow (sum of all items)
├── [if all_confirmed]
│   └── AutoSendCountdown (1.5s progress bar + "Enviando en X.Xs...")
├── ActionButtons
│   ├── ConfirmButton ("Confirmo" -- for non-proponent diners who haven't voted)
│   ├── RetractButton ("Cancelar mi voto" -- for diners who voted YES, during countdown)
│   └── CancelRoundButton ("Cancelar Ronda" -- proponent only)
└── SoundManager (plays audio cues per SND-001..003)
```

---

## 8. File Structure (New/Modified Files)

```
shared/
├── shared/
│   ├── enums.py                          # ADD: RoundStatus, KitchenTicketStatus, OutboxEventStatus, OutboxEventType
│   ├── models/
│   │   ├── orders/
│   │   │   ├── round.py                  # MODIFY: expand from stub, add version, cancel fields
│   │   │   ├── round_item.py             # MODIFY: expand, add diner_id, unit_price_cents, notes
│   │   │   ├── kitchen_ticket.py         # MODIFY: expand, add station, timestamps
│   │   │   └── kitchen_ticket_item.py    # NEW: junction table
│   │   ├── outbox/
│   │   │   ├── __init__.py               # NEW
│   │   │   └── outbox_event.py           # NEW: OutboxEvent model
│   │   ├── catalog/
│   │   │   └── product.py                # MODIFY: add kitchen_station column
│   │   └── __init__.py                   # MODIFY: register new models
│   └── repositories/
│       ├── round_repo.py                 # NEW
│       ├── kitchen_ticket_repo.py        # NEW
│       └── outbox_repo.py                # NEW

rest_api/
├── app/
│   ├── main.py                           # MODIFY: register new routers, start outbox processor
│   ├── routers/
│   │   ├── rounds.py                     # NEW: Round CRUD + transition endpoints
│   │   ├── kitchen.py                    # NEW: Kitchen ticket endpoints + dashboard
│   │   └── admin_orders.py              # NEW: Admin orders summary + list
│   ├── services/
│   │   ├── round_service.py             # NEW: Round state machine, price capture, fragmentation
│   │   ├── kitchen_service.py           # NEW: Ticket transitions, auto-consolidation
│   │   ├── outbox_service.py            # NEW: Helper to create OutboxEvents
│   │   └── outbox_processor.py          # NEW: Background outbox processor
│   └── schemas/
│       ├── round_schemas.py             # NEW: Pydantic request/response models
│       ├── kitchen_schemas.py           # NEW
│       └── admin_order_schemas.py       # NEW

ws_gateway/
├── main.py                               # MODIFY: Full implementation
├── connection_registry.py                # NEW: WebSocket connection index
├── event_router.py                       # NEW: Event -> connection mapping
├── broadcast_pool.py                     # NEW: Worker pool for sending
├── stream_consumer.py                    # NEW: Redis Streams consumer
├── voting_manager.py                     # NEW: Round voting protocol handler
├── models.py                             # NEW: WebSocketConnection dataclass
└── health.py                             # NEW: /ws/health endpoint

pwa_menu/src/
├── components/
│   ├── round/
│   │   ├── RoundConfirmationPanel.tsx    # NEW
│   │   ├── VoterList.tsx                 # NEW
│   │   ├── VoterRow.tsx                  # NEW
│   │   ├── AutoSendCountdown.tsx         # NEW
│   │   └── ItemSummary.tsx               # NEW
│   └── shared/
│       └── SoundManager.tsx              # NEW
├── hooks/
│   ├── useVoting.ts                      # NEW: Voting protocol WebSocket hook
│   └── useSound.ts                       # NEW: Audio playback hook
├── stores/
│   └── roundStore.ts                     # NEW: Zustand store for round/voting state
├── services/
│   └── roundApi.ts                       # NEW: API client for round endpoints
└── assets/
    └── sounds/
        ├── vote-request.mp3              # NEW
        ├── round-submitted.mp3           # NEW
        └── alert.mp3                     # NEW

dashboard/src/
├── pages/
│   ├── KitchenDashboardPage.tsx          # NEW
│   └── AdminOrdersPage.tsx              # NEW
├── components/
│   ├── kitchen/
│   │   ├── KitchenHeader.tsx             # NEW
│   │   ├── KitchenColumn.tsx             # NEW
│   │   ├── KitchenTicketCard.tsx         # NEW
│   │   ├── KitchenTicketModal.tsx        # NEW
│   │   ├── KitchenAudioManager.tsx       # NEW
│   │   └── StationSelector.tsx           # NEW
│   └── orders/
│       ├── OrdersSummaryCards.tsx         # NEW
│       ├── SummaryCard.tsx               # NEW
│       ├── OrdersKanban.tsx              # NEW
│       ├── KanbanColumn.tsx              # NEW
│       ├── RoundCard.tsx                 # NEW
│       ├── OrdersGrid.tsx               # NEW
│       ├── FilterBar.tsx                 # NEW
│       └── RoundDetailModal.tsx          # NEW
├── hooks/
│   ├── useKitchenTickets.ts              # NEW: Kitchen ticket data + WebSocket
│   ├── useAdminOrders.ts                 # NEW: Admin orders data + WebSocket
│   └── useWebSocket.ts                   # MODIFY: Add event routing support
├── stores/
│   ├── kitchenStore.ts                   # NEW
│   └── ordersStore.ts                    # NEW
└── services/
    ├── kitchenApi.ts                     # NEW
    └── adminOrdersApi.ts                # NEW

alembic/versions/
└── XXX_sprint8_rounds_kitchen_outbox.py  # NEW: Migration
```

---

## 9. Zustand Store Design

### 9.1 Kitchen Store
```typescript
// dashboard/src/stores/kitchenStore.ts
interface KitchenState {
  tickets: Record<number, KitchenTicket>;
  selectedStation: string | null; // null = ALL
  selectedTicketId: number | null;
  isMuted: boolean;
}

interface KitchenActions {
  setTickets: (tickets: KitchenTicket[]) => void;
  upsertTicket: (ticket: KitchenTicket) => void;
  removeTicket: (id: number) => void;
  setSelectedStation: (station: string | null) => void;
  setSelectedTicket: (id: number | null) => void;
  toggleMute: () => void;
}

// Selectors (individual, per React 19 convention):
const usePendingTickets = () => useKitchenStore(s =>
  Object.values(s.tickets)
    .filter(t => t.status === 'PENDIENTE' && (!s.selectedStation || t.station === s.selectedStation))
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
);
```

### 9.2 Orders Store
```typescript
// dashboard/src/stores/ordersStore.ts
interface OrdersState {
  rounds: Record<number, Round>;
  summary: OrdersSummary | null;
  filters: OrdersFilters;
  viewMode: 'kanban' | 'grid';
  selectedRoundId: number | null;
  pagination: { page: number; pageSize: number; total: number };
}

interface OrdersActions {
  setRounds: (rounds: Round[], total: number) => void;
  upsertRound: (round: Round) => void;
  setSummary: (summary: OrdersSummary) => void;
  setFilters: (filters: Partial<OrdersFilters>) => void;
  setViewMode: (mode: 'kanban' | 'grid') => void;
  setSelectedRound: (id: number | null) => void;
  setPage: (page: number) => void;
}
```

### 9.3 Round/Voting Store (pwaMenu)
```typescript
// pwa_menu/src/stores/roundStore.ts
interface RoundState {
  currentVote: VotingSession | null;
  rounds: Round[];
  isSubmitting: boolean;
}

interface VotingSession {
  roundDraftId: string;
  proponentId: number;
  items: RoundItemDraft[];
  votes: Record<number, 'pending' | 'yes' | 'no' | 'retracted'>;
  expiresAt: string;
  autoSendAt: string | null;
  allConfirmed: boolean;
}

interface RoundActions {
  setVotingSession: (session: VotingSession | null) => void;
  updateVotes: (votes: Record<number, string>, allConfirmed: boolean, autoSendAt?: string) => void;
  setRounds: (rounds: Round[]) => void;
  upsertRound: (round: Round) => void;
  setSubmitting: (v: boolean) => void;
  clearVoting: () => void;
}
```

---

## 10. Trade-offs Considered

| Decision | Alternative | Why Rejected |
|----------|------------|--------------|
| Outbox in same DB | Kafka/RabbitMQ for events | External broker adds infra complexity for MVP; outbox guarantees atomicity without 2PC |
| Redis Streams | Redis Pub/Sub | Pub/Sub is fire-and-forget, no persistence, no consumer groups, no retry |
| Single stream per branch | Single global stream | Per-branch isolation prevents cross-branch message leakage; simpler consumer logic |
| Asyncio worker pool | Thread pool | FastAPI/WS Gateway are async; mixing threads adds complexity. Asyncio workers share event loop. |
| Voting in Redis (not DB) | Voting in PostgreSQL | Voting is ephemeral (max 6min), high-frequency updates -- Redis is faster and TTL auto-cleans |
| 10 workers fixed | Auto-scaling pool | Fixed pool is predictable; 10 workers handle 400 users easily. Scale later if needed. |
| Kitchen station on product | Separate station-product mapping table | Over-engineering for MVP; one station per product covers 95% of cases |
| `SELECT FOR UPDATE` on Round | Application-level distributed lock | DB-level locking is simpler, correct, and sufficient for single-DB architecture |
| Optimistic locking (version col) | Pessimistic locking everywhere | Optimistic is lighter for the common non-contention case; pessimistic only for consolidation |
| Sound via Web Audio API | Push notifications | Push requires service worker registration, permission dialogs; audio is immediate in-app |
