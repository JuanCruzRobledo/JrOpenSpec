---
sprint: 12
artifact: spec
status: complete
---

# Spec: Resiliencia y Real-time Completo

## Requirements (RFC 2119)

### Circuit Breaker — Redis Gateway
- The Gateway MUST wrap all Redis Pub/Sub operations in a circuit breaker
- The circuit breaker MUST transition from CLOSED to OPEN after 5 consecutive failures
- In OPEN state, the Gateway MUST NOT attempt Redis operations and MUST queue messages locally
- After 30 seconds in OPEN state, the circuit breaker MUST transition to SEMI_OPEN
- In SEMI_OPEN state, the Gateway MUST allow 3 probe operations
- If all 3 probes succeed, the circuit breaker MUST transition to CLOSED
- If any probe fails, the circuit breaker MUST transition back to OPEN (reset cooldown)
- The local queue MUST have a capacity of 5,000 messages
- When the queue exceeds 5,000 messages, the oldest messages MUST be discarded (FIFO eviction)
- The system MUST emit an alert when discard rate exceeds 5% of incoming messages in a 1-minute window

### Rate Limiting
- The Gateway MUST enforce a rate limit of 20 messages/second per WebSocket connection using a sliding window algorithm
- The Gateway MUST enforce a global broadcast rate limit of 10 broadcasts/second
- Rate limiting MUST be implemented via Redis Lua scripts for atomicity
- When a connection exceeds the rate limit, the message MUST be dropped and a warning sent to the client
- If a connection exceeds the rate limit 10 times within 5 minutes, the Gateway MUST impose a 1-hour penalty (ban)
- Banned connections MUST receive close code 4029 and be disconnected
- Rate limit configuration MUST be overridable via environment variables:
  - `WS_RATE_LIMIT_PER_CONNECTION` (default: 20)
  - `WS_RATE_LIMIT_BROADCAST` (default: 10)
  - `WS_EVASION_THRESHOLD` (default: 10)
  - `WS_EVASION_PENALTY_SECONDS` (default: 3600)

### Backpressure System
- The Pub/Sub subscriber queue MUST have a maximum capacity of 5,000 messages
- When the queue is full, new incoming messages MUST be auto-discarded
- The Gateway MUST process messages in batches of 50 events per cycle
- Each processing cycle MUST have a timeout of 30 seconds
- The Gateway MUST track discarded messages with a counter and timestamp
- The discard tracker MUST expose metrics for monitoring

### pwaMenu Reconnection
- The `DinerWebSocket` class MUST attempt up to 50 reconnection attempts
- Reconnection MUST use exponential backoff: base 1s, multiplier 2x, max 30s
- Each reconnection attempt MUST add random jitter of 0-500ms
- On disconnect, the app MUST activate the `OfflineQueue` for write operations
- On reconnect, the app MUST:
  1. Re-authenticate the WebSocket connection
  2. Request a full state sync from the server
  3. Replay queued offline operations
  4. Deactivate the OfflineQueue
- The app MUST display a connection status indicator during reconnection

### pwaWaiter Reconnection
- The waiter app MUST implement the same reconnection strategy as pwaMenu (50 attempts, backoff + jitter)
- Additionally, the offline queue MUST persist operations to IndexedDB (not just in-memory)
- The app MUST display a banner with connection status: "Reconectando... (intento N/50)"
- On reconnect, the app MUST replay IndexedDB queue before fetching fresh state
- The app MUST handle the case where queued operations conflict with server state (server wins)

### Graceful Shutdown
- On SIGTERM/SIGINT, the Gateway MUST execute shutdown in this order:
  1. Stop accepting new WebSocket connections
  2. Cancel all pending async tasks (5 second grace period)
  3. Stop background workers (outbox processor, retry worker)
  4. Flush and clean Redis caches
  5. Close Redis connections
  6. Send close frame (code 1001 "Going Away") to all connected WebSockets
  7. Close HTTP server
- The total shutdown MUST complete within 10 seconds
- If shutdown exceeds 10 seconds, the process MUST force-exit

### Origin Validation
- The Gateway MUST maintain a whitelist of allowed origins for WebSocket connections
- Origins MUST be configurable via environment variable: `WS_ALLOWED_ORIGINS` (comma-separated)
- Connections from non-whitelisted origins MUST be rejected with HTTP 403
- In development mode (`ENVIRONMENT=development`), all origins SHOULD be allowed

### WebSocket Close Codes
- 4001: Authentication failure (invalid/expired token)
- 4003: Forbidden (insufficient role/permissions)
- 4029: Rate limited (evasion penalty applied)
- 1001: Server going away (graceful shutdown)
- 1000: Normal closure (client-initiated)
- Clients MUST handle each close code with appropriate UI feedback

### Dashboard Tab Sync
- The Dashboard MUST use the BroadcastChannel API to synchronize state across browser tabs
- Channel name: `buen-sabor-dashboard-{branchId}`
- Events to sync: table state changes, order updates, payment updates
- On receiving a BroadcastChannel message, the Dashboard MUST update its local Zustand store
- Feature detection MUST be used: if BroadcastChannel is unsupported, the Dashboard MUST fall back to no sync (each tab independent)

### Health Checks
- GET /api/health/live MUST return 200 if the process is running (liveness)
- GET /api/health/ready MUST return 200 only if ALL subsystems are healthy:
  - PostgreSQL: connection pool active, can execute simple query
  - Redis: connection active, can PING
  - Circuit breaker: state is CLOSED or SEMI_OPEN (not OPEN)
  - Retry queue: no stuck items older than 1 hour
- If any subsystem is unhealthy, /ready MUST return 503 with details
- Gateway MUST have its own health endpoint: GET /ws/health

