---
sprint: 7
artifact: tasks
status: complete
---

# SDD Tasks — Sprint 7: WebSocket Gateway + Carrito Compartido

## Status: APPROVED

---

## Phase 1: Gateway Infrastructure & Configuration

### Task 1.1: Gateway Project Setup
**Description**: Create the ws_gateway Python package with pyproject.toml, Dockerfile, and basic FastAPI app with lifespan.
**Files**:
- `ws_gateway/pyproject.toml` — Package definition with dependencies: fastapi, uvicorn, redis[hiredis], pydantic-settings
- `ws_gateway/Dockerfile` — Multi-stage build (same pattern as rest_api)
- `ws_gateway/ws_gateway/__init__.py` — Package init
- `ws_gateway/ws_gateway/main.py` — FastAPI app factory, lifespan handler (init Redis, start heartbeat/reauth/pubsub managers, cleanup on shutdown), health endpoint `GET /health` returning `{"status": "ok", "connections": count}`
- `ws_gateway/ws_gateway/config.py` — `GatewaySettings(BaseSettings)` with: `WS_MAX_CONNECTIONS=1000`, `WS_MAX_PER_USER=3`, `WS_HEARTBEAT_INTERVAL=30`, `WS_HEARTBEAT_TIMEOUT=60`, `WS_CLEANUP_INTERVAL=30`, `WS_ORIGIN_WHITELIST`, `WS_STAFF_REAUTH_SECONDS=300`, `WS_DINER_REAUTH_SECONDS=1800`, `WS_CONNECTION_RATE_LIMIT=10`, `WS_MESSAGE_RATE_LIMIT=30`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `TABLE_TOKEN_SECRET_KEY`
- `ws_gateway/ws_gateway/dependencies.py` — Dependency container holding references to ConnectionManager, HeartbeatManager, ReauthManager, RedisPubSubManager, auth strategies

**Acceptance Criteria**:
- `docker compose up gateway` starts on :8001
- `GET /health` returns 200 with connection count
- Health check passes in docker-compose
- Config loads from environment variables

### Task 1.2: Update Docker Compose
**Description**: Add gateway service to docker-compose.yml.
**Files**:
- `docker-compose.yml` — Add `gateway` service (port 8001, depends on postgres + redis healthy, volume mount shared/, environment variables from .env)
- `.env.example` — Add all new WS_* and CART_* variables

**Acceptance Criteria**:
- `docker compose up` starts all services including gateway
- Gateway waits for postgres and redis to be healthy
- Gateway health check works in compose

---

## Phase 2: WebSocket Auth Strategies

### Task 2.1: Auth Strategy Base + Staff JWT Strategy
**Description**: Implement the WebSocket auth strategy pattern with StaffJWTStrategy.
**Files**:
- `ws_gateway/ws_gateway/auth/__init__.py`
- `ws_gateway/ws_gateway/auth/strategy.py` — `WebSocketAuthStrategy` ABC with `authenticate(ws) -> AuthResult`, `revalidate(ws, metadata) -> bool`, `reauth_interval_seconds() -> int`. `StaffJWTStrategy` implementation: extract token from query param, decode JWT via shared jwt module, check Redis blacklist, validate role matches endpoint (`/ws/waiter` -> waiter/manager/admin, `/ws/kitchen` -> kitchen/chef/manager/admin, `/ws/admin` -> admin/manager/owner). `AuthResult` dataclass with all fields.

**Acceptance Criteria**:
- Valid JWT authenticates successfully, returns correct user_id/tenant_id/branch_id/role
- Expired JWT returns auth_failed error
- Blacklisted JTI returns auth_failed error
- Wrong role for endpoint returns auth_failed error
- Missing token returns auth_failed error
- Revalidation checks expiry + blacklist, returns bool

### Task 2.2: Diner Table Token Strategy
**Description**: Implement DinerTableTokenStrategy for diner authentication.
**Files**:
- `ws_gateway/ws_gateway/auth/strategy.py` — Add `DinerTableTokenStrategy`: extract table_token from query param, verify HMAC using shared hmac_token module, extract session_id/table_id/diner_id/tenant_id/branch_id, verify session status is active via DB query. Revalidation every 30min checks session still active.

