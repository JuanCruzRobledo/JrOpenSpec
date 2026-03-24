---
sprint: 12
artifact: design
status: complete
---

# Design: Resiliencia y Real-time Completo

## Architecture Decisions

### AD-1: Lua Scripts for Atomic Rate Limiting
- **Decision**: Implement rate limiting as Redis Lua scripts executed atomically.
- **Rationale**: Sliding window rate limiting requires read-then-write on sorted sets. Without atomicity, race conditions between concurrent checks would allow burst violations. Lua scripts execute atomically in Redis.
- **Tradeoff**: Lua scripts are harder to debug than application-level code. Mitigated by thorough unit testing and logging.

### AD-2: Fail-Open Rate Limiting
- **Decision**: If the Lua script fails (Redis down), allow the request rather than blocking it.
- **Rationale**: Availability over strict rate enforcement. A Redis failure already triggers the circuit breaker; additionally blocking all requests would cascade the outage.
- **Tradeoff**: Brief window of unlimited requests during Redis failure — acceptable since the circuit breaker limits damage.

### AD-3: BroadcastChannel with Feature Detection
- **Decision**: Use BroadcastChannel API for Dashboard tab sync with runtime feature detection.
- **Rationale**: BroadcastChannel is supported in all modern browsers (Chrome 54+, Firefox 38+, Edge 79+). For unsupported browsers, each tab operates independently (no data loss, just stale views).
- **Tradeoff**: No fallback sync mechanism — acceptable for an admin Dashboard.

### AD-4: Ordered Graceful Shutdown
- **Decision**: Strict sequential shutdown: tasks → workers → cache → Redis → WebSockets → HTTP.
- **Rationale**: Order matters — workers may need Redis to flush; WebSockets should get close frames before the server stops. Timeout of 10s ensures the process doesn't hang.
- **Tradeoff**: Slightly slower shutdown than parallel — but prevents data corruption.

### AD-5: Backpressure via Bounded Queues + Batch Processing
- **Decision**: 5k message queue with batch-50 processing and auto-discard on overflow.
- **Rationale**: Unbounded queues cause memory exhaustion. Batch processing amortizes I/O overhead. 5k capacity ≈ 10 minutes of normal traffic.
- **Tradeoff**: Message loss on sustained overload — tracked by discard counter and alerted at 5% threshold.

## File Structure

### Backend / Gateway additions
```
gateway/
├── circuit_breaker/
│   ├── redis_circuit_breaker.py     # Redis-specific CB implementation
│   └── metrics.py                   # CB metrics collector
├── rate_limiting/
│   ├── rate_limiter.py              # Main rate limiter class
│   ├── lua_scripts/
│   │   ├── sliding_window.lua       # Atomic sliding window check+add
│   │   └── evasion_check.lua        # Violation counter + ban check
│   ├── evasion_tracker.py           # Ban management
│   └── config.py                    # Rate limit configuration
├── backpressure/
│   ├── bounded_queue.py             # 5k capacity queue
│   ├── batch_processor.py           # 50-event batch cycle
│   └── discard_tracker.py           # Discard counting + alerting
├── shutdown/
│   └── graceful_shutdown.py         # Ordered shutdown sequence
├── security/
│   ├── origin_validator.py          # Whitelist-based origin check
│   └── close_codes.py              # Custom WebSocket close codes
├── health/
│   ├── health_checker.py            # Subsystem health aggregator
│   ├── checks/
│   │   ├── postgresql_check.py
│   │   ├── redis_check.py
│   │   ├── circuit_breaker_check.py
│   │   └── retry_queue_check.py
│   └── routes.py                    # /health/live, /health/ready, /ws/health
├── metrics/
│   ├── prometheus.py                # Metrics registry + exposition
│   ├── collectors/
│   │   ├── ws_collector.py          # WebSocket metrics
│   │   ├── db_collector.py          # Database pool metrics
│   │   └── redis_collector.py       # Redis pool metrics
│   └── routes.py                    # /metrics endpoint
└── sync/
    └── broadcast_channel.py         # Server-side broadcast event formatting
```

