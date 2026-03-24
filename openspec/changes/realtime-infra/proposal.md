---
sprint: 7
artifact: proposal
status: complete
---

# SDD Proposal -- Sprint 7: WebSocket Gateway + Carrito Compartido

## Status: APPROVED

## Executive Summary

Sprint 7 delivers the real-time communication backbone: a standalone WebSocket Gateway service (:8001) with role-based endpoints, multi-dimensional connection management, sharded locking, and Redis Pub/Sub event routing. On top of that, a shared cart system for the pwaMenu allows multiple diners at a table to collaboratively build an order with optimistic UI updates, automatic conflict resolution, and resilient reconnection.

## Key Components

### WebSocket Gateway (ws_gateway/)
- Standalone FastAPI on port 8001
- 4 endpoints: /ws/waiter, /ws/kitchen, /ws/admin, /ws/diner
- Auth: JWT for staff (5min revalidation), HMAC table token for diners (30min revalidation)
- Connection Manager: multi-dimensional indexes, sharded locks, max 1000 total / 3 per user
- Heartbeat: ping 30s, timeout 60s, 2-phase zombie cleanup
- Redis Pub/Sub: channels per branch/sector/session

### Shared Cart (pwaMenu)
- Modular tableStore (store.ts, selectors.ts, helpers.ts, types.ts)
- Optimistic updates with rollback on failure
- useCartSync hook with LRU cache (100 entries, 5s TTL)
- DinerWebSocket class: auto-reconnection (50 attempts, exponential backoff)

### Backend Cart Endpoints
- POST/PUT/DELETE /api/sessions/{id}/cart/items
- Cart events: CART_ITEM_ADDED/UPDATED/REMOVED/CLEARED

## Risks
- Connection memory leaks -> 2-phase cleanup cycle
- Race conditions in shared cart -> sharded locks + server-authoritative merge
- WS connection storms -> exponential backoff + debounced reconnect
- Redis Pub/Sub message loss -> full cart sync on reconnect

## Estimated: 12-16 sessions