**Acceptance Criteria**:
- Valid table token authenticates, returns session_id/table_id/diner_id
- Invalid HMAC signature returns auth_failed
- Token for closed/cancelled session returns session_not_active
- Revalidation returns False when session changes to closed

### Task 2.3: Origin Validator + Connection Rate Limiter
**Description**: Implement origin whitelist validation and per-IP connection rate limiting.
**Files**:
- `ws_gateway/ws_gateway/auth/origin.py` — `OriginValidator` class: takes whitelist from config, `is_allowed(origin: str | None) -> bool`, rejects None origin and non-whitelisted origins
- `ws_gateway/ws_gateway/auth/rate_limiter.py` — `WSConnectionRateLimiter`: sliding window in Redis (key: `ws:ratelimit:{ip}`, ZSET of timestamps), max 10 per minute per IP. `check(ip: str) -> bool`.

**Acceptance Criteria**:
- Whitelisted origin passes validation
- Non-whitelisted origin is rejected
- None origin is rejected
- 10th connection from same IP within 1 minute passes
- 11th connection from same IP within 1 minute is rejected (429)
- Rate limit window slides correctly (old entries expire)

---

## Phase 3: Connection Manager

### Task 3.1: ConnectionMetadata + ShardedLocks
**Description**: Implement ConnectionMetadata dataclass and ShardedLocks class.
**Files**:
- `ws_gateway/ws_gateway/core/__init__.py`
- `ws_gateway/ws_gateway/core/connection_manager.py` — `ConnectionMetadata` dataclass (user_id, diner_id, tenant_id, branch_id, role, session_id, table_id, sector_id, connected_at, last_heartbeat, last_reauth, auth_strategy, identity_key property). `ShardedLocks` class with global, user, branch, sector, session lock dictionaries using defaultdict(Lock), timeout-based acquisition.

**Acceptance Criteria**:
- ConnectionMetadata stores all required fields
- identity_key returns "user:{id}" for staff, "diner:{id}" for diners
- ShardedLocks creates locks on demand per key
- Lock acquisition respects timeout (raises TimeoutError after 5s)
- Different keys get different locks (sharding works)

### Task 3.2: ConnectionManager connect/disconnect
**Description**: Implement the full ConnectionManager with forward/inverse indexes and connect/disconnect operations.
**Files**:
- `ws_gateway/ws_gateway/core/connection_manager.py` — `ConnectionManager` class with: `__init__(max_total, max_per_user, lock_timeout)`, forward indexes (identity_connections, branch_connections, sector_waiters, session_diners), inverse indexes (ws_to_identity, ws_to_branch, ws_to_sector, ws_to_session, ws_to_metadata), `connect(ws, metadata) -> displaced WebSocket | None`, `disconnect(ws)`, `get_metadata(ws)`, `get_session_connections(session_id)`, `get_branch_connections(branch_id)`, `get_sector_connections(sector_id)`, `get_all_connections()`, `update_heartbeat(ws)`, `update_reauth(ws)`. Custom exceptions: `ServerFullError`, `LockTimeoutError`.

