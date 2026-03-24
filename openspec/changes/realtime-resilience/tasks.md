---
sprint: 12
artifact: tasks
status: complete
---

# Tasks: Resiliencia y Real-time Completo

## Phase 1: Circuit Breaker — Redis Gateway

### 1.1 Redis circuit breaker implementation
- Implement `RedisCircuitBreaker` class wrapping all Redis Pub/Sub operations
- States: CLOSED (default), OPEN (after 5 failures), SEMI_OPEN (after 30s cooldown)
- SEMI_OPEN allows 3 probes; all succeed → CLOSED; any fails → OPEN
- Thread-safe with asyncio Lock
- Expose state, failure_count, metrics via properties
- **Files**: `gateway/circuit_breaker/redis_circuit_breaker.py`, `gateway/circuit_breaker/metrics.py`
- **AC**: State transitions correct under concurrent operations; metrics expose current state and counters

### 1.2 Local message queue (5k capacity)
- Implement `BoundedQueue` with capacity 5,000 messages
- FIFO eviction when full (discard oldest)
- Integrate with circuit breaker: queue messages when OPEN, flush on transition to CLOSED
- **Files**: `gateway/backpressure/bounded_queue.py`
- **AC**: Queue caps at 5k; oldest evicted on overflow; flush delivers all queued messages to Redis on recovery

### 1.3 Discard tracker & alerting
- Implement `DiscardTracker`: count discards per minute, track timestamps
- Alert when discard rate exceeds 5% of incoming messages in 1-minute window
- Expose Prometheus counter `ws_messages_discarded_total`
- **Files**: `gateway/backpressure/discard_tracker.py`
- **AC**: Discard count accurate; alert fires at 5% threshold; Prometheus counter increments

## Phase 2: Rate Limiting

### 2.1 Lua scripts for sliding window
- Write `sliding_window.lua`: atomic ZREMRANGEBYSCORE + ZCARD + ZADD in Redis sorted set
- Write `evasion_check.lua`: atomic violation counting + ban decision
- Load scripts at Gateway startup via SCRIPT LOAD, cache SHA hashes
- **Files**: `gateway/rate_limiting/lua_scripts/sliding_window.lua`, `gateway/rate_limiting/lua_scripts/evasion_check.lua`
- **AC**: Lua scripts execute atomically; sliding window correctly counts within time window; evasion triggers ban

### 2.2 Rate limiter class
- Implement `RateLimiter` class using Lua scripts
- Per-connection limit: 20 msg/sec (configurable via env)
- Global broadcast limit: 10/sec (configurable via env)
- Fail-open policy: on Redis error, allow the request
- **Files**: `gateway/rate_limiting/rate_limiter.py`, `gateway/rate_limiting/config.py`
- **AC**: Enforces per-connection and global limits; fail-open on Redis error; config from env vars

### 2.3 Evasion tracker & ban management
- Implement `EvasionTracker`: 10 violations in 5 min → 1-hour ban
- Use Redis key with TTL for ban state
- On ban: send close code 4029, disconnect, log event
- **Files**: `gateway/rate_limiting/evasion_tracker.py`
- **AC**: Ban triggered at threshold; close code 4029 sent; ban persists in Redis with correct TTL

## Phase 3: Backpressure

### 3.1 Batch processor
- Implement `BatchProcessor`: process 50 events per cycle from bounded queue
- 30-second timeout per cycle
- On timeout: log warning, skip remaining events in batch, continue
- **Files**: `gateway/backpressure/batch_processor.py`
- **AC**: Processes in batches of 50; timeout stops batch; next cycle starts fresh

### 3.2 Integrate backpressure with Pub/Sub subscriber
- Wire `BoundedQueue` + `BatchProcessor` + `DiscardTracker` into the Gateway's Pub/Sub subscriber
- Replace direct message handling with queue-based processing
- **Files**: Gateway main module, Pub/Sub subscriber (existing files)
- **AC**: Messages flow through bounded queue → batch processor; overflow tracked; no memory growth under load

## Phase 4: Frontend Reconnection

### 4.1 Shared backoff strategy
- Implement `BackoffStrategy` class: exponential backoff with jitter
- Config: base 1s, multiplier 2x, max 30s, jitter 0-500ms, max attempts 50
- **Files**: `pwaMenu/src/realtime/reconnection/BackoffStrategy.ts` (shared via copy or package)
- **AC**: Delay increases exponentially; jitter adds randomness; caps at 30s; stops at 50 attempts

### 4.2 pwaMenu DinerWebSocket reconnection
- Enhance `DinerWebSocket` with reconnection using `BackoffStrategy`
- On disconnect: start reconnection loop, activate OfflineQueue
- On reconnect: re-authenticate, request full sync, replay queue, deactivate OfflineQueue
- Connection status indicator in UI
- **Files**: `pwaMenu/src/realtime/DinerWebSocket.ts`, `pwaMenu/src/realtime/reconnection/ReconnectionManager.ts`, `pwaMenu/src/realtime/offline/OfflineQueue.ts`
- **AC**: Reconnects up to 50 times; queue replays on reconnect; status indicator updates; full sync after reconnect

