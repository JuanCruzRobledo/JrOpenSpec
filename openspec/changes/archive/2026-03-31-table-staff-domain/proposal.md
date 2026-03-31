---
sprint: 5
artifact: proposal
status: complete
---

# SDD Proposal — Sprint 5: Mesas, Sectores y Personal

## Status: APPROVED

## Executive Summary

Sprint 5 delivers the physical restaurant structure management (sectors + tables) with a real-time visual grid, staff CRUD with RBAC enforcement, and daily waiter-to-sector assignments. This sprint bridges the gap between the menu domain (Sprint 4) and the order-taking domain (Sprint 6+), by establishing the physical layout that orders attach to. Key innovations: a finite state machine for table statuses with 6 color-coded states, batch table creation, urgency-based sorting, and a shift-based assignment model.

---

## 1. Intent

Provide restaurant operators with:
1. **Spatial management** — Define sectors (interior, terraza, barra, VIP) and place tables within them, with visual feedback on real-time status.
2. **Staff management** — CRUD for restaurant personnel with RBAC-enforced role assignment and email uniqueness per tenant.
3. **Operational assignments** — Daily waiter-to-sector mappings per shift (morning/afternoon/night), enabling order routing and responsibility tracking.
4. **Table lifecycle** — A state machine governing table status transitions with temporal tracking (when was the order placed? when was it fulfilled?), urgency sorting, and automated archival.

---

## 2. Scope

### In Scope
- **Sector CRUD**: Create, read, update, soft-delete sectors with type classification and capacity tracking
- **Table CRUD**: Individual and batch creation, alphanumeric code generation (sector prefix + number), capacity, sector assignment
- **Table Visual Grid**: Color-coded card grid (6 states x 6 colors), filterable by branch + status, sorted by urgency
- **Table State Machine**: 6 states (libre → ocupada → pedido_solicitado → pedido_cumplido → cuenta → inactiva), transition rules with timestamp tracking
- **Table Archival**: When cuenta is requested → save session to history → reset table to libre
- **Staff CRUD**: Paginated table with real-time search, create with role assignment (ADMIN creates any role, MANAGER creates all except ADMIN), email unique per tenant, DNI field, hire date
- **Roles Matrix View**: Read-only view showing permissions per role (from RBAC Strategy Pattern)
- **Waiter-Sector Assignment**: Daily assignment of waiters to sectors per shift, model WaiterSectorAssignment with date field, only current-day assignments are active
- **Backend RBAC**: All endpoints protected with appropriate permission checks

### Out of Scope
- Real-time WebSocket updates for table status (Sprint 6+, via ws_gateway)
- Table reservations / booking system (future sprint)
- Floor plan visual editor (drag-and-drop table positioning)
- Staff scheduling / shift management beyond daily assignments
- Payroll or HR features
- Table merge / split operations

### Modules Affected

| Module | Changes |
|--------|---------|
| `shared/models/room/` | Update `Sector`, `Table` models; add new fields |
| `shared/models/services/` | Update `WaiterSectorAssignment` model |
| `shared/enums.py` | Add `SectorType`, `TableStatus`, `ShiftType` enums |
| `shared/repositories/` | New `SectorRepository`, `TableRepository`, `StaffRepository`, `AssignmentRepository` |
| `shared/services/` | New `SectorService`, `TableService`, `StaffService`, `AssignmentService` |
| `rest_api/routers/` | New `sectors.py`, `tables.py`, `staff.py`, `assignments.py` |
| `rest_api/schemas/` | New schemas for all 4 domains |
| `dashboard/src/pages/` | New `SectorsPage`, `TablesPage`, `StaffPage`, `AssignmentsPage`, `RolesPage` |
| `dashboard/src/stores/` | New `table.store.ts`, `sector.store.ts`, `staff.store.ts`, `assignment.store.ts` |
| `dashboard/src/services/` | New `sector.service.ts`, `table.service.ts`, `staff.service.ts`, `assignment.service.ts` |
| `dashboard/src/components/` | New `TableGrid`, `TableCard`, `StatusLegend`, `BatchCreateForm`, `AssignmentMatrix`, `RolesMatrix` |

---

## 3. Approach

### 3.1 Backend
- Extend existing `Sector` and `Table` models from Sprint 1 with the new fields (type, capacity, status enum, timestamps)
- Implement table state machine as a service-layer concern (not DB triggers) — `TableService.transition_status()` validates allowed transitions and records timestamps
- Batch table creation via a dedicated endpoint that generates codes: `{sector_prefix}{number}` (e.g., `INT-01`, `TER-05`, `VIP-01`)
- Staff management reuses the existing `User` model but adds `dni` and `hired_at` fields; role assignment follows existing RBAC strategy
- MANAGER role CANNOT assign ADMIN role — enforced at service layer with explicit check
- WaiterSectorAssignment uses a composite key of (waiter_id, sector_id, date, shift) to prevent duplicate assignments
- All endpoints scoped to tenant + branch via existing middleware

### 3.2 Frontend
- Table grid uses CSS Grid with `grid-auto-flow: dense` for responsive layout
- Each `TableCard` shows: table code, capacity, current status color, time since last state change
- Urgency sorting algorithm: `cuenta (5) > pedido_solicitado (4) > pedido_cumplido (3) > ocupada (2) > libre (1) > inactiva (0)`
- Staff page uses the generic `useCrud` hook from Sprint 3 with added search debounce
- Assignment page: matrix UI where rows = waiters, columns = sectors, cells = shift toggles
- Roles page: static matrix rendered from the RBAC permission definitions

### 3.3 State Management
- `table.store.ts` — tables by sector, selected table, status filter, polling interval for refresh
- `sector.store.ts` — sectors list, selected sector for filtering
- `staff.store.ts` — staff list with search/pagination state
- `assignment.store.ts` — today's assignments, selected date (default: today)

---

## 4. Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Table state transitions triggered concurrently (e.g., two waiters changing same table) | Medium | High | Optimistic locking via `version` column on tables; retry on conflict |
| Batch creation generates duplicate codes if sector prefix changes | Low | Medium | Validate uniqueness at DB level (UNIQUE constraint on sector_id + number) |
| Staff email uniqueness conflict across branches (same tenant) | Medium | Medium | UNIQUE(tenant_id, email) already exists on users table |
| Assignment date validation bypass (assigning for future dates) | Low | Low | Service layer enforces `date == today()` for active assignments; allow future dates for planning but mark as "scheduled" |
| Large number of tables (100+) causing grid performance issues | Low | Medium | Virtualization not needed for 100 cards; revisit if >500 |

---

## 5. Rollback Strategy

- **Database**: Each Alembic migration has a `downgrade()` that drops new columns/tables. Run `alembic downgrade -1` per migration.
- **Backend**: New routers are registered independently in `main.py`; comment out the `include_router` lines to disable.
- **Frontend**: New pages are behind route definitions; remove routes to hide features. New sidebar items are conditional on feature flag.
- **Data**: Soft delete means no data loss. Batch-created tables can be bulk soft-deleted by sector.

---

## 6. Dependencies

| Dependency | Sprint | Status | Notes |
|------------|--------|--------|-------|
| User model + RBAC | Sprint 2 | Designed | Users table, roles, PermissionChecker |
| Branch model + tenant scoping | Sprint 1 | Designed | TenantScopedMixin, branch_id filtering |
| Dashboard shell + routing | Sprint 3 | Designed | Layout, sidebar, generic CRUD hook |
| Sector/Table base models | Sprint 1 | Designed | Basic models exist, need extension |

---

## Next Recommended
`sdd-spec` — Full requirements, data models, API contracts, UI specs, scenarios.