**Acceptance Criteria**:
- connect() adds to ALL forward and inverse indexes atomically
- connect() rejects with ServerFullError when total >= max_total
- connect() displaces oldest connection when user at max_per_user limit
- disconnect() removes from ALL indexes (idempotent -- calling twice doesn't error)
- get_session_connections returns only diners in that session
- get_branch_connections returns all connection types in that branch
- Lock acquisition follows order: global -> user -> branch -> sector/session
- After disconnect, WebSocket appears in NO index
- total_connections property matches actual count

---

## Phase 4: Heartbeat + Revalidation

### Task 4.1: HeartbeatManager
**Description**: Implement heartbeat ping loop and 2-phase zombie cleanup.
**Files**:
- `ws_gateway/ws_gateway/core/heartbeat.py` — `HeartbeatManager` class: `__init__(connection_manager, ping_interval=30, zombie_timeout=60, cleanup_interval=30)`, `start()` creates asyncio tasks for ping loop and cleanup loop, `stop()` cancels tasks. Ping loop: every ping_interval seconds, iterate all connections, send PING JSON message. Cleanup loop: every cleanup_interval seconds, Phase 1 (scan without locks, collect zombies where last_heartbeat > zombie_timeout), Phase 2 (acquire locks, re-verify timestamp, close with code 4004, disconnect from manager). Logs stats after cleanup.

**Acceptance Criteria**:
- PING messages sent every 30s to all connections
- Connections with no PONG for 60s identified as zombies
- Phase 2 re-verifies before closing (prevents race condition)
- Closed zombies are removed from ConnectionManager
- Close code is 4004 (heartbeat_timeout)
- Stats logged: identified count, closed count, remaining total

### Task 4.2: ReauthManager
**Description**: Implement periodic revalidation of auth for all connections.
**Files**:
- `ws_gateway/ws_gateway/core/reauth.py` — `ReauthManager` class: `__init__(connection_manager, auth_strategies dict, check_interval=60)`, `start()`, `stop()`. Loop: every check_interval seconds, iterate all connections, check if `now - last_reauth > strategy.reauth_interval_seconds()`, if due -> call `strategy.revalidate(ws, metadata)`, if valid -> update_reauth, if invalid -> close with 4001 (staff) or 4003 (diner) and disconnect.

**Acceptance Criteria**:
- Staff connections revalidated every 5 minutes
- Diner connections revalidated every 30 minutes
- Valid tokens extend reauth timestamp
- Invalid/blacklisted tokens close connection with correct code
- Closed sessions close diner connections with 4003

---

## Phase 5: Redis Pub/Sub

### Task 5.1: RedisPubSubManager
**Description**: Implement Redis Pub/Sub subscription management and message routing.
**Files**:
- `ws_gateway/ws_gateway/core/pubsub.py` — `RedisPubSubManager` class: `__init__(redis, connection_manager)`, `start()` creates listener task, `stop()` unsubscribes and closes, `subscribe_connection(metadata)` subscribes to channels (ws:branch:{id}, ws:sector:{id}, ws:session:{id}), `unsubscribe_connection(metadata)` unsubscribes if no more local subscribers on channel, `publish(channel, message)`. Listener loop: async for message in pubsub.listen(), parse JSON, route to local WebSockets via ConnectionManager. Route logic: branch -> get_branch_connections, sector -> get_sector_connections, session -> get_session_connections. Skip echo to sender (compare sender_id). Reconnection with exponential backoff on Redis failure.

**Acceptance Criteria**:
- Connections subscribe to correct channels on connect
- Connections unsubscribe on disconnect
- Empty channels are fully unsubscribed from Redis
- Published messages route to correct local WebSockets
- Messages are NOT echoed back to sender
- Redis disconnection handled gracefully (local-only mode)
- Redis reconnection resubscribes all active channels
- Published messages are JSON with correct envelope format

### Task 5.2: Event Types + Envelope Builder
**Description**: Define event type constants and a utility to build event envelopes.
**Files**:
- `ws_gateway/ws_gateway/events/__init__.py`
- `ws_gateway/ws_gateway/events/types.py` — Constants: `CONNECTED`, `ERROR`, `CART_ITEM_ADDED`, `CART_ITEM_UPDATED`, `CART_ITEM_REMOVED`, `CART_CLEARED`, `CART_SYNC`, `PING`. `build_envelope(type, payload, sender_id, session_id=None) -> dict` generates UUID id, ISO timestamp, assembles meta block.
- `shared/shared/events/__init__.py`
- `shared/shared/events/cart_events.py` — Same constants and `build_cart_event(type, payload, sender_id, session_id)` for use by REST API when publishing to Redis.

**Acceptance Criteria**:
- All event types defined as string constants
- build_envelope generates valid UUID for id
- build_envelope generates ISO 8601 timestamp
- Envelope matches the spec format: {type, payload, meta: {id, timestamp, sender_id, session_id}}

---

## Phase 6: WebSocket Endpoint Handlers

### Task 6.1: Diner Handler
**Description**: Implement the `/ws/diner` WebSocket endpoint handler.
**Files**:
- `ws_gateway/ws_gateway/handlers/__init__.py`
- `ws_gateway/ws_gateway/handlers/diner.py` — FastAPI WebSocket route `/ws/diner`. Flow: 1) Validate origin, 2) Check rate limit, 3) Accept WebSocket, 4) Authenticate with DinerTableTokenStrategy, 5) Build ConnectionMetadata, 6) ConnectionManager.connect() -> handle displaced/ServerFull/LockTimeout, 7) Subscribe to Pub/Sub channels, 8) Send CONNECTED message with session info + heartbeat_interval + reauth_interval, 9) Enter receive loop: handle PONG (update heartbeat), handle client messages. On disconnect: unsubscribe Pub/Sub, ConnectionManager.disconnect().

