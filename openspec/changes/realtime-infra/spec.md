---
sprint: 7
artifact: spec
status: complete
---

# SDD Spec -- Sprint 7: WebSocket Gateway + Carrito Compartido

## Status: APPROVED

## 1. Requirements (67 requirements across 8 sections)

### 1.1 Gateway Service (WS-001 to WS-005)
- Independent FastAPI on :8001, 4 WS endpoints, shared/ imports, lifespan handler, /health

### 1.2 Authentication (AUTH-001 to AUTH-010)
- Staff: JWT in query param, revalidate 5min, close 4001 on failure
- Diner: HMAC table token, revalidate 30min, close 4003 on session closed
- Origin whitelist, rate limit 10 connections/IP/min, max 1000 total

### 1.3 Connection Manager (CONN-001 to CONN-009)
- Forward indexes: user->ws, branch->ws, sector->waiters, session->diners
- Inverse indexes: ws->user/branch/sector/session/metadata
- ConnectionMetadata: user_id, tenant_id, branch_id, role, session_id, table_id, etc.
- Per-user limit: 3 (oldest displaced with 4007)
- Sharded locks: global->user->branch->sector/session (5s timeout)

### 1.4 Heartbeat (HB-001 to HB-006)
- PING every 30s, PONG within 10s, zombie at 60s
- 2-phase cleanup: identify (no locks) + close (with locks, re-verify)

### 1.5 Redis Pub/Sub (REDIS-001 to REDIS-006)
- Channels: ws:branch:{id}, ws:sector:{id}, ws:session:{id}
- Graceful Redis failure handling + exponential backoff reconnect

### 1.6 Cart Operations (CART-001 to CART-008)
- REST endpoints: POST/PUT/DELETE /api/sessions/{id}/cart/items, GET/DELETE /cart
- Composite key: (session_id, diner_id, product_id) - upsert on duplicate
- Validation: session active, diner belongs, product available, quantity > 0
- Events published to session channel on each mutation

### 1.7 Cart Sync (SYNC-001 to SYNC-007)
- Optimistic updates with rollback
- LRU cache (100 entries, 5s TTL)
- Deduplication (300ms window)
- Reconnection sync debounced 1s
- DinerWebSocket: exponential backoff, 50 attempts, jitter 20%

### 1.8 Rate Limiting (RATE-001 to RATE-003)
- Connection: 10/IP/min, Messages: 30/conn/min, Cart: 10/diner/min

## 2. Protocol Specification
- Message envelope: { type, payload, meta: { id, timestamp, sender_id, session_id } }
- Close codes: 1000 (normal), 4001 (auth_failed), 4003 (session_closed), 4004 (heartbeat_timeout), 4007 (connection_replaced), 4008 (server_full), 4009 (rate_limited)
- Event types: CONNECTED, ERROR, CART_ITEM_ADDED/UPDATED/REMOVED, CART_CLEARED, CART_SYNC, PING

## 3. Event Payloads (7 detailed JSON schemas)

## 4. Cart REST API Contracts (5 endpoints with full request/response schemas)

## 5. Connection Manager Invariants (7 invariants)

## 6. Sharded Lock Protocol (connect + disconnect sequences)

## 7. Scenarios (12 total)