### 4.3 pwaWaiter persistent reconnection
- Enhance `WaiterWebSocket` with reconnection (same backoff strategy)
- Build `PersistentQueue` backed by IndexedDB (survive page refresh)
- Build `QueueReplay` with conflict resolution: on 409/conflict, discard queued operation (server wins)
- Build `ConnectionBanner.tsx`: "Reconectando... (intento N/50)" with progress
- **Files**: `pwaWaiter/src/realtime/WaiterWebSocket.ts`, `pwaWaiter/src/realtime/reconnection/ReconnectionManager.ts`, `pwaWaiter/src/realtime/offline/PersistentQueue.ts`, `pwaWaiter/src/realtime/offline/QueueReplay.ts`, `pwaWaiter/src/components/ConnectionBanner.tsx`
- **AC**: Queue persists in IndexedDB; survives page refresh; conflicts resolved (server wins); banner shows attempt count

## Phase 5: Graceful Shutdown

### 5.1 Ordered shutdown sequence
- Implement `GracefulShutdown` class with ordered steps:
  1. Stop accepting connections
  2. Cancel async tasks (5s grace)
  3. Stop workers (outbox, retry)
  4. Flush Redis caches
  5. Close Redis connections
  6. Send WS close frame 1001 to all connections
  7. Close HTTP server
- 10-second total timeout → force exit
- Register SIGTERM + SIGINT handlers
- **Files**: `gateway/shutdown/graceful_shutdown.py`
- **AC**: Shutdown completes in order; all connections receive 1001; total time < 10s; force exit on timeout

## Phase 6: Security

### 6.1 Origin validation
- Implement `OriginValidator`: whitelist from `WS_ALLOWED_ORIGINS` env var (comma-separated)
- Check Origin header on WebSocket upgrade request
- Reject non-whitelisted origins with HTTP 403
- Development mode: allow all origins
- **Files**: `gateway/security/origin_validator.py`
- **AC**: Whitelisted origins accepted; non-whitelisted rejected with 403; dev mode allows all

### 6.2 Custom close codes
- Define close code constants: 4001 (auth), 4003 (forbidden), 4029 (rate limited)
- Use in all disconnect scenarios with appropriate reason messages
- Document in `close_codes.py` with docstrings explaining each
- Update all WebSocket disconnect points to use semantic codes
- **Files**: `gateway/security/close_codes.py`, updates to WS handler
- **AC**: Each disconnect scenario uses correct close code; client receives code + reason string

## Phase 7: Dashboard Tab Sync

### 7.1 BroadcastChannel wrapper
- Implement `BroadcastSync` class: create channel `buen-sabor-dashboard-{branchId}`
- Methods: `postEvent(event)`, `onEvent(callback)`, `close()`
- Feature detection: if `BroadcastChannel` not available, methods are no-ops
- **Files**: `dashboard/src/sync/BroadcastSync.ts`, `dashboard/src/sync/types.ts`
- **AC**: Events broadcast between tabs; feature detection prevents errors in old browsers

### 7.2 React hook & store integration
- Implement `useBroadcastSync` hook: subscribes to channel, dispatches to Zustand stores
- On WebSocket event: update local store AND post to BroadcastChannel
- On BroadcastChannel event: update local store only (no re-broadcast to avoid loops)
- **Files**: `dashboard/src/sync/useBroadcastSync.ts`, updates to Dashboard WebSocket handler
- **AC**: Two tabs stay in sync; no infinite broadcast loops; events propagate within 50ms

## Phase 8: Observability

### 8.1 Health check endpoints
- Implement `HealthChecker`: aggregates subsystem health checks
- Implement individual checks: PostgreSQL (SELECT 1), Redis (PING), circuit breaker (state check), retry queue (stuck items)
- Routes: GET /api/health/live (always 200), GET /api/health/ready (200 if all healthy, 503 if any unhealthy), GET /ws/health
- **Files**: `gateway/health/health_checker.py`, `gateway/health/checks/*.py`, `gateway/health/routes.py`
- **AC**: /live always 200; /ready 503 when any subsystem unhealthy; each check returns latency_ms; response schema matches spec

### 8.2 Prometheus metrics
- Set up prometheus_client registry with all defined metrics
- Implement collectors: WS (messages, errors, connections), DB (pool stats), Redis (pool stats)
- Instrument: message processing (latency histogram), broadcast (duration histogram), HTTP requests (duration)
- Expose on GET /metrics in Prometheus text format
- **Files**: `gateway/metrics/prometheus.py`, `gateway/metrics/collectors/*.py`, `gateway/metrics/routes.py`
- **AC**: All counters, gauges, histograms exposed; labels correct; /metrics returns valid Prometheus format

## Phase 9: Integration Testing

### 9.1 Resilience integration tests
- Test circuit breaker: simulate Redis failure → OPEN → recovery → CLOSED
- Test rate limiting: send burst → verify drops after threshold → verify ban after evasion
- Test backpressure: flood queue → verify discard at 5k → verify batch processing
- Test graceful shutdown: signal SIGTERM → verify ordered shutdown → verify 1001 codes
- **AC**: All resilience mechanisms work under simulated adverse conditions

### 9.2 Reconnection integration tests
- Test pwaMenu: disconnect → reconnect → queue replay → state sync
- Test pwaWaiter: disconnect → queue to IndexedDB → page refresh → reconnect → replay
- Test Dashboard: tab sync via BroadcastChannel
- **AC**: Reconnection flows work end-to-end; no data loss; conflict resolution works