**Acceptance Criteria**:
- Valid table_token completes full connection flow
- Invalid token closes with 4001 before message loop
- CONNECTED message sent with correct payload
- PONG messages update last_heartbeat
- Clean disconnect removes from all indexes and unsubscribes channels
- Origin validation rejects non-whitelisted
- Rate limiting returns 429 on excess

### Task 6.2: Staff Handlers (Waiter, Kitchen, Admin)
**Description**: Implement the 3 staff WebSocket endpoint handlers.
**Files**:
- `ws_gateway/ws_gateway/handlers/waiter.py` — `/ws/waiter` handler, same pattern as diner but uses StaffJWTStrategy, subscribes to branch + sector channels
- `ws_gateway/ws_gateway/handlers/kitchen.py` — `/ws/kitchen` handler, subscribes to branch channel
- `ws_gateway/ws_gateway/handlers/admin.py` — `/ws/admin` handler, subscribes to branch channel

**Acceptance Criteria**:
- Each handler authenticates with StaffJWTStrategy
- Role validation: waiter endpoint accepts waiter/manager/admin roles, kitchen accepts kitchen/chef/manager/admin, admin accepts admin/manager/owner
- Waiter handler subscribes to branch + sector channels
- Kitchen handler subscribes to branch channel
- Admin handler subscribes to branch channel
- All send CONNECTED message with correct role-specific info
- All handle PONG for heartbeat
- All clean up properly on disconnect

### Task 6.3: Gateway Main — Wire Everything Together
**Description**: Wire all components together in main.py with lifespan.
**Files**:
- `ws_gateway/ws_gateway/main.py` — Update to: create ConnectionManager, HeartbeatManager, ReauthManager, RedisPubSubManager in lifespan startup. Store in app.state. Include all 4 WebSocket routers. Start all managers. On shutdown: stop all managers, close Redis.
- `ws_gateway/ws_gateway/dependencies.py` — FastAPI dependency functions to get ConnectionManager, PubSubManager, etc. from app.state.

**Acceptance Criteria**:
- All managers start on app startup
- All managers stop on app shutdown
- Health endpoint shows correct connection count
- All 4 WebSocket endpoints are accessible
- Dependencies inject correctly into handlers

---

## Phase 7: Cart Backend (Database + Repository + Service)

### Task 7.1: CartItem Model + Migration
**Description**: Create the cart_items database table.
**Files**:
- `shared/shared/models/room/cart_item.py` — `CartItem(Base)` model: id SERIAL PK, session_id UUID FK->table_sessions(id) ON DELETE CASCADE, diner_id UUID NOT NULL, product_id INT FK->products(id), quantity INT NOT NULL CHECK > 0, notes TEXT nullable, modifiers JSONB default '[]', created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ. UniqueConstraint(session_id, diner_id, product_id). Indexes on session_id and (session_id, diner_id).
- `shared/shared/models/__init__.py` — Add CartItem import
- `shared/shared/models/room/__init__.py` — Add CartItem import
- `alembic/versions/XXX_add_cart_items.py` — Migration to create cart_items table

**Acceptance Criteria**:
- Migration creates cart_items table with all columns, constraints, indexes
- Unique constraint on (session_id, diner_id, product_id) works
- FK cascade: deleting a table_session deletes its cart_items
- quantity CHECK constraint rejects 0 and negative
- Migration is reversible (downgrade drops table)

### Task 7.2: Cart Repository
**Description**: Implement CartRepository with CRUD operations.
**Files**:
- `shared/shared/repositories/cart_repository.py` — `CartRepository`: `get_by_session(session_id) -> list[CartItem]`, `get_by_session_and_diner(session_id, diner_id) -> list[CartItem]`, `get_item(item_id) -> CartItem | None`, `find_existing(session_id, diner_id, product_id) -> CartItem | None`, `add_item(session_id, diner_id, product_id, quantity, notes, modifiers) -> CartItem` (upsert: if exists, increment quantity), `update_item(item_id, quantity=None, notes=None, modifiers=None) -> CartItem`, `remove_item(item_id) -> bool`, `clear_session(session_id) -> int` (returns count of items removed), `soft_delete_by_session(session_id)`.