### Prometheus Metrics
- **Counters**: ws_messages_total, ws_errors_total, ws_auth_failures_total, ws_rate_limited_total, ws_messages_discarded_total
- **Gauges**: ws_connections_active, db_pool_active, db_pool_idle, redis_pool_active
- **Histograms**: ws_message_latency_seconds (buckets: 10ms, 50ms, 100ms, 250ms, 500ms, 1s), ws_broadcast_duration_seconds, http_request_duration_seconds
- All metrics MUST be exposed on GET /metrics in Prometheus text format
- Each metric MUST include relevant labels: service, branch_id, message_type

## Data Models

### CircuitBreakerMetrics
```python
class CircuitBreakerMetrics:
    state: str                          # CLOSED | OPEN | SEMI_OPEN
    failure_count: int
    success_count: int
    last_failure_at: datetime | None
    last_success_at: datetime | None
    total_requests: int
    total_failures: int
    total_circuit_opens: int
```

### ConnectionRateState
```python
class ConnectionRateState:
    connection_id: str
    message_timestamps: list[float]     # sliding window
    violation_count: int                # for evasion detection
    banned_until: datetime | None
```

### HealthStatus
```python
class HealthStatus:
    status: Literal['healthy', 'degraded', 'unhealthy']
    subsystems: dict[str, SubsystemHealth]
    timestamp: datetime

class SubsystemHealth:
    name: str
    status: Literal['healthy', 'unhealthy']
    latency_ms: float | None
    error: str | None
```

## API Contracts

### GET /api/health/live
**Auth**: None
**Response 200**: `{ "status": "alive", "uptime": 3600 }`

### GET /api/health/ready
**Auth**: None
**Response 200**:
```json
{
  "status": "healthy",
  "subsystems": {
    "postgresql": { "status": "healthy", "latency_ms": 2.1 },
    "redis": { "status": "healthy", "latency_ms": 0.5 },
    "circuit_breaker": { "status": "healthy", "state": "CLOSED" },
    "retry_queue": { "status": "healthy", "stuck_count": 0 }
  },
  "timestamp": "ISO8601"
}
```
**Response 503** (degraded):
```json
{
  "status": "unhealthy",
  "subsystems": {
    "postgresql": { "status": "healthy", "latency_ms": 2.1 },
    "redis": { "status": "unhealthy", "error": "Connection refused" },
    "circuit_breaker": { "status": "unhealthy", "state": "OPEN" },
    "retry_queue": { "status": "healthy", "stuck_count": 0 }
  },
  "timestamp": "ISO8601"
}
```

### GET /ws/health
**Auth**: None
**Response 200**:
```json
{
  "status": "healthy",
  "connections": 142,
  "redis": "connected",
  "circuitBreaker": "CLOSED",
  "queueSize": 23,
  "queueCapacity": 5000,
  "discardedLastMinute": 0
}
```

### GET /metrics
**Auth**: None (internal network only)
**Response 200**: Prometheus text format

## Scenarios

### Scenario: Redis Gateway circuit breaker activates
```
Given the Redis Gateway circuit breaker is CLOSED with 4 consecutive failures
When a 5th Redis Pub/Sub operation fails
Then the circuit breaker transitions to OPEN
And subsequent messages are queued locally (up to 5,000)
And /ws/health shows circuitBreaker: "OPEN"
After 30 seconds, the circuit breaker transitions to SEMI_OPEN
When 3 probe Redis operations succeed
Then the circuit breaker transitions to CLOSED
And queued messages are flushed to Redis
```

### Scenario: Rate limiting and evasion penalty
```
Given a WebSocket connection is sending messages
When the connection sends the 21st message within 1 second
Then the 21st message is dropped
And a rate limit warning is sent to the client
When the connection exceeds the rate limit 10 times within 5 minutes
Then the connection receives close code 4029
And the connection is disconnected
And the IP/user is banned for 1 hour
```

### Scenario: pwaMenu reconnection with offline queue
```
Given a diner has an active WebSocket connection
When the network drops
Then the DinerWebSocket starts reconnection attempts
And the OfflineQueue activates
And the UI shows "Reconectando..."
When the diner submits an order while offline
Then the order is queued in OfflineQueue
After 3 reconnection attempts (1s, 2s, 4s + jitter)
When connectivity returns
Then the WebSocket reconnects
And re-authenticates with the JWT
And replays the queued order
And the UI returns to normal
```

### Scenario: Graceful shutdown preserves state
```
Given the Gateway has 50 active WebSocket connections
And 12 messages in the Redis queue
When SIGTERM is received
Then the Gateway stops accepting new connections
And cancels pending tasks (within 5s)
And stops the outbox processor
And flushes Redis caches
And closes Redis connections
And sends close code 1001 to all 50 connections
And closes the HTTP server
And the total shutdown completes within 10 seconds
```

### Scenario: Dashboard tab synchronization
```
Given two Dashboard tabs are open for branch "Sucursal Centro"
And both subscribe to BroadcastChannel "buen-sabor-dashboard-sucursal-centro"
When Tab 1 receives a TABLE_STATE_CHANGED WebSocket event
Then Tab 1 updates its Zustand store
And Tab 1 posts the event to the BroadcastChannel
And Tab 2 receives the BroadcastChannel message
And Tab 2 updates its Zustand store without making an API call
```

### Scenario: Health check reports degraded state
```
Given PostgreSQL is healthy and Redis connection has failed
When GET /api/health/ready is called
Then response is 503 with status "unhealthy"
And postgresql subsystem shows "healthy"
And redis subsystem shows "unhealthy" with error details
And Kubernetes/Docker marks the pod as not ready
And load balancer stops routing traffic to this instance
```
