---
sprint: 16
artifact: spec
status: complete
---

# Spec: CI/CD, Monitoring y Security Hardening

## Requirements (RFC 2119)

### CI/CD Pipeline
- Every pull request MUST trigger: ruff lint, mypy type check, pytest unit tests
- Tests MUST include unit tests and integration tests (separate stages)
- A passing PR MUST trigger Docker image build and push to container registry
- Merge to `main` MUST automatically deploy to staging environment
- Deploy to production MUST require manual approval (GitHub Environments)
- The pipeline MUST cache pip dependencies and Docker layers for speed
- Pipeline total time SHOULD be under 10 minutes for the lint+test+build stages
- Failed lint or tests MUST block the PR from merging

### Environment Validation
- The system MUST include a `validate_env.py` script that checks all required environment variables at startup
- Required variables MUST include: DATABASE_URL, REDIS_URL, JWT_SECRET, MERCADOPAGO_ACCESS_TOKEN (or MERCADOPAGO_SIMULATE=true), ALLOWED_ORIGINS, ENVIRONMENT
- Missing required variables MUST cause the process to exit with code 1 and a clear error message listing ALL missing variables
- The script MUST distinguish between required and optional variables
- Optional variables MUST log a warning if missing but not fail

### Health Checks
- GET /api/health/live MUST return 200 with `{"status": "alive", "uptime": <seconds>}` if the process is running
- GET /api/health/ready MUST check ALL subsystems and return 200 only if all are healthy:
  - **PostgreSQL**: execute `SELECT 1`, verify connection pool has available connections
  - **Redis**: execute `PING`, verify response is `PONG`
  - **Circuit breaker**: state MUST NOT be OPEN
  - **Retry queue**: no items stuck for > 1 hour
- If any subsystem is unhealthy, /ready MUST return 503 with per-subsystem details
- GET /ws/health MUST return Gateway-specific health: connections count, Redis status, circuit breaker state, queue size/capacity
- Health check endpoints MUST NOT require authentication
- Health check responses MUST include `Cache-Control: no-store`

### Prometheus Metrics
- **Counters** (MUST):
  - `http_requests_total{method, path, status_code}` — total HTTP requests
  - `http_errors_total{method, path, error_type}` — HTTP errors (4xx, 5xx)
  - `auth_failures_total{reason}` — authentication failures (expired, invalid, missing)
  - `ws_rate_limited_total{action}` — WebSocket rate limit events (drop, ban)
  - `ws_messages_total{type, direction}` — WebSocket messages (in/out, by event type)
  - `ws_messages_discarded_total{reason}` — discarded messages (queue_full, timeout)
- **Gauges** (MUST):
  - `ws_connections_active{branch_id}` — current WebSocket connections per branch
  - `db_pool_connections{state}` — database pool (active, idle, total)
  - `redis_pool_connections{state}` — Redis pool (active, idle)
- **Histograms** (MUST):
  - `http_request_duration_seconds{method, path}` — HTTP request latency (buckets: 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 5s)
  - `ws_broadcast_duration_seconds` — WebSocket broadcast latency
  - `db_query_duration_seconds{query_type}` — database query latency
- Metrics MUST be exposed on GET /metrics in Prometheus text exposition format
- The /metrics endpoint MUST be accessible only from internal network (no public access)

