---
sprint: 5
artifact: tasks
status: complete
---

# SDD Tasks — Sprint 5: Mesas, Sectores y Personal

## Status: APPROVED

---

## Phase 1: Database Foundation (Enums, Models, Migrations)

### Task 1.1: New Enums
**Description**: Add Sprint 5 enums to the shared enums module.
**Files**:
- `shared/enums.py` — Add: `SectorType`, `TableStatus`, `ShiftType`, `TABLE_TRANSITIONS` dict, `TABLE_URGENCY_SCORE` dict, `SECTOR_PREFIX_MAP` dict.
**Acceptance Criteria**:
- `SectorType` has values: `interior`, `terraza`, `barra`, `vip`
- `TableStatus` has values: `libre`, `ocupada`, `pedido_solicitado`, `pedido_cumplido`, `cuenta`, `inactiva`
- `ShiftType` has values: `morning`, `afternoon`, `night`
- `TABLE_TRANSITIONS` maps each status to its list of allowed target statuses (per state machine in Design S2.2)
- `TABLE_URGENCY_SCORE` maps each status to its urgency integer: cuenta=50, pedido_solicitado=40, pedido_cumplido=30, ocupada=20, libre=10, inactiva=0
- `SECTOR_PREFIX_MAP` maps SectorType to prefix strings: interior->INT, terraza->TER, barra->BAR, vip->VIP
- All enums extend `str, Enum` for JSON serialization compatibility

### Task 1.2: Update Sector Model
**Description**: Extend the existing Sector model with new fields.
**Files**:
- `shared/models/room/sector.py` — Add columns: `type` (String(20), SectorType), `prefix` (String(10)), `capacity` (Integer). Add constraints: `ck_sector_capacity_positive`, `uq_sectors_branch_name`, `uq_sectors_branch_prefix`. Add relationship to `WaiterSectorAssignment`.
**Dependencies**: Task 1.1
**Acceptance Criteria**:
- Sector model has `type`, `prefix`, `capacity` columns
- `branch_id` + `name` has UNIQUE constraint
- `branch_id` + `prefix` has UNIQUE constraint
- `capacity > 0` CHECK constraint exists
- Relationship `tables` uses `selectin` loading strategy
- Relationship `assignments` links to `WaiterSectorAssignment`

### Task 1.3: Update Table Model
**Description**: Extend the existing Table model with status tracking and optimistic locking.
**Files**:
- `shared/models/room/table.py` — Add columns: `code` (String(15)), `status` (String(25), default LIBRE), `version` (Integer, default 1), `status_changed_at` (TIMESTAMPTZ), `occupied_at` (TIMESTAMPTZ), `order_requested_at` (TIMESTAMPTZ), `order_fulfilled_at` (TIMESTAMPTZ), `check_requested_at` (TIMESTAMPTZ), `session_count` (Integer, default 0). Add constraints and indexes per Design S1.2.
**Dependencies**: Task 1.1
**Acceptance Criteria**:
- Table model has all 10 new columns
- `capacity` has CHECK constraint: `>= 1 AND <= 20`
- `number` has CHECK constraint: `> 0`
- Partial UNIQUE index on `(sector_id, number)` WHERE `deleted_at IS NULL`
- Composite index on `(sector_id, status)` WHERE `deleted_at IS NULL`
- `version` defaults to 1 and is NOT NULL

### Task 1.4: Update/Create TableSession Model
**Description**: Create or update the TableSession model for archiving completed table sessions.
**Files**:
- `shared/models/room/table_session.py` — Full model with: `table_id` (FK), `opened_at`, `closed_at`, `order_requested_at`, `order_fulfilled_at`, `check_requested_at` (all TIMESTAMPTZ), `duration_minutes` (Integer), `status` (String(20), default "closed"). Add index on `(table_id, closed_at)`.
**Dependencies**: Task 1.3
**Acceptance Criteria**:
- TableSession inherits AuditMixin + TenantScopedMixin
- All timestamp fields present
- `duration_minutes` is computed and stored (not a DB-level computed column)
- Index on `(table_id, closed_at)` exists
- Relationship `table` links back to Table model