**Acceptance Criteria**:
- get_by_session returns all items for a session with product relationship loaded
- find_existing correctly identifies composite key match
- add_item creates new if not exists, increments quantity if exists (upsert)
- update_item only updates provided fields (partial update)
- remove_item deletes the row (hard delete -- cart items are ephemeral)
- clear_session removes all items for a session, returns count
- All queries use selectinload for product relationship

### Task 7.3: Cart Pydantic Schemas
**Description**: Create request/response schemas for cart endpoints.
**Files**:
- `shared/shared/schemas/cart.py` — `CartItemAddRequest(BaseModel)`: product_id (int), diner_id (str UUID), quantity (int >= 1), notes (str | None, max 500), modifiers (list[ModifierInput] | None). `CartItemUpdateRequest`: quantity (int >= 1 | None), notes (str | None), modifiers (list[ModifierInput] | None). `ModifierInput`: modifier_id (int), option_id (int). `CartItemResponse(BaseModel)`: all CartItem fields + product_name, product_image_url, unit_price_cents, subtotal_cents. `CartResponse`: session_id, items list, by_diner dict, total_cents, item_count. `DinerCartSummary`: diner_id, display_name, items, subtotal_cents.
- `rest_api/app/schemas/cart.py` — Re-export from shared or define REST-specific variants if needed.

**Acceptance Criteria**:
- CartItemAddRequest validates quantity >= 1
- CartItemAddRequest validates notes max 500 chars
- CartItemAddRequest validates diner_id is valid UUID
- CartItemUpdateRequest allows all fields optional (partial update)
- CartItemResponse includes computed subtotal_cents
- CartResponse groups items by diner correctly

---

## Phase 8: Cart REST Endpoints

### Task 8.1: Cart Service
**Description**: Implement cart business logic with validation and event publishing.
**Files**:
- `rest_api/app/services/cart_service.py` — `CartService` class: `__init__(cart_repo, session_repo, product_repo, redis)`. Methods:
  - `add_item(session_id, input) -> CartItemResponse`: Validate session active, diner belongs to session, product exists and available in branch. Call cart_repo.add_item. Publish CART_ITEM_ADDED (or CART_ITEM_UPDATED if upsert) to `ws:session:{session_id}`.
  - `update_item(session_id, item_id, input, requester_diner_id) -> CartItemResponse`: Validate session active, item exists, requester owns item (or is staff). Call cart_repo.update_item. Publish CART_ITEM_UPDATED.
  - `remove_item(session_id, item_id, requester_diner_id)`: Validate session active, item exists, requester owns item (or is staff). Call cart_repo.remove_item. Publish CART_ITEM_REMOVED.
  - `get_cart(session_id) -> CartResponse`: Get all items, group by diner, calculate totals.
  - `clear_cart(session_id) -> int`: Staff only. Call cart_repo.clear_session. Publish CART_CLEARED.

**Acceptance Criteria**:
- add_item validates session is active, returns 409 if not
- add_item validates diner belongs to session, returns 403 if not
- add_item validates product exists and is available in branch, returns 400 if not
- add_item publishes correct event to Redis
- update_item validates ownership (diner can only update own items)
- remove_item validates ownership
- get_cart returns items grouped by diner with totals
- clear_cart is staff-only, publishes CART_CLEARED
- All mutations respect rate limit (10 per diner per minute)

### Task 8.2: Cart Router
**Description**: Implement cart REST endpoints.
**Files**:
- `rest_api/app/routers/cart.py` — FastAPI router with prefix `/api/sessions/{session_id}/cart`:
  - `POST /items` — Auth: table token or JWT with orders:write. Body: CartItemAddRequest. Returns 201 + CartItemResponse.
  - `PUT /items/{item_id}` — Auth: table token (owner) or JWT with orders:write. Body: CartItemUpdateRequest. Returns 200 + CartItemResponse.
  - `DELETE /items/{item_id}` — Auth: table token (owner) or JWT with orders:write. Returns 204.
  - `GET /` — Auth: table token or JWT with orders:read. Returns 200 + CartResponse.
  - `DELETE /` — Auth: JWT with orders:write only. Returns 204.
