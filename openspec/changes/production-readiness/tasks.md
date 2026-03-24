---
sprint: 16
artifact: tasks
status: complete
---

# Tasks: CI/CD, Monitoring y Security Hardening

## Phase 1: CI/CD Pipeline

### 1.1 CI workflow (lint + test)
- Create `.github/workflows/ci.yml`: trigger on PR to main
- Stage 1 (parallel): ruff lint, mypy type check
- Stage 2 (sequential): pytest unit tests
- Stage 3 (sequential): pytest integration tests (with DB + Redis via services)
- Cache pip dependencies across runs
- Fail PR if any step fails
- **Files**: `.github/workflows/ci.yml`, `.github/actions/setup-python/action.yml`
- **AC**: PR triggers CI; lint/test run correctly; cache speeds up subsequent runs; failed step blocks merge

### 1.2 Build & push workflow
- Create `.github/workflows/build.yml`: trigger on merge to main
- Build Docker images for: api, gateway, worker
- Tag images with: commit SHA, `latest`, semver (from git tag if present)
- Push to container registry (GitHub Container Registry or DockerHub)
- Cache Docker layers
- **Files**: `.github/workflows/build.yml`, `Dockerfile` (api), `Dockerfile` (gateway), `Dockerfile` (worker)
- **AC**: Merge to main builds and pushes 3 images; layer caching reduces build time; tags correct

### 1.3 Deploy workflows
- Create `.github/workflows/deploy-staging.yml`: auto-deploy on successful build
- Create `.github/workflows/deploy-production.yml`: manual trigger with environment approval
- Production workflow: require approval from at least 1 reviewer
- Both workflows: pull image, run migrations, restart services, verify health
- **Files**: `.github/workflows/deploy-staging.yml`, `.github/workflows/deploy-production.yml`
- **AC**: Staging auto-deploys on merge; production requires manual approval; health verified post-deploy

## Phase 2: Environment & Logging

### 2.1 Environment validation
- Create Pydantic `Settings` class with all env vars (required + optional with defaults)
- Required: DATABASE_URL, REDIS_URL, JWT_SECRET, ALLOWED_ORIGINS, ENVIRONMENT
- Required (conditional): MERCADOPAGO_ACCESS_TOKEN (unless MERCADOPAGO_SIMULATE=true)
- Optional with defaults: LOG_LEVEL=INFO, WS_RATE_LIMIT_PER_CONNECTION=20, DB_POOL_SIZE=20
- Create `validate_env.py` script: instantiate Settings, catch ValidationError, print all missing/invalid vars, exit(1)
- Run at container startup (before uvicorn)
- **Files**: `app/config/settings.py`, `app/config/validate_env.py`
- **AC**: Missing required var prints clear error and exits 1; optional vars use defaults; conditional logic works

### 2.2 Structured JSON logging
- Implement `JsonFormatter` class: outputs JSON with timestamp, level, message, service, correlation_id
- Implement `CorrelationMiddleware`: generates UUID per request, stores in `contextvars`, includes in all log entries
- Configure Python logging to use JSON formatter for all handlers
- Mask sensitive data in logs (passwords, tokens) via log filter
- **Files**: `app/logging/json_formatter.py`, `app/logging/correlation.py`, `app/logging/filters.py`, `app/config/logging_config.py`
- **AC**: All log output is valid JSON; correlation_id present in request logs; sensitive data masked; level configurable via env

## Phase 3: Health Checks

### 3.1 Health check implementation
- Implement `SubsystemHealthChecker` with check methods for: PostgreSQL, Redis, circuit breaker, retry queue
- PostgreSQL check: execute `SELECT 1`, check pool stats (active, idle, total)
- Redis check: execute `PING`, verify `PONG` response
- Circuit breaker check: verify state is not OPEN
- Retry queue check: count items stuck > 1 hour
- **Files**: `app/health/checker.py`, `app/health/checks/postgresql.py`, `app/health/checks/redis.py`, `app/health/checks/circuit_breaker.py`, `app/health/checks/retry_queue.py`
- **AC**: Each check returns status + latency_ms; failed check returns error message; independent failures don't crash other checks

### 3.2 Health endpoints
- GET /api/health/live: always 200 with uptime
- GET /api/health/ready: 200 if all healthy, 503 with details if any unhealthy
- GET /ws/health: Gateway-specific health (connections, Redis, CB, queue)
- All endpoints: no auth, Cache-Control: no-store
- **Files**: `app/health/router.py`, `gateway/health/router.py`
- **AC**: /live always returns 200; /ready returns 503 when any subsystem down; /ws/health returns gateway stats

## Phase 4: Prometheus Metrics

### 4.1 Metrics instrumentation
- Set up `prometheus_client` registry with all defined metrics (counters, gauges, histograms)
- Implement `MetricsMiddleware` for FastAPI: auto-increment request counters, measure latency histograms
- Instrument WebSocket: message counters (in/out by type), connection gauge, broadcast duration
- Instrument DB: pool stats gauge (active, idle)
- Instrument Redis: pool stats gauge
- **Files**: `app/metrics/prometheus.py`, `app/metrics/middleware.py`, `app/metrics/ws_metrics.py`, `gateway/metrics/ws_collector.py`
- **AC**: All metrics exposed; counters increment on events; histograms capture latency; gauges reflect current state