### Structured Logging
- All services MUST output logs in JSON format to stdout
- Each log entry MUST include: timestamp (ISO 8601), level, message, service_name, correlation_id
- HTTP request logs MUST include: method, path, status_code, duration_ms, user_id (if authenticated)
- WebSocket logs MUST include: connection_id, event_type, branch_id
- Error logs MUST include: exception type, message, stack trace (as array of strings)
- Log levels MUST be configurable via environment variable: `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR)
- The system MUST generate a unique correlation_id per HTTP request and propagate it through all downstream calls

### Security Headers
- All HTTP responses MUST include:
  - `Content-Security-Policy`: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss: https://api.mercadopago.com; font-src 'self'
  - `Strict-Transport-Security`: max-age=31536000; includeSubDomains
  - `X-Frame-Options`: DENY
  - `X-Content-Type-Options`: nosniff
  - `X-XSS-Protection`: 0 (disabled in favor of CSP)
  - `Referrer-Policy`: strict-origin-when-cross-origin
  - `Permissions-Policy`: camera=(), microphone=(), geolocation=()
- CSP MUST be tested in report-only mode in staging before enforcement in production

### SSRF Protection
- All outbound HTTP requests (e.g., Mercado Pago webhook verification) MUST validate the target URL
- The system MUST block requests to:
  - Private IP ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8
  - Link-local: 169.254.0.0/16
  - Cloud metadata endpoints: 169.254.169.254, metadata.google.internal
  - IPv6 equivalents: ::1, fc00::/7, fe80::/10
- Blocked requests MUST log a security warning and return 403
- The whitelist for allowed external domains MUST be configurable

### Security Audit Checklist
- All API endpoints MUST have RBAC decorator/dependency checking user role
- All user inputs MUST be validated via Pydantic schemas (no raw dict access)
- SQL queries MUST use parameterized queries only (no f-string interpolation)
- All rate limiting configurations MUST be verified as active
- Blacklisted users/IPs MUST be verified as blocked
- WebSocket connections MUST verify JWT on connect and periodically (every 5 min)
- File uploads (import) MUST validate content type and size before processing
- Password hashing MUST use bcrypt with minimum 12 rounds

### Performance Targets
- The system MUST support 400-600 concurrent users (mixed: 60% diners, 30% waiters, 10% admin)
- WebSocket broadcast to 400 users MUST complete in < 200ms
- API endpoints MUST respond in < 100ms at P95 under normal load
- Database connection pool MUST handle concurrent queries without exhaustion (pool size >= 20)
- Redis operations MUST complete in < 5ms at P95

### Load Testing
- Load tests MUST be implemented using k6 or locust
- Test scenarios MUST include:
  - API load: concurrent GET /branches/{id}/tables, POST /sessions/{id}/orders
  - WebSocket load: 400 concurrent connections with message broadcast
  - Mixed load: simultaneous API + WebSocket traffic
  - Spike test: sudden increase from 100 to 500 users in 30 seconds
- Tests MUST run against staging environment
- Results MUST be recorded and compared across releases

### Documentation
- A production Docker Compose file MUST be provided with all services
- An environment variables reference MUST list all vars with: name, required/optional, default, description
- An operational runbook MUST cover: deployment, rollback, common issues, monitoring alerts
- Backup/restore procedures MUST cover: PostgreSQL full backup, point-in-time recovery, Redis snapshot

## Data Models

### HealthResponse
```python
class HealthResponse:
    status: Literal['healthy', 'degraded', 'unhealthy']
    uptime: int                          # seconds
    subsystems: dict[str, SubsystemStatus]
    timestamp: str                       # ISO 8601

class SubsystemStatus:
    status: Literal['healthy', 'unhealthy']
    latency_ms: float | None
    details: dict | None                 # extra info
    error: str | None
```

### LogEntry
```python
class LogEntry:
    timestamp: str                       # ISO 8601
    level: str                           # DEBUG, INFO, WARNING, ERROR
    message: str
    service: str                         # "api", "gateway", "worker"
    correlation_id: str                  # UUID, propagated across calls
    # HTTP-specific
    method: str | None
    path: str | None
    status_code: int | None
    duration_ms: float | None
    user_id: str | None
    # Error-specific
    exception_type: str | None
    exception_message: str | None
    stack_trace: list[str] | None
```

### LoadTestConfig
```python
class LoadTestConfig:
    scenario: str                        # "api_load", "ws_load", "mixed", "spike"
    target_users: int                    # 400-600
    duration_seconds: int                # test duration
    ramp_up_seconds: int                 # time to reach target
    thresholds: dict[str, str]           # e.g., {"http_req_duration": "p(95)<100"}
