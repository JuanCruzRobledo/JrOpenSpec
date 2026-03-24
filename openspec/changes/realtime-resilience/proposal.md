---
sprint: 12
artifact: proposal
status: complete
---

# Proposal: Resiliencia y Real-time Completo

## Intent

Harden the entire real-time infrastructure to gracefully handle adverse conditions: network failures, Redis outages, message floods, tab synchronization, and service shutdowns — ensuring transparent reconnection and zero data loss under all scenarios.

## Scope

### In Scope
- Redis Gateway circuit breaker: CLOSED → OPEN (5 failures) → SEMI_OPEN (30s, 3 probes)
- Message queue with 5k capacity and auto-discard on overflow with alert
- Global rate limiting: 20 msg/sec per connection (sliding window), 10 broadcast/sec
- Evasion penalty: 1-hour ban on repeated rate limit violations
- Lua scripts for atomic Redis rate limiting operations
- Backpressure system: Pub/Sub queue 5k auto-discard, batch 50 events/cycle, 30s timeout, discard tracker
- pwaMenu reconnection: DinerWebSocket 50 attempts, exponential backoff + jitter, OfflineQueue
- pwaWaiter reconnection: persistent queue, status banner, IndexedDB recovery
- Graceful shutdown: ordered task cancellation → worker stop (5s) → cache cleanup → Redis close → WS close (1001)
- Origin validation whitelist for WebSocket connections
- Custom WebSocket close codes: 4001 (auth), 4003 (forbidden), 4029 (rate limited)
- Dashboard tab synchronization via BroadcastChannel API
- Detailed health checks with subsystem status
- Prometheus metrics for all resilience subsystems

### Out of Scope
- Application-level caching strategies (Sprint 15)
- Horizontal scaling / load balancing
- Database failover / replication
- CDN configuration

## Modules

| Module | Description |
|--------|-------------|
| `circuit-breaker-redis` | Circuit breaker for Redis Gateway operations |
| `rate-limiting` | Global rate limiting with Lua scripts |
| `backpressure` | Queue management, batching, discard tracking |
| `reconnection-menu` | pwaMenu WebSocket reconnection + offline queue |
| `reconnection-waiter` | pwaWaiter WebSocket reconnection + persistent queue |
| `graceful-shutdown` | Ordered shutdown sequence |
| `security` | Origin validation, close codes |
| `sync-tabs` | Dashboard BroadcastChannel synchronization |
| `observability` | Health checks, Prometheus metrics |

## Approach

1. **Circuit breaker** for Redis Gateway — wrap all Redis Pub/Sub operations
2. **Rate limiting** with Lua scripts — atomic sliding window per connection + global broadcast limit
3. **Backpressure** system — bounded queues, batch processing, discard tracking with alerts
4. **pwaMenu reconnection** — exponential backoff + jitter, 50 attempts, offline queue replay
5. **pwaWaiter reconnection** — same + persistent IndexedDB queue, status banner
6. **Graceful shutdown** — ordered sequence ensuring no lost messages
7. **Origin validation** — whitelist-based, reject unknown origins
8. **Custom close codes** — semantic disconnect reasons for client handling
9. **BroadcastChannel** — sync Dashboard state across tabs
10. **Health checks** — per-subsystem status with degraded/unhealthy states
11. **Prometheus metrics** — counters, gauges, histograms for all resilience paths

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rate limiting too aggressive on busy nights | High — legitimate messages dropped | Configurable limits via env vars; per-connection tracking; generous defaults |
| Queue overflow during sustained high load | Medium — messages lost | 5k buffer is ~10 min of normal traffic; discard tracker alerts ops team |
| BroadcastChannel not supported in older browsers | Low — dashboard stale tabs | Feature detection; fallback to periodic polling |
| Graceful shutdown timeout exceeded | Medium — dirty state | Hard kill after 10s grace period; recovery on restart via outbox replay |
| Lua script errors in Redis | Medium — rate limiting fails | Fail-open policy: on Lua error, allow the request (prefer availability) |

## Rollback

- All resilience features are additive — removal restores previous (less resilient) behavior
- Circuit breaker can be disabled via config flag
- Rate limiting can be set to very high thresholds (effectively disabled)
- Graceful shutdown doesn't affect data — worst case is abrupt disconnect
- BroadcastChannel is progressive enhancement — removal just stops tab sync
- Metrics endpoints are independent — removal has no functional impact