- `rest_api/app/main.py` — Include cart router

**Acceptance Criteria**:
- POST /items creates item, returns 201
- POST /items with existing composite key increments quantity, returns 200
- PUT /items/{id} updates item, returns 200
- DELETE /items/{id} removes item, returns 204
- GET / returns full cart with diner grouping
- DELETE / clears cart (staff only), returns 204
- Auth works for both table token and JWT
- Rate limiting returns 429
- Invalid session_id returns 404
- Inactive session returns 409

---

## Phase 9: Frontend — DinerWebSocket

### Task 9.1: WebSocket Types
**Description**: Define TypeScript types for WebSocket communication.
**Files**:
- `pwa_menu/src/lib/ws/types.ts` — `WSEventType` union type, `WSMessage<T>` generic interface (type, payload, meta with id/timestamp/sender_id/session_id), `ConnectionState` type ("connecting" | "connected" | "disconnected" | "reconnecting")

**Acceptance Criteria**:
- All event types from spec are included
- WSMessage is generic over payload type
- Types are exported and importable

### Task 9.2: DinerWebSocket Class
**Description**: Implement the DinerWebSocket client class with auto-reconnection.
**Files**:
- `pwa_menu/src/lib/ws/DinerWebSocket.ts` — `DinerWebSocket` class: constructor(DinerWebSocketConfig), connect(), disconnect(), on(type, handler) -> unsubscribe fn, onStateChange(callback) -> unsubscribe fn, getState(). Config: baseUrl, tableToken, maxReconnectAttempts=50, initialReconnectDelay=1000ms, maxReconnectDelay=30000ms, jitterPercent=0.2, heartbeatTimeout=40000ms. Internal: state management, reconnection with exponential backoff + jitter, heartbeat monitoring (reset timer on PING, close if no PING for heartbeatTimeout), message routing to registered handlers. No reconnect on code 1000 (normal) or 4003 (session closed).

**Acceptance Criteria**:
- connect() establishes WebSocket to /ws/diner?table_token=TOKEN
- State transitions: disconnected -> connecting -> connected
- PING messages reset heartbeat timer
- No PING for 40s triggers close(4004)
- onclose with code != 1000/4003 triggers reconnect
- Reconnection uses exponential backoff: 1s, 2s, 4s, 8s... up to 30s
- Jitter +/-20% applied to backoff delay
- Max 50 reconnect attempts, then state = disconnected
- on() registers handlers, returns unsubscribe function
- onStateChange notifies on every state transition
- disconnect() prevents further reconnection
- Multiple handlers for same event type all get called

---

## Phase 10: Frontend — Cart Store + Sync

### Task 10.1: Cart Types
**Description**: Define TypeScript types for the cart store.
**Files**:
- `pwa_menu/src/features/table/store/types.ts` — CartItem, CartItemInput, CartItemUpdate, ModifierSelection, DinerSummary, CartState (items, sessionId, diners, totalCents, isLoading, isSyncing, error, pendingMutations), CartActions (addItem, updateItem, removeItem, syncFromServer, handleRemoteEvent, initialize, reset), CartStore = CartState & CartActions

**Acceptance Criteria**:
- All types match the API contracts from spec
- CartItem matches server response shape
- CartItemInput matches POST request body
- CartStore combines state and actions

### Task 10.2: Cart Helpers
**Description**: Implement helper utilities for the cart store.
**Files**:
- `pwa_menu/src/features/table/store/helpers.ts` — `LRUCache<K,V>` class (maxSize=100, ttlMs=5000, get/set/clear methods), `mergeCartState(local, server) -> merged` (server-authoritative, keeps local temp IDs not on server), `generateTempId() -> negative number`, `calculateSubtotal(item) -> cents`, `createDinerSummaries(items) -> DinerSummary[]`

**Acceptance Criteria**:
- LRU cache evicts oldest when at capacity
- LRU cache respects TTL (expired entries return undefined)
- mergeCartState: server items take precedence, local-only temp items preserved
- generateTempId returns unique negative numbers
- calculateSubtotal includes modifier price deltas
- createDinerSummaries correctly groups and sums