### Task 1.5: Add User Model Fields
**Description**: Add `dni` and `hired_at` fields to the existing User model.
**Files**:
- `shared/models/core/user.py` — Add: `dni` (String(20), nullable), `hired_at` (Date, nullable).
**Acceptance Criteria**:
- `dni` is optional String(20)
- `hired_at` is optional Date type
- No existing functionality is broken (fields are nullable)

### Task 1.6: Create WaiterSectorAssignment Model
**Description**: Create the assignment model linking waiters to sectors by date and shift.
**Files**:
- `shared/models/services/waiter_sector_assignment.py` — Full model with: `waiter_id` (FK users.id), `sector_id` (FK sectors.id), `date` (Date), `shift` (String(15), ShiftType). Add UNIQUE constraint on `(waiter_id, sector_id, date, shift)`. Add indexes per Design S1.5.
**Dependencies**: Task 1.2, Task 1.5
**Acceptance Criteria**:
- UNIQUE constraint on all 4 fields
- Index on `(date, shift)` with partial WHERE
- Index on `(waiter_id, date)` with partial WHERE
- Relationships: `waiter` -> User, `sector` -> Sector
- Inherits AuditMixin + TenantScopedMixin

### Task 1.7: Update Models __init__.py
**Description**: Register all new/updated models in the shared models init for Alembic discovery.
**Files**:
- `shared/models/__init__.py` — Ensure all models are imported: Sector, Table, TableSession, WaiterSectorAssignment, updated User.
**Dependencies**: Tasks 1.2-1.6
**Acceptance Criteria**:
- All models importable from `shared.models`
- Alembic `autogenerate` detects all new tables/columns

### Task 1.8: Alembic Migration
**Description**: Generate and verify the Alembic migration for all Sprint 5 schema changes.
**Files**:
- `alembic/versions/XXX_sprint5_tables_sectors_staff.py` — Auto-generated migration covering: sector new columns, table new columns, table_sessions table, user new columns, waiter_sector_assignments table, all indexes and constraints.
**Dependencies**: Task 1.7
**Acceptance Criteria**:
- Migration `upgrade()` creates all new columns, tables, indexes, constraints
- Migration `downgrade()` cleanly reverses all changes
- Running `alembic upgrade head` succeeds
- Running `alembic downgrade -1` then `upgrade head` succeeds (idempotent)

---

## Phase 2: Backend Repositories

### Task 2.1: Sector Repository
**Description**: Create repository for sector CRUD operations.
**Files**:
- `shared/repositories/sector_repository.py` — Class `SectorRepository(TenantScopedRepository[Sector])` with methods: `get_by_branch(branch_id, include_inactive=False)`, `get_by_name(branch_id, name)`, `get_by_prefix(branch_id, prefix)`, `count_active_tables(sector_id)`.
**Dependencies**: Task 1.2
**Acceptance Criteria**:
- All queries auto-filter by `tenant_id` via TenantScopedRepository
- `get_by_branch` returns sectors ordered by type then name
- `get_by_name` is case-insensitive
- `count_active_tables` returns count of tables where `is_active=True` and `deleted_at IS NULL`

### Task 2.2: Table Repository
**Description**: Create repository for table CRUD and batch operations.
**Files**:
- `shared/repositories/table_repository.py` — Class `TableRepository(TenantScopedRepository[Table])` with methods: `get_by_branch(branch_id, sector_id=None, status=None)`, `get_for_update(table_id)` (SELECT FOR UPDATE), `get_max_number(sector_id)`, `get_existing_numbers(sector_id, numbers: list[int])`, `bulk_create(tables: list[Table])`, `get_by_sector_and_number(sector_id, number)`.
**Dependencies**: Task 1.3
**Acceptance Criteria**:
- `get_by_branch` supports optional filtering by sector_id and status
- `get_for_update` uses `with_for_update()` for row-level locking
- `get_max_number` returns MAX(number) for a sector, or None if empty
- `get_existing_numbers` returns list of numbers that already exist
- `bulk_create` uses `session.add_all()` for atomic batch insert