### 4.2 Metrics endpoint
- GET /metrics: expose Prometheus text format
- Restrict to internal network only (middleware check for source IP or API key)
- **Files**: `app/metrics/router.py`
- **AC**: /metrics returns valid Prometheus format; accessible from internal network; blocked from public

## Phase 5: Security Hardening

### 5.1 Security headers middleware
- Implement FastAPI middleware that adds all security headers to every response
- CSP in report-only mode when ENVIRONMENT=staging, enforced when ENVIRONMENT=production
- **Files**: `app/security/headers_middleware.py`
- **AC**: All headers present on every response; CSP mode correct per environment; no PWA functionality broken

### 5.2 SSRF protection
- Implement `validate_url()` function: resolve hostname to IP, check against blocked ranges and hostnames
- Wrap all outbound HTTP calls (httpx/aiohttp) with URL validation
- Block private IPs, link-local, cloud metadata, IPv6 equivalents
- Log security warning on blocked attempt
- **Files**: `app/security/ssrf_validator.py`
- **AC**: Internal IPs blocked; cloud metadata blocked; IPv6 equivalents blocked; legitimate external URLs allowed; security warning logged

### 5.3 Security audit test suite
- Create automated security tests:
  - Verify all endpoints have RBAC decorators (scan router files)
  - Verify no raw SQL string interpolation (scan service files)
  - Verify all rate limiting configs are active
  - Verify WebSocket JWT re-validation interval
  - Verify file upload size limits
  - Verify password hashing rounds >= 12
- **Files**: `app/security/audit_checklist.py` (or `tests/test_security_audit.py`)
- **AC**: All security checks pass; any regression (missing RBAC, raw SQL) fails the test

## Phase 6: Performance

### 6.1 k6 load test scripts
- Create `api-load.js`: 500 VUs, 5 min, GET /tables + POST /orders
- Create `ws-load.js`: 400 WS connections, broadcast messages, measure delivery time
- Create `mixed-load.js`: 300 HTTP + 150 WS + 50 admin, 5 min
- Create `spike-test.js`: ramp from 100 to 500 VUs in 30s, hold 2 min
- Define thresholds: API P95 < 100ms, WS broadcast < 200ms, error rate < 1%
- **Files**: `load-tests/k6/api-load.js`, `load-tests/k6/ws-load.js`, `load-tests/k6/mixed-load.js`, `load-tests/k6/spike-test.js`, `load-tests/k6/thresholds.json`
- **AC**: All 4 test scenarios run without script errors; thresholds defined; results exportable

### 6.2 Load test runner & comparison
- Create `run-load-tests.sh`: runs all 4 scenarios sequentially against target URL
- Create `compare-results.sh`: compares latest results with previous run, highlights regressions
- Archive results in `load-tests/results/{date}/`
- **Files**: `load-tests/scripts/run-load-tests.sh`, `load-tests/scripts/compare-results.sh`
- **AC**: Runner executes all tests; results archived with timestamp; comparison highlights P95 changes

## Phase 7: Production Documentation

### 7.1 Docker Compose production
- Create `docker-compose.prod.yml` with all services: api (x2), gateway (x2), worker, postgresql, redis, nginx, prometheus
- Include: health checks, resource limits, volume mounts, restart policies
- Include: nginx config for TLS termination, reverse proxy, static file serving
- **Files**: `docs/deployment/docker-compose.prod.yml`, `docs/deployment/nginx.conf`
- **AC**: `docker compose up` starts all services; health checks pass; nginx routes traffic correctly

### 7.2 Environment variables reference
- Document every environment variable: name, required/optional, default, type, description, example
- Group by service (API, Gateway, Worker, shared)
- **Files**: `docs/deployment/env-vars-reference.md`
- **AC**: Every var from Settings class documented; no undocumented vars; examples for all

### 7.3 Operational runbook
- Document procedures: deployment (staging + prod), rollback, common issues + resolution
- Document monitoring: Prometheus queries for common alerts, dashboard setup
- Document backup: PostgreSQL pg_dump schedule, point-in-time recovery steps, Redis RDB/AOF
- Document restore: PostgreSQL pg_restore, Redis recovery, full disaster recovery
- **Files**: `docs/operations/runbook.md`, `docs/operations/monitoring-guide.md`, `docs/operations/backup-restore.md`
- **AC**: Runbook covers all operational scenarios; procedures are step-by-step; tested against staging

### 7.4 Security audit report
- Document audit findings: all endpoints checked, RBAC coverage, rate limiting coverage
- Document: injection prevention status, XSS prevention via CSP, SSRF protection scope
- List any known risks with severity and mitigation
- **Files**: `docs/security/security-audit-report.md`
- **AC**: All endpoints listed with RBAC status; all security controls documented; risks rated and mitigated