### Task 10.3: Cart Selectors
**Description**: Implement memoized Zustand selectors.
**Files**:
- `pwa_menu/src/features/table/store/selectors.ts` — selectAllItems, selectItemsByDiner(dinerId), selectItemCount, selectTotalCents, selectDinerSummaries, selectDinerSubtotal(dinerId), selectIsLoading, selectIsSyncing, selectError, selectItemById(itemId), selectHasPendingMutations

**Acceptance Criteria**:
- Selectors return correct derived data
- selectItemsByDiner filters correctly
- selectItemCount sums quantities (not just array length)
- selectDinerSubtotal sums subtotal_cents for specific diner

### Task 10.4: Cart API Client
**Description**: Implement the cart REST API client.
**Files**:
- `pwa_menu/src/features/table/api/cartApi.ts` — `cartApi` object: `addItem(sessionId, input) -> CartItem`, `updateItem(sessionId, itemId, update) -> CartItem`, `removeItem(sessionId, itemId) -> void`, `getCart(sessionId) -> CartResponse`. Uses fetch with table_token in Authorization header. Base URL from environment config.

**Acceptance Criteria**:
- All methods hit correct endpoints with correct HTTP methods
- Request bodies match schema
- Auth header includes table token
- Error responses throw with meaningful message
- 201/200/204 responses handled correctly

### Task 10.5: Cart Store (Zustand)
**Description**: Implement the main Zustand store with optimistic updates.
**Files**:
- `pwa_menu/src/features/table/store/store.ts` — `useTableStore = create<CartStore>()` with initialState and all actions:
  - `addItem`: snapshot -> optimistic add (check existing for upsert) -> cartApi.addItem -> on success: replace temp -> on failure: rollback
  - `updateItem`: snapshot -> optimistic update -> cartApi.updateItem -> on success: merge server -> on failure: rollback
  - `removeItem`: snapshot -> optimistic remove -> cartApi.removeItem -> on success: clear pending -> on failure: rollback
  - `syncFromServer`: mergeCartState(local, server), recalculate totals
  - `handleRemoteEvent`: switch on event type, add/update/remove/clear items
  - `initialize`: set sessionId, clear items
  - `reset`: restore initialState

**Acceptance Criteria**:
- addItem updates UI immediately (optimistic)
- addItem with existing product increments quantity (upsert)
- Backend failure triggers rollback to snapshot
- Temp items get negative IDs, replaced by server IDs on success
- handleRemoteEvent correctly processes all 4 event types
- Remote CART_ITEM_ADDED doesn't duplicate if already in store
- syncFromServer uses server-authoritative merge
- pendingMutations tracked and cleaned up

### Task 10.6: useCartSync Hook
**Description**: Implement the cart sync hook that bridges WebSocket events and the store.
**Files**:
- `pwa_menu/src/features/table/hooks/useCartSync.ts` — `useCartSync(sessionId, dinerWs)`: initialize store, subscribe to WS events (CART_ITEM_ADDED/UPDATED/REMOVED/CLEARED/SYNC -> handleRemoteEvent/syncFromServer), subscribe to connection state changes (on "connected" -> debounce 1s -> fetch cart from API -> syncFromServer), LRU cache prevents redundant syncs, initial sync on mount, cleanup on unmount.

**Acceptance Criteria**:
- Store initialized with sessionId on mount
- WS events forwarded to store.handleRemoteEvent
- Reconnection triggers cart sync after 1s debounce
- LRU cache prevents sync if already synced within 5s
- Initial mount triggers sync
- All subscriptions cleaned up on unmount
- Multiple rapid reconnections don't cause multiple syncs (debounce)

---

## Phase 11: Frontend — Cart UI Components

### Task 11.1: Cart Components
**Description**: Implement cart UI components.
**Files**:
- `pwa_menu/src/features/table/components/CartPanel.tsx` — Main cart container. Uses useTableStore selectors. Shows cart items grouped by diner, total, loading/syncing states. Empty state when no items.
- `pwa_menu/src/features/table/components/CartItemCard.tsx` — Single cart item card: product name, image, quantity controls (+/-), notes, modifiers, subtotal, remove button. Calls store.updateItem on quantity change, store.removeItem on remove.
- `pwa_menu/src/features/table/components/DinerSection.tsx` — Section for a single diner's items. Header with diner name + subtotal. List of CartItemCard. Only allows editing own items.
- `pwa_menu/src/features/table/components/CartSummary.tsx` — Bottom summary: total items, total price, per-diner breakdown, "Pedir" button (disabled -- future sprint).
- `pwa_menu/src/features/table/components/ConnectionStatus.tsx` — Small indicator showing WebSocket state: green dot (connected), yellow pulsing (reconnecting), red dot (disconnected), syncing spinner.