### Task 2.3: TableSession Repository
**Description**: Create repository for table session history.
**Files**:
- `shared/repositories/table_session_repository.py` — Class `TableSessionRepository(TenantScopedRepository[TableSession])` with methods: `get_by_table(table_id, limit=50)`, `create(session: TableSession)`.
**Dependencies**: Task 1.4
**Acceptance Criteria**:
- `get_by_table` returns sessions ordered by `closed_at` descending
- Respects tenant scoping

### Task 2.4: Staff Repository
**Description**: Create repository for staff (user) CRUD with search.
**Files**:
- `shared/repositories/staff_repository.py` — Class `StaffRepository(TenantScopedRepository[User])` with methods: `search(q: str, role: str = None, is_active: bool = True, page: int = 1, limit: int = 20)`, `get_by_email(email: str)`, `get_waiters(is_active=True)`.
**Dependencies**: Task 1.5
**Acceptance Criteria**:
- `search` uses ILIKE for case-insensitive matching on `full_name` and `email`
- `search` supports pagination with total count
- `search` supports optional `role` filter
- `get_waiters` returns only users with `role = WAITER`

### Task 2.5: Assignment Repository
**Description**: Create repository for waiter-sector assignments.
**Files**:
- `shared/repositories/assignment_repository.py` — Class `AssignmentRepository(TenantScopedRepository[WaiterSectorAssignment])` with methods: `get_by_date(branch_id, date)`, `get_by_waiter_date(waiter_id, date)`, `delete_by_date_shift(branch_id, date, shift)`, `bulk_create(assignments: list[WaiterSectorAssignment])`, `has_active_assignments(waiter_id, date)`.
**Dependencies**: Task 1.6
**Acceptance Criteria**:
- `get_by_date` returns assignments with eager-loaded waiter and sector relationships
- `delete_by_date_shift` deletes all assignments for a specific date+shift in a branch (for replace-all pattern)
- `has_active_assignments` checks if a waiter has any assignments for today (used before staff deletion)
- `bulk_create` is atomic

---

## Phase 3: Backend Services

### Task 3.1: Sector Service
**Description**: Business logic for sector management including prefix generation.
**Files**:
- `shared/services/sector_service.py` — Class `SectorService` with methods: `list_sectors(branch_id, include_inactive)`, `create_sector(branch_id, data)`, `update_sector(sector_id, data)`, `delete_sector(sector_id)`, `_generate_prefix(sector_type, branch_id)`.
**Dependencies**: Task 2.1
**Acceptance Criteria**:
- `create_sector` auto-generates prefix using the algorithm from Design S6
- `create_sector` validates name uniqueness within branch (case-insensitive)
- `update_sector`: if type changes, prefix is recalculated and all table codes under this sector are regenerated
- `delete_sector` checks for non-libre active tables before soft-deleting; cascades soft-delete to all tables
- Returns proper error types: `ConflictError`, `NotFoundError`, `ValidationError`

### Task 3.2: Table Service
**Description**: Business logic for table management including state machine and archival.
**Files**:
- `shared/services/table_service.py` — Class `TableService` with methods: `list_tables(branch_id, sector_id, status)`, `create_table(branch_id, data)`, `batch_create(branch_id, data)`, `update_table(table_id, data)`, `delete_table(table_id)`, `transition_status(table_id, new_status, version)`, `_archive_session(table)`, `_apply_side_effects(table, from_status, to_status)`.
**Dependencies**: Tasks 2.2, 2.3, 1.1 (TABLE_TRANSITIONS, TRANSITION_SIDE_EFFECTS)
**Acceptance Criteria**:
- `transition_status` implements full optimistic locking (Design S2.4)
- `transition_status` validates against `TABLE_TRANSITIONS` dict
- `transition_status` applies side effects per `TRANSITION_SIDE_EFFECTS` dict (Design S2.3)
- `_archive_session` creates TableSession with all timestamps and duration calculation
- `_archive_session` resets table: status=libre, clears temporal fields, increments session_count
- `batch_create` implements the algorithm from Design S7 with collision detection
- `create_table` auto-generates code: `{sector.prefix}-{number:02d}`
- `update_table` only allowed when status is `libre` or `inactiva`; regenerates code if sector changes
- `delete_table` only allowed when status is `libre` or `inactiva`