### pwaMenu additions
```
pwaMenu/src/
├── realtime/
│   ├── DinerWebSocket.ts            # Enhanced with reconnection
│   ├── reconnection/
│   │   ├── BackoffStrategy.ts       # Exponential backoff + jitter
│   │   └── ReconnectionManager.ts   # Attempt tracking, state management
│   └── offline/
│       └── OfflineQueue.ts          # In-memory queue with replay
```

### pwaWaiter additions
```
pwaWaiter/src/
├── realtime/
│   ├── WaiterWebSocket.ts           # Enhanced with reconnection
│   ├── reconnection/
│   │   ├── BackoffStrategy.ts       # Shared with pwaMenu
│   │   └── ReconnectionManager.ts
│   └── offline/
│       ├── PersistentQueue.ts       # IndexedDB-backed queue
│       └── QueueReplay.ts           # Conflict resolution (server wins)
├── components/
│   └── ConnectionBanner.tsx         # "Reconectando... (intento N/50)"
```

### Dashboard additions
```
dashboard/src/
├── sync/
│   ├── BroadcastSync.ts            # BroadcastChannel wrapper
│   ├── useBroadcastSync.ts         # React hook
│   └── types.ts                    # Sync message types
```

## Sequence Diagrams

### Circuit Breaker — Redis Failure Recovery
```
Gateway         CircuitBreaker     Redis           LocalQueue       AlertService
  |                  |                |                |                |
  |--publish msg---->|                |                |                |
  |                  |--try Redis---->|                |                |
  |                  |<--FAIL---------|                |                |
  |                  |  (failure 5/5) |                |                |
  |                  |--state→OPEN--->|                |                |
  |                  |                |                |                |
  |--publish msg---->|                |                |                |
  |                  |--[OPEN]------->|  queue msg---->|                |
  |                  |                |                |                |
  |  ... 30 seconds pass ...         |                |                |
  |                  |--state→SEMI_OPEN               |                |
  |--publish msg---->|                |                |                |
  |                  |--probe Redis-->|                |                |
  |                  |<--OK-----------|                |                |
  |                  |--probe 2------>|                |                |
  |                  |<--OK-----------|                |                |
  |                  |--probe 3------>|                |                |
  |                  |<--OK-----------|                |                |
  |                  |--state→CLOSED  |                |                |
  |                  |--flush queue-->|  drain-------->|                |
  |                  |                |--publish all-->|                |
```

### Rate Limiting Flow
```
Client          Gateway          Redis (Lua)       EvasionTracker
  |                |                |                   |
  |--WS message--->|                |                   |
  |                |--EVALSHA sliding_window.lua-------->|
  |                |<--{allowed: true, count: 15}-------|
  |                |--process msg   |                   |
  |                |                |                   |
  |--WS message--->|  (21st in 1s) |                   |
  |                |--EVALSHA------>|                   |
  |                |<--{allowed: false, count: 21}------|
  |                |--drop msg      |                   |
  |                |--warn client   |                   |
  |                |--increment violation-------------->|
  |                |                |                   |
  |  ... 10 violations in 5 min ...                     |
  |                |<--ban triggered-|                   |
  |                |--close(4029)-->|                   |
  |<--[disconnected]                |                   |
```

### Reconnection + Offline Queue Replay
```
DinerApp       DinerWebSocket    BackoffStrategy    OfflineQueue     Server
  |                |                  |                 |               |
  |  [network drops]                  |                 |               |
  |                |--onclose-------->|                 |               |
  |                |                  |--delay 1s+jitter|               |
  |                |--attempt 1----->|                  |               |
  |                |  [FAIL]         |--delay 2s+jitter|               |
  |                |--attempt 2----->|                  |               |
  |                |  [FAIL]         |--delay 4s+jitter|               |
  |                |                  |                 |               |
  |--submit order->|                  |                 |               |
  |                |--[offline]------>|  enqueue-------->|               |
  |                |                  |                 |               |
  |                |--attempt 3----->|                  |               |
  |                |  [SUCCESS]      |                  |               |
  |                |--re-auth------->|                  |-------------->|
  |                |<--auth OK-------|                  |               |
  |                |--request sync-->|                  |-------------->|
  |                |<--full state----|                  |               |
  |                |--replay queue-->|  dequeue-------->|               |
  |                |                  |  POST order---->|-------------->|
  |                |                  |                 |<--201---------|
  |                |                  |  clear queue--->|               |
```