```

## API Contracts

### GET /api/health/live
**Auth**: None
**Headers**: `Cache-Control: no-store`
**Response 200**:
```json
{ "status": "alive", "uptime": 86400 }
```

### GET /api/health/ready
**Auth**: None
**Headers**: `Cache-Control: no-store`
**Response 200** (all healthy):
```json
{
  "status": "healthy",
  "uptime": 86400,
  "subsystems": {
    "postgresql": { "status": "healthy", "latency_ms": 1.8, "details": { "pool_active": 5, "pool_idle": 15 } },
    "redis": { "status": "healthy", "latency_ms": 0.4 },
    "circuit_breaker": { "status": "healthy", "details": { "state": "CLOSED", "failure_count": 0 } },
    "retry_queue": { "status": "healthy", "details": { "pending": 3, "stuck": 0 } }
  },
  "timestamp": "2026-03-19T10:00:00Z"
}
```
**Response 503** (unhealthy): Same schema with `status: "unhealthy"` and affected subsystem details

### GET /ws/health
**Auth**: None
**Response 200**:
```json
{
  "status": "healthy",
  "connections": 142,
  "redis": { "status": "connected", "latency_ms": 0.3 },
  "circuitBreaker": { "state": "CLOSED" },
  "queue": { "size": 23, "capacity": 5000, "discardedLastMinute": 0 }
}
```

### GET /metrics
**Auth**: Internal network only (no public access)
**Response 200**: Prometheus text exposition format

## Scenarios

### Scenario: CI pipeline on pull request
```
Given a developer pushes a commit to a feature branch
When a pull request is created
Then GitHub Actions triggers:
  1. ruff lint (parallel)
  2. mypy type check (parallel)
  3. pytest unit tests (after lint passes)
  4. pytest integration tests (after unit passes)
  5. Docker build (after all tests pass)
And if any step fails, the PR is marked as failed
And the PR cannot be merged until all checks pass
```

### Scenario: Environment validation on startup
```
Given the Docker container starts
When validate_env.py runs
And DATABASE_URL is set but JWT_SECRET is missing
Then the script prints: "FATAL: Missing required environment variables: JWT_SECRET"
And the process exits with code 1
And the container is marked as crashed (Docker restart policy applies)
```

### Scenario: Structured log with correlation ID
```
Given a diner sends POST /api/sessions/{id}/orders
When the request enters the API
Then a correlation_id UUID is generated and set in request context
And the API logs: {"timestamp":"...","level":"INFO","message":"Order created","service":"api","correlation_id":"abc-123","method":"POST","path":"/api/sessions/x/orders","status_code":201,"duration_ms":45,"user_id":"..."}
And the outbox processor logs with the same correlation_id
And the Gateway broadcasts with the same correlation_id
```

### Scenario: CSP blocks inline script injection
```
Given an attacker manages to inject a <script>alert('xss')</script> into a product description
When the diner views the product in pwaMenu
Then the CSP header prevents inline script execution
And the browser console logs: "Refused to execute inline script because it violates CSP"
And the XSS attack is neutralized
```

### Scenario: SSRF protection blocks internal request
```
Given a Mercado Pago webhook payload contains redirect URL "http://169.254.169.254/latest/meta-data/"
When the system attempts to verify the webhook by fetching the URL
Then the SSRF protection middleware intercepts the request
And the URL is matched against the blocked IP ranges
And the request is blocked with a security warning log
And 403 is returned instead of following the redirect
```

### Scenario: Load test validates performance targets
```
Given k6 is configured with 500 virtual users, 5-minute duration
When the mixed load test runs against staging:
  - 300 diners browsing menu + ordering (HTTP)
  - 150 waiters monitoring tables (WebSocket)
  - 50 admins viewing dashboard (HTTP)
Then API P95 latency is < 100ms
And WebSocket broadcast to 400 users completes in < 200ms
And no HTTP 5xx errors occur
And database pool is not exhausted
And the test results are saved for comparison
```

### Scenario: Production deployment with approval
```
Given all tests pass on a PR merged to main
When the staging deployment succeeds
And the team verifies staging is working correctly
When an admin clicks "Approve" on the production deployment
Then the production Docker images are pulled
And the new containers start with health checks
And the load balancer routes traffic after /ready returns 200
And the old containers are stopped gracefully
```
