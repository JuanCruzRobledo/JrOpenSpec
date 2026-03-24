---
sprint: 16
artifact: proposal
status: complete
---

# Proposal: CI/CD, Monitoring y Security Hardening

## Intent

Prepare the entire Buen Sabor platform for production deployment with automated CI/CD pipelines, comprehensive monitoring and alerting, security hardening across all layers, performance validation, and operational documentation.

## Scope

### In Scope
- CI/CD pipeline: lint (ruff + mypy) + tests per PR, Docker build, staging auto-deploy, production manual deploy (approval gate)
- Environment validation: script verifying all required env vars, fail-fast on missing
- Health checks: /api/health/live (liveness), /api/health/ready (PostgreSQL + Redis + circuit breaker + retry queue), Gateway health
- Prometheus metrics: request counters, error counters, auth failure counters, rate-limited counters, WS connections gauge, DB pool gauge, Redis pool gauge, latency histograms, broadcast duration histograms
- Structured JSON logging across all services
- Security headers: CSP, HSTS, X-Frame-Options DENY, X-Content-Type-Options nosniff
- SSRF protection: block internal IPs + cloud metadata endpoints
- Security audit: RBAC verification on all endpoints, rate limiting coverage, blacklist enforcement, SQL injection prevention, XSS prevention
- Performance targets: 400-600 concurrent users, broadcast <200ms/400 users, API <100ms P95
- Load testing with k6 or locust
- Documentation: Docker Compose production config, env vars reference, runbook, backup/restore procedures

### Out of Scope
- Kubernetes/ECS orchestration
- Multi-region deployment
- Automated scaling policies
- APM (Application Performance Monitoring) integration
- PCI DSS compliance for payment data

## Modules

| Module | Description |
|--------|-------------|
| `ci-cd` | GitHub Actions pipeline |
| `env-validation` | Environment variable checker |
| `health` | Health check endpoints |
| `metrics` | Prometheus metrics instrumentation |
| `logging` | Structured JSON logging |
| `security-headers` | HTTP security headers middleware |
| `ssrf-protection` | SSRF mitigation middleware |
| `security-audit` | Comprehensive security review |
| `performance` | Load testing + optimization |
| `docs` | Operational documentation |

## Approach

1. **CI/CD pipeline** — GitHub Actions with lint/type-check/test/build/deploy stages
2. **Env validation** — Python script checking all required vars, run at container startup
3. **Health endpoints** — enhance Sprint 12 health checks with full subsystem coverage
4. **Prometheus** — instrument all request paths, WebSocket operations, pool stats
5. **Structured logging** — JSON format for all services, correlation IDs across requests
6. **Security headers** — FastAPI middleware for all HTTP responses
7. **SSRF protection** — URL validation middleware blocking private/internal ranges
8. **Security audit** — systematic review of all endpoints for RBAC, injection, XSS
9. **Load testing** — k6 scripts for API + WebSocket load, targeting 400-600 concurrent
10. **Documentation** — Docker Compose prod, env reference, runbook, backup procedures

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| CI pipeline too slow (>10 min) | Medium — developer friction | Parallelize lint/test/build; cache dependencies; split unit/integration tests |
| Health check false negatives during deployment | High — traffic routed to unready pod | Startup probe with longer initial delay; ready check only after warm-up |
| CSP too restrictive breaking PWA functionality | Medium — broken features in prod | Test CSP in staging first; use report-only mode initially |
| Load test revealing bottleneck too late | High — poor production performance | Run load tests in staging before every release; set performance gates in CI |
| Documentation becoming outdated | Medium — ops confusion | Docs generated/validated from code where possible; runbook review on each release |

## Rollback

- CI/CD: revert workflow files; no impact on application
- Security headers: remove middleware; headers disappear from responses
- SSRF protection: remove middleware; URL validation stops (revert to unchecked)
- Monitoring: remove instrumentation; metrics endpoints return empty
- Documentation: no runtime impact
- All changes are additive and non-destructive