**Acceptance Criteria**:
- CartPanel renders items grouped by diner
- CartItemCard allows quantity change and removal
- Diner can only edit their own items
- CartSummary shows correct totals
- ConnectionStatus reflects actual WS state
- Loading/syncing states shown appropriately
- Empty cart state is user-friendly
- Error toasts appear on mutation failure

---

## Phase 12: Integration & Logging

### Task 12.1: Structured Logging
**Description**: Add structured logging to the gateway.
**Files**:
- `ws_gateway/ws_gateway/middleware/__init__.py`
- `ws_gateway/ws_gateway/middleware/logging.py` — Configure structlog or standard logging with JSON format. Log events: connection_accepted, connection_rejected (reason), connection_disconnected, heartbeat_timeout, zombie_cleanup, reauth_failed, pubsub_error, pubsub_reconnected, rate_limit_exceeded.

**Acceptance Criteria**:
- All connection lifecycle events logged as structured JSON
- Log includes: timestamp, event name, identity, branch_id, role, total_connections
- Error events include stack trace
- Log level configurable via environment variable

### Task 12.2: Gateway Integration Test Setup
**Description**: Set up test infrastructure for gateway testing.
**Files**:
- `tests/ws_gateway/__init__.py`
- `tests/ws_gateway/conftest.py` — Fixtures: test FastAPI app with all managers, test Redis, test DB session, mock WebSocket connections, factory functions for JWT tokens and table tokens.
- `tests/ws_gateway/test_connection_manager.py` — Unit tests for ConnectionManager: connect, disconnect, limits, sharded locks, index consistency.
- `tests/ws_gateway/test_auth_strategies.py` — Unit tests for StaffJWTStrategy and DinerTableTokenStrategy.
- `tests/ws_gateway/test_heartbeat.py` — Unit tests for HeartbeatManager zombie detection.

**Acceptance Criteria**:
- Test fixtures create isolated test environment
- ConnectionManager tests verify all invariants from spec
- Auth strategy tests cover happy path and all error cases
- Heartbeat tests verify 2-phase cleanup correctness
- All tests pass independently and in CI

---

## Summary

| Phase | Tasks | Key Deliverables | Est. Sessions |
|-------|-------|------------------|---------------|
| 1 | 1.1, 1.2 | Gateway project + Docker | 2 |
| 2 | 2.1, 2.2, 2.3 | Auth strategies + origin + rate limit | 2 |
| 3 | 3.1, 3.2 | ConnectionManager with sharded locks | 2 |
| 4 | 4.1, 4.2 | Heartbeat + revalidation managers | 1-2 |
| 5 | 5.1, 5.2 | Redis Pub/Sub + event types | 1-2 |
| 6 | 6.1, 6.2, 6.3 | 4 WS handlers + wiring | 2 |
| 7 | 7.1, 7.2, 7.3 | CartItem model + repo + schemas | 1-2 |
| 8 | 8.1, 8.2 | Cart service + REST endpoints | 2 |
| 9 | 9.1, 9.2 | DinerWebSocket class | 1-2 |
| 10 | 10.1-10.6 | Cart store + sync hook | 3 |
| 11 | 11.1 | Cart UI components | 1-2 |
| 12 | 12.1, 12.2 | Logging + tests | 1-2 |
| **Total** | **25 tasks** | | **14-22 sessions** |

### Dependency Order

```
Phase 1 (infra)
  -> Phase 2 (auth)
    -> Phase 3 (conn manager)
      -> Phase 4 (heartbeat/reauth) --+
      -> Phase 5 (pubsub) ------------+
        -> Phase 6 (handlers) <-------+
          -> Phase 12 (logging/tests)

Phase 7 (cart model) -> Phase 8 (cart endpoints)

Phase 9 (DinerWebSocket) -> Phase 10 (cart store) -> Phase 11 (cart UI)

Phases 6, 8, 9 can run in PARALLEL once their dependencies are met.
```