### Task 3.3: Staff Service
**Description**: Business logic for staff CRUD with role assignment validation.
**Files**:
- `shared/services/staff_service.py` — Class `StaffService` with methods: `list_staff(q, role, is_active, page, limit)`, `create_staff(data, current_user)`, `update_staff(user_id, data, current_user)`, `delete_staff(user_id)`, `_validate_role_assignment(assigner_role, target_role)`.
**Dependencies**: Tasks 2.4, 2.5
**Acceptance Criteria**:
- `_validate_role_assignment` enforces: ADMIN can assign any, MANAGER can assign all except ADMIN, others get 403
- `create_staff` checks email uniqueness per tenant, hashes password, sets `hired_at` default to today
- `update_staff` re-validates role assignment if role is being changed
- `delete_staff` checks for active today's assignments before soft-deleting (409 if assignments exist)
- Password is NEVER returned in any response

### Task 3.4: Roles Service
**Description**: Service to expose the RBAC permission matrix.
**Files**:
- `shared/services/roles_service.py` — Class `RolesService` with method: `get_permissions_matrix()` returning all roles with their permissions, sourced from the Strategy Pattern classes.
**Dependencies**: Sprint 2 RBAC strategies
**Acceptance Criteria**:
- Reads permissions directly from each strategy class (`AdminStrategy`, `ManagerStrategy`, etc.)
- Returns structured data: `[{ role, label, permissions[] }]`
- Labels are Spanish: ADMIN->Administrador, MANAGER->Gerente, WAITER->Mozo, KITCHEN->Cocina, READONLY->Solo Lectura
- Includes the NEW permissions from Sprint 5 (sectors:*, tables:*, staff:*, assignments:*)

### Task 3.5: Assignment Service
**Description**: Business logic for waiter-sector daily assignments.
**Files**:
- `shared/services/assignment_service.py` — Class `AssignmentService` with methods: `list_assignments(branch_id, date)`, `bulk_save(branch_id, date, shift, assignments)`, `delete_assignment(assignment_id)`, `_validate_waiter(user_id)`, `_validate_sector(sector_id)`.
**Dependencies**: Tasks 2.5, 2.4
**Acceptance Criteria**:
- `list_assignments` returns assignments grouped by shift: `{ morning: [], afternoon: [], night: [] }`
- `bulk_save` implements delete-and-reinsert for the given date+shift (Design Decision D3)
- `_validate_waiter` checks that user exists, is active, and has role WAITER (422 if not)
- `_validate_sector` checks that sector exists and is active (422 if not)
- Validates all assignments in the bulk request before inserting any (atomic)

---

## Phase 4: Backend API Endpoints

### Task 4.1: Sector Schemas
**Files**: `rest_api/schemas/sector.py`
**Acceptance Criteria**:
- `SectorCreate(name, type)`, `SectorUpdate(name?, type?, capacity?)`, `SectorResponse(id, name, type, prefix, capacity, is_active, table_count, available_tables, created_at)`, `SectorListResponse(data, total)`
- `SectorCreate.name` has max_length=100, `SectorCreate.type` validates against `SectorType` enum

### Task 4.2: Table Schemas
**Files**: `rest_api/schemas/table.py`
**Acceptance Criteria**:
- `TableCreate(number, capacity, sector_id)`, `TableBatchCreate(sector_id, quantity, capacity_base, start_number?)`, `TableUpdate(capacity?, sector_id?)`, `TableStatusUpdate(status, version)`, `TableResponse`, `TableBatchResponse`
- Capacity 1-20, quantity 1-50, status validates against `TableStatus` enum

### Task 4.3: Staff Schemas
**Files**: `rest_api/schemas/staff.py`
**Acceptance Criteria**:
- `StaffCreate(full_name, email, password, role, dni?, hired_at?)`, `StaffUpdate(full_name?, role?, dni?, hired_at?, is_active?)`, `StaffResponse`, `StaffListResponse`
- Password min_length=8, email validated, role validated, StaffResponse NEVER includes password_hash

