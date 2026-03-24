---
sprint: 16
artifact: design
status: complete
---

# Design: CI/CD, Monitoring y Security Hardening

## Architecture Decisions

### AD-1: GitHub Actions with Environment Protection
- **Decision**: GitHub Actions for CI/CD with staging (auto-deploy) and production (manual approval) environments.
- **Rationale**: Native GitHub integration, free for public repos, environment protection rules provide approval gates for production.
- **Tradeoff**: Vendor lock-in to GitHub — acceptable since the repo is already on GitHub.

### AD-2: Correlation ID via Middleware
- **Decision**: Generate a UUID correlation_id per request in FastAPI middleware, propagate via `contextvars`.
- **Rationale**: Enables tracing a request across API → outbox → Gateway → WebSocket. `contextvars` is thread/async-safe and doesn't require passing IDs through function signatures.
- **Tradeoff**: contextvars can be tricky in nested async contexts — mitigated by middleware-level initialization.

### AD-3: CSP Report-Only in Staging, Enforce in Production
- **Decision**: Use `Content-Security-Policy-Report-Only` in staging, switch to `Content-Security-Policy` in production after validation.
- **Rationale**: CSP can break functionality if misconfigured (inline styles, external resources). Report-only mode logs violations without blocking, allowing safe tuning.
- **Tradeoff**: Staging period without enforcement — acceptable since staging is not public.

### AD-4: k6 for Load Testing
- **Decision**: Use k6 (Grafana Labs) for load testing over locust.
- **Rationale**: k6 supports both HTTP and WebSocket protocols natively, has built-in thresholds, and outputs results in Prometheus-compatible format. Written in Go (no Python dependency overhead).
- **Tradeoff**: JavaScript-based test scripts (not Python) — acceptable for test scripts.

### AD-5: Python-dotenv + Pydantic Settings for Env Validation
- **Decision**: Use Pydantic `BaseSettings` for environment variable validation with explicit required/optional annotations.
- **Rationale**: Pydantic validates types, provides defaults, and generates clear error messages. Single source of truth for all configuration.
- **Tradeoff**: Slightly heavier than raw os.environ — but the validation is worth it.

## File Structure

### CI/CD
```
.github/
├── workflows/
│   ├── ci.yml                        # Lint + test on every PR
│   ├── build.yml                     # Docker build + push on merge to main
│   ├── deploy-staging.yml            # Auto-deploy to staging
│   └── deploy-production.yml        # Manual approval + deploy to production
├── actions/
│   └── setup-python/
│       └── action.yml                # Reusable Python setup action
└── CODEOWNERS                        # Review requirements
```

### Environment & Config
```
app/
├── config/
│   ├── settings.py                   # Pydantic BaseSettings (all env vars)
│   ├── validate_env.py               # Startup validation script
│   └── logging_config.py            # Structured JSON logging setup
```

### Health & Metrics
```
app/
├── health/
│   ├── router.py                     # /health/live, /health/ready
│   ├── checker.py                    # SubsystemHealthChecker
│   └── checks/
│       ├── postgresql.py             # SELECT 1 + pool check
│       ├── redis.py                  # PING check
│       ├── circuit_breaker.py        # State check
│       └── retry_queue.py           # Stuck items check
├── metrics/
│   ├── prometheus.py                 # Metrics registry
│   ├── middleware.py                 # Request duration + counter middleware
│   ├── ws_metrics.py                # WebSocket instrumentation
│   └── router.py                    # GET /metrics

gateway/
├── health/
│   └── router.py                     # GET /ws/health
├── metrics/
│   └── ws_collector.py              # WS-specific metrics
```

### Security
```
app/
├── security/
│   ├── headers_middleware.py         # Security headers (CSP, HSTS, etc.)
│   ├── ssrf_validator.py            # URL validation against blocked ranges
│   ├── audit_checklist.py           # Automated security checks (test suite)
│   └── cors_config.py              # CORS configuration
```

### Logging
```
app/
├── logging/
│   ├── json_formatter.py            # Custom JSON log formatter
│   ├── correlation.py               # Correlation ID middleware + contextvars
│   └── filters.py                   # Log filters (mask sensitive data)
```

### Load Testing
```
load-tests/
├── k6/
│   ├── api-load.js                   # HTTP API load test
│   ├── ws-load.js                    # WebSocket load test
│   ├── mixed-load.js                # Combined HTTP + WS
│   ├── spike-test.js                # Spike from 100 to 500 users
│   └── thresholds.json              # Performance thresholds config
├── scripts/
│   ├── run-load-tests.sh            # Test runner with reporting
│   └── compare-results.sh          # Compare results across runs
└── results/                          # Test result archives
```

### Documentation
```
docs/
├── deployment/
│   ├── docker-compose.prod.yml      # Production compose file
│   ├── env-vars-reference.md        # All environment variables
│   └── deployment-guide.md          # Step-by-step deployment
├── operations/
│   ├── runbook.md                    # Operational runbook
│   ├── monitoring-guide.md          # Prometheus + alerting setup
│   └── backup-restore.md           # Backup/restore procedures
└── security/
    └── security-audit-report.md     # Audit findings + remediation
```

