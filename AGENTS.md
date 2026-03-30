# Code Review Rules — JrOpenSpec (Integrador)

## General
- Never use `console.*` or `print()` — use the centralized logger
- IDs: BigInteger in backend, String in frontend (`String(backendId)`)
- Prices stored in cents (e.g. 12550 = $125.50)
- Status values: UPPERCASE in backend, lowercase in frontend
- UI language: Spanish; code comments: English

## Python / FastAPI
- Routers must be THIN: only `Depends`, `PermissionContext`, and service call — zero business logic
- Never use `db.commit()` directly — always `safe_commit(db)`
- SQLAlchemy boolean checks: `.is_(True)` — never `== True`
- Use `with_for_update()` for billing and round operations (race condition prevention)
- CRUDFactory is deprecated — use Domain Services always
- Never instantiate models inside routers

## SQLAlchemy / Alembic
- All seed data for system rows must use `WHERE NOT EXISTS` (not `ON CONFLICT`) when `tenant_id IS NULL`
- Cross-reaction inserts must use `LEAST/GREATEST` with subselects — never hardcode IDs
- Junction models must declare `relationship()` to parent entities (prevents N+1)
- Use `selectinload().joinedload()` chains — never fire queries inside per-row loops

## TypeScript / React
- Never destructure Zustand stores: `const { items } = useStore()` causes infinite re-renders
- Always use selectors: `const items = useStore(selectItems)`
- Use `useShallow` for arrays/computed values from stores
- React 19 forms: use `useActionState` — not `useState + handlers`
- HelpButton required on all Dashboard pages

## Testing
- Backend: use real PostgreSQL via `TEST_DATABASE_URL` — no mocking the DB
- Rate limiter must be disabled by default in conftest (`limiter.enabled = False`)
- Use `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` or `@pytest.mark.anyio` decorators
- Frontend: Vitest + React Testing Library — no Enzyme

## SDD Workflow
- No code without an approved spec
- Routers: THIN — delegate to services
- Services: domain logic only — no HTTP concerns
- Never skip the verify phase before archiving