### Graceful Shutdown
```
OS              Gateway         AsyncTasks      Workers         Redis           WebSockets
  |                |                |               |               |               |
  |--SIGTERM------>|                |               |               |               |
  |                |--stop accept-->|               |               |               |
  |                |--cancel tasks->|               |               |               |
  |                |                |--grace 5s---->|               |               |
  |                |                |--done-------->|               |               |
  |                |--stop workers->|               |               |               |
  |                |                |               |--stop-------->|               |
  |                |--flush cache-->|               |               |               |
  |                |                |               |--flush------->|               |
  |                |--close Redis-->|               |               |               |
  |                |                |               |               |--close------->|
  |                |--close WS(1001)>               |               |               |
  |                |                |               |               |               |--1001
  |                |--close HTTP--->|               |               |               |
  |                |--exit(0)------>|               |               |               |
```

## Lua Scripts Design

### sliding_window.lua
```lua
-- KEYS[1] = rate limit key (e.g., "rate:ws:{conn_id}")
-- ARGV[1] = current timestamp (ms)
-- ARGV[2] = window size (ms)
-- ARGV[3] = max requests
-- Returns: {allowed (0/1), current_count}

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_requests = tonumber(ARGV[3])

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count current entries
local count = redis.call('ZCARD', key)

if count >= max_requests then
    return {0, count}
end

-- Add current request
redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))
redis.call('PEXPIRE', key, window)

return {1, count + 1}
```

### evasion_check.lua
```lua
-- KEYS[1] = violation counter key
-- ARGV[1] = current timestamp (ms)
-- ARGV[2] = window size (ms) -- 5 min = 300000
-- ARGV[3] = threshold (10)
-- ARGV[4] = penalty duration (ms) -- 1 hour = 3600000
-- Returns: {should_ban (0/1), violation_count}

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local threshold = tonumber(ARGV[3])
local penalty = tonumber(ARGV[4])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))
redis.call('PEXPIRE', key, window)

local count = redis.call('ZCARD', key)

if count >= threshold then
    -- Set ban key
    redis.call('SET', key .. ':ban', '1', 'PX', penalty)
    return {1, count}
end

return {0, count}
```

## Prometheus Metrics Schema

```
# Counters
ws_messages_total{service="gateway", branch_id="uuid", type="TABLE_STATE_CHANGED"} 1234
ws_errors_total{service="gateway", error_type="auth_failure"} 5
ws_auth_failures_total{service="gateway"} 12
ws_rate_limited_total{service="gateway", action="drop|ban"} 89
ws_messages_discarded_total{service="gateway", reason="queue_full|timeout"} 3

# Gauges
ws_connections_active{service="gateway", branch_id="uuid"} 142
db_pool_active{service="api"} 8
db_pool_idle{service="api"} 12
redis_pool_active{service="gateway"} 3

# Histograms
ws_message_latency_seconds_bucket{le="0.01"} 950
ws_message_latency_seconds_bucket{le="0.05"} 990
ws_message_latency_seconds_bucket{le="0.1"} 998
ws_message_latency_seconds_bucket{le="0.25"} 999
ws_message_latency_seconds_bucket{le="0.5"} 1000
ws_message_latency_seconds_bucket{le="1.0"} 1000
ws_broadcast_duration_seconds_bucket{...} ...
http_request_duration_seconds_bucket{method="GET", path="/api/tables", ...} ...
```