## Sequence Diagrams

### CI/CD Pipeline
```
Developer       GitHub           CI Runner         Registry         Staging          Production
  |                |                |                 |                |                |
  |--push commit-->|                |                 |                |                |
  |--open PR------>|                |                 |                |                |
  |                |--trigger CI--->|                 |                |                |
  |                |                |--ruff lint      |                |                |
  |                |                |--mypy check     |                |                |
  |                |                |--pytest unit    |                |                |
  |                |                |--pytest integ   |                |                |
  |                |                |--[all pass]     |                |                |
  |                |<--PR checks OK-|                 |                |                |
  |                |                |                 |                |                |
  |--merge to main>|               |                 |                |                |
  |                |--trigger build>|                 |                |                |
  |                |                |--docker build-->|                |                |
  |                |                |                 |--push image--->|                |
  |                |--auto deploy-->|                 |                |                |
  |                |                |--deploy-------->|  staging       |                |
  |                |                |                 |                |                |
  |                |  [manual approval]               |                |                |
  |                |--approve prod->|                 |                |                |
  |                |                |--deploy-------->|                |  production    |
```

### Request with Correlation ID
```
Client          Middleware       API Handler       OutboxProcessor   Gateway          Client
  |                |                |                  |                |                |
  |--POST /order-->|                |                  |                |                |
  |                |--gen corr_id   |                  |                |                |
  |                |--set contextvar|                  |                |                |
  |                |--log: "Request started" {corr_id}  |                |                |
  |                |--forward------>|                  |                |                |
  |                |                |--create order    |                |                |
  |                |                |--insert outbox   |                |                |
  |                |                |  (corr_id in metadata)           |                |
  |                |<--201----------|                  |                |                |
  |                |--log: "201 in 45ms" {corr_id}     |                |                |
  |<--response-----|                |                  |                |                |
  |                |                |                  |                |                |
  |                |                |  [outbox poll]   |                |                |
  |                |                |  log: "Processing event" {corr_id}|                |
  |                |                |                  |--publish------>|                |
  |                |                |                  |                |--broadcast---->|
  |                |                |                  |                |  log: "Broadcast" {corr_id}
```

### Health Check Integration
```
LoadBalancer    API              HealthChecker     PostgreSQL       Redis
  |                |                |                 |                |
  |--GET /ready--->|                |                 |                |
  |                |--check all---->|                 |                |
  |                |                |--SELECT 1------>|                |
  |                |                |<--OK (1.8ms)----|                |
  |                |                |--PING---------->|                |
  |                |                |<--PONG (0.4ms)--|                |
  |                |                |--check CB state |                |
  |                |                |--check retry Q  |                |
  |                |<--all healthy--|                 |                |
  |<--200 {healthy}|                |                 |                |
  |                |                |                 |                |
  |  [Redis goes down]              |                 |                |
  |--GET /ready--->|                |                 |                |
  |                |--check all---->|                 |                |
  |                |                |--SELECT 1------>|                |
  |                |                |<--OK------------|                |
  |                |                |--PING---------->|                |
  |                |                |<--FAIL----------|                |
  |                |<--redis unhealthy                |                |
  |<--503 {unhealthy, redis: error} |                 |                |
  |--[stop routing traffic]         |                 |                |
```

## Security Headers Configuration

```python
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "  # Tailwind needs unsafe-inline
        "img-src 'self' data: https:; "       # data: for base64, https: for CDN images
        "connect-src 'self' wss: https://api.mercadopago.com; "
        "font-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "0",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
```

## SSRF Blocked IP Ranges

```python
BLOCKED_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),      # Link-local + AWS metadata
    ipaddress.ip_network("::1/128"),               # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),              # IPv6 private
    ipaddress.ip_network("fe80::/10"),             # IPv6 link-local
]

BLOCKED_HOSTNAMES = [
    "metadata.google.internal",
    "metadata.internal",
]
```

## Docker Compose Production Architecture

```yaml
services:
  api:
    image: buensabor/api:${VERSION}
    environment:
      - DATABASE_URL
      - REDIS_URL
      - JWT_SECRET
      - ENVIRONMENT=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/ready"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    deploy:
      replicas: 2
      resources:
        limits: { cpus: '1', memory: '512M' }

  gateway:
    image: buensabor/gateway:${VERSION}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/ws/health"]
    deploy:
      replicas: 2
      resources:
        limits: { cpus: '0.5', memory: '256M' }

  worker:
    image: buensabor/worker:${VERSION}
    # Outbox processor + retry worker

  postgresql:
    image: postgres:16-alpine
    volumes: [pgdata:/var/lib/postgresql/data]
    environment: [POSTGRES_PASSWORD]

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  nginx:
    image: nginx:alpine
    # Reverse proxy + TLS termination + static file serving
    ports: ["443:443", "80:80"]

  prometheus:
    image: prom/prometheus
    volumes: [./prometheus.yml:/etc/prometheus/prometheus.yml]
```