### Task 4.4: Assignment Schemas
**Files**: `rest_api/schemas/assignment.py`
**Acceptance Criteria**:
- `AssignmentBulkItem(waiter_id, sector_id)`, `AssignmentBulkCreate(date, shift, assignments)`, `AssignmentResponse`, `AssignmentsByShiftResponse`, `AssignmentBulkResponse`

### Task 4.5: Roles Schema
**Files**: `rest_api/schemas/role.py`
**Acceptance Criteria**:
- `RolePermissions(role, label, permissions[])`, `RolesMatrixResponse(roles[])`

### Task 4.6: Sector Router
**Files**: `rest_api/routers/sectors.py`
**Acceptance Criteria**:
- GET / (list), POST / (create), PUT /{id} (update), DELETE /{id} (soft delete)
- All with PermissionChecker, branch-scoped

### Task 4.7: Table Router
**Files**: `rest_api/routers/tables.py`
**Acceptance Criteria**:
- GET / (list+filters+urgency), POST / (create), POST /batch (batch), PUT /{id} (update), DELETE /{id} (soft delete), PATCH /{id}/status (transition)
- 409 on version mismatch, 422 on invalid transition

### Task 4.8: Staff Router
**Files**: `rest_api/routers/staff.py`
**Acceptance Criteria**:
- GET / (list+search+pagination), POST / (create), PUT /{id} (update), DELETE /{id} (soft delete)
- 403 for role assignment violation, tenant-scoped

### Task 4.9: Roles Router
**Files**: `rest_api/routers/roles.py`
**Acceptance Criteria**:
- GET /permissions (matrix), protected by staff:read

### Task 4.10: Assignment Router
**Files**: `rest_api/routers/assignments.py`
**Acceptance Criteria**:
- GET / (list by date), POST /bulk (bulk save), DELETE /{id} (remove)
- Branch-scoped, validates waiter role and sector active status

### Task 4.11: Register Routers in Main App
**Files**: `rest_api/app/main.py`
**Acceptance Criteria**:
- All 5 new routers registered, no route conflicts

### Task 4.12: Update RBAC Strategies with New Permissions
**Files**: `shared/security/rbac/strategy.py`
**Acceptance Criteria**:
- MANAGER gets sectors:*, tables:*, staff:*, assignments:*
- WAITER gets sectors:read, tables:read+write, assignments:read
- READONLY gets sectors:read, tables:read, staff:read, assignments:read
- KITCHEN unchanged, ADMIN unchanged (wildcard)

---

## Phase 5: Frontend Types & Services

### Task 5.1: Frontend Type Definitions
**Files**: `dashboard/src/types/sector.ts`, `table.ts`, `staff.ts`, `role.ts`, `assignment.ts`

### Task 5.2: Sector Service
**Files**: `dashboard/src/services/sector.service.ts`

### Task 5.3: Table Service
**Files**: `dashboard/src/services/table.service.ts`

### Task 5.4: Staff Service
**Files**: `dashboard/src/services/staff.service.ts`

### Task 5.5: Role Service
**Files**: `dashboard/src/services/role.service.ts`

### Task 5.6: Assignment Service
**Files**: `dashboard/src/services/assignment.service.ts`

---

## Phase 6: Frontend Stores

### Task 6.1: Sector Store
**Files**: `dashboard/src/stores/sector.store.ts`

### Task 6.2: Table Store
**Files**: `dashboard/src/stores/table.store.ts`

### Task 6.3: Staff Store
**Files**: `dashboard/src/stores/staff.store.ts`

### Task 6.4: Assignment Store
**Files**: `dashboard/src/stores/assignment.store.ts`

---

## Phase 7: Frontend Components & Pages

### Task 7.1: TableCard Component
**Files**: `dashboard/src/components/tables/TableCard.tsx`

### Task 7.2: TableGrid Component
**Files**: `dashboard/src/components/tables/TableGrid.tsx`

### Task 7.3: TableStatusModal Component
**Files**: `dashboard/src/components/tables/TableStatusModal.tsx`

### Task 7.4: TableBatchForm Component
**Files**: `dashboard/src/components/tables/TableBatchForm.tsx`

### Task 7.5: TableFilters Component
**Files**: `dashboard/src/components/tables/TableFilters.tsx`

### Task 7.6: StatusLegend Component
**Files**: `dashboard/src/components/tables/StatusLegend.tsx`

### Task 7.7: TablesPage (Container)
**Files**: `dashboard/src/pages/TablesPage.tsx`

### Task 7.8: useTableGrid Hook
**Files**: `dashboard/src/hooks/useTableGrid.ts`

### Task 7.9: SectorForm Component
**Files**: `dashboard/src/components/forms/SectorForm.tsx`

### Task 7.10: SectorsPage
**Files**: `dashboard/src/pages/SectorsPage.tsx`

### Task 7.11: StaffForm Component
**Files**: `dashboard/src/components/staff/StaffForm.tsx`

### Task 7.12: StaffSearch Component
**Files**: `dashboard/src/components/staff/StaffSearch.tsx`

### Task 7.13: StaffPage
**Files**: `dashboard/src/pages/StaffPage.tsx`

### Task 7.14: useStaffSearch Hook
**Files**: `dashboard/src/hooks/useStaffSearch.ts`

### Task 7.15: PermissionsMatrix Component
**Files**: `dashboard/src/components/roles/PermissionsMatrix.tsx`

### Task 7.16: RolesPage
**Files**: `dashboard/src/pages/RolesPage.tsx`

### Task 7.17: AssignmentMatrix Component
**Files**: `dashboard/src/components/assignments/AssignmentMatrix.tsx`

### Task 7.18: ShiftSelector Component
**Files**: `dashboard/src/components/assignments/ShiftSelector.tsx`

### Task 7.19: AssignmentsPage
**Files**: `dashboard/src/pages/AssignmentsPage.tsx`

### Task 7.20: useAssignmentMatrix Hook
**Files**: `dashboard/src/hooks/useAssignmentMatrix.ts`

### Task 7.21: Update Sidebar Navigation
**Files**: `dashboard/src/components/layout/Sidebar.tsx`

### Task 7.22: Update Router Configuration
**Files**: `dashboard/src/router/routes.ts`, `dashboard/src/router/index.tsx`

---

## Phase Summary

| Phase | Tasks | Key Deliverables |
|-------|-------|-----------------|
| 1: DB Foundation | 1.1-1.8 | Enums, models, migration |
| 2: Repositories | 2.1-2.5 | Data access layer |
| 3: Services | 3.1-3.5 | Business logic |
| 4: API Endpoints | 4.1-4.12 | REST API + schemas + RBAC |
| 5: FE Types/Services | 5.1-5.6 | TypeScript types + API services |
| 6: FE Stores | 6.1-6.4 | Zustand state management |
| 7: FE Components | 7.1-7.22 | Pages, components, hooks, routing |

**Total**: 47 tasks across 7 phases
**Estimated files**: ~55 new/modified files

---

## Critical Implementation Notes

1. **React 19 Zustand Rule**: NEVER destructure from Zustand stores. ALWAYS use individual selectors: `const x = useStore((s) => s.x)`. This is a HARD RULE.

2. **TailwindCSS 4**: Uses `@theme` in CSS for custom properties. No `tailwind.config.ts` needed. Use utility classes directly.

3. **Price Convention**: All prices in integer cents. Frontend formats for display.

4. **ID Convention**: Backend uses `int`, frontend uses `string` for IDs.

5. **Soft Delete**: All models use `is_active` + `deleted_at`. BaseRepository auto-filters `deleted_at IS NULL`.

6. **Tenant Scoping**: All queries auto-filter by `tenant_id` via TenantScopedRepository + contextvars middleware.

7. **Error Types**: Use project exceptions: `NotFoundError` (404), `ConflictError` (409), `ValidationError` (422), `ForbiddenError` (403).

8. **Table State Machine**: Transitions are validated at the SERVICE layer, not the DB layer. The `TABLE_TRANSITIONS` dict is the single source of truth.
