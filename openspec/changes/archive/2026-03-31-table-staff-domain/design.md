---
sprint: 5
artifact: design
status: complete
---

# SDD Design — Sprint 5: Mesas, Sectores y Personal

## Status: APPROVED

---

## 1. Database Schema (Physical Design)

### 1.1 Migration: Update Sectors Table

```sql
-- Alembic migration: add new columns to sectors
ALTER TABLE sectors ADD COLUMN type VARCHAR(20) NOT NULL DEFAULT 'interior';
ALTER TABLE sectors ADD COLUMN prefix VARCHAR(10) NOT NULL DEFAULT 'INT';
ALTER TABLE sectors ADD COLUMN capacity INTEGER NOT NULL DEFAULT 0;

-- Add constraints
ALTER TABLE sectors ADD CONSTRAINT ck_sector_capacity_positive CHECK (capacity > 0);
ALTER TABLE sectors ADD CONSTRAINT uq_sectors_branch_name UNIQUE (branch_id, name);
ALTER TABLE sectors ADD CONSTRAINT uq_sectors_branch_prefix UNIQUE (branch_id, prefix);

-- Index for branch filtering
CREATE INDEX ix_sectors_branch_active ON sectors(branch_id) WHERE deleted_at IS NULL;
```

### 1.2 Migration: Update Tables Table

```sql
-- Alembic migration: update tables with new columns
ALTER TABLE tables ADD COLUMN code VARCHAR(15) NOT NULL DEFAULT '';
ALTER TABLE tables ADD COLUMN status VARCHAR(25) NOT NULL DEFAULT 'libre';
ALTER TABLE tables ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE tables ADD COLUMN status_changed_at TIMESTAMPTZ;
ALTER TABLE tables ADD COLUMN occupied_at TIMESTAMPTZ;
ALTER TABLE tables ADD COLUMN order_requested_at TIMESTAMPTZ;
ALTER TABLE tables ADD COLUMN order_fulfilled_at TIMESTAMPTZ;
ALTER TABLE tables ADD COLUMN check_requested_at TIMESTAMPTZ;
ALTER TABLE tables ADD COLUMN session_count INTEGER NOT NULL DEFAULT 0;

-- Constraints
ALTER TABLE tables ADD CONSTRAINT ck_table_capacity_range CHECK (capacity >= 1 AND capacity <= 20);
ALTER TABLE tables ADD CONSTRAINT ck_table_number_positive CHECK (number > 0);

-- Indexes
CREATE INDEX ix_tables_sector_status ON tables(sector_id, status) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_tables_sector_number ON tables(sector_id, number) WHERE deleted_at IS NULL;
```

### 1.3 Migration: Update/Create TableSession

```sql
CREATE TABLE IF NOT EXISTS table_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    table_id INTEGER NOT NULL REFERENCES tables(id),
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ NOT NULL,
    order_requested_at TIMESTAMPTZ,
    order_fulfilled_at TIMESTAMPTZ,
    check_requested_at TIMESTAMPTZ,
    duration_minutes INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'closed',
    -- AuditMixin
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    created_by INTEGER,
    updated_by INTEGER
);

CREATE INDEX ix_table_sessions_table_date ON table_sessions(table_id, closed_at);
CREATE INDEX ix_table_sessions_tenant ON table_sessions(tenant_id) WHERE deleted_at IS NULL;
```

### 1.4 Migration: Add User Fields

```sql
ALTER TABLE users ADD COLUMN dni VARCHAR(20);
ALTER TABLE users ADD COLUMN hired_at DATE;
```

### 1.5 Migration: Create WaiterSectorAssignment

```sql
CREATE TABLE waiter_sector_assignments (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    waiter_id INTEGER NOT NULL REFERENCES users(id),
    sector_id INTEGER NOT NULL REFERENCES sectors(id),
    date DATE NOT NULL,
    shift VARCHAR(15) NOT NULL,
    -- AuditMixin
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    created_by INTEGER,
    updated_by INTEGER
);

ALTER TABLE waiter_sector_assignments ADD CONSTRAINT uq_assignment_waiter_sector_date_shift
    UNIQUE (waiter_id, sector_id, date, shift);
CREATE INDEX ix_assignments_date_shift ON waiter_sector_assignments(date, shift) WHERE deleted_at IS NULL;
CREATE INDEX ix_assignments_waiter_date ON waiter_sector_assignments(waiter_id, date) WHERE deleted_at IS NULL;
CREATE INDEX ix_assignments_tenant ON waiter_sector_assignments(tenant_id) WHERE deleted_at IS NULL;
```

### 1.6 Index Summary

| Table | Index | Columns | Type | Purpose |
|-------|-------|---------|------|---------|
| sectors | ix_sectors_branch_active | branch_id WHERE deleted_at IS NULL | BTREE | Branch sector listing |
| sectors | uq_sectors_branch_name | branch_id, name | UNIQUE | Prevent duplicate names |
| sectors | uq_sectors_branch_prefix | branch_id, prefix | UNIQUE | Prevent duplicate prefixes |
| tables | ix_tables_sector_status | sector_id, status WHERE deleted_at IS NULL | BTREE | Grid filtering by sector+status |
| tables | uq_tables_sector_number | sector_id, number WHERE deleted_at IS NULL | UNIQUE (partial) | Prevent duplicate numbers in sector |
| table_sessions | ix_table_sessions_table_date | table_id, closed_at | BTREE | Session history for a table |
| waiter_sector_assignments | ix_assignments_date_shift | date, shift WHERE deleted_at IS NULL | BTREE | Daily assignment lookup |
| waiter_sector_assignments | ix_assignments_waiter_date | waiter_id, date WHERE deleted_at IS NULL | BTREE | Waiter schedule lookup |

---

## 2. Table State Machine

### 2.1 State Diagram

```
                    +----------+
                    | INACTIVA | <------------------------+
                    |  (gray)  |                           |
                    +----+-----+                           |
                         |                                 |
                         | admin re-enables                | admin disables
                         v                                 |
                    +----------+                           |
              +-----|  LIBRE   |---------------------------+
              |     | (green)  |
              |     +----+-----+
              |          | ^
              |          | | guests leave (cancel)
              |          | | OR payment processed (archive)
              |          v |
              |     +----------+
              |     | OCUPADA  |
              |     |  (red)   |
              |     +----+-----+
              |          |
              |          | guests place order
              |          v
              |     +-------------------+
              |     | PEDIDO_SOLICITADO | <----------+
              |     |    (yellow)       |            |
              |     +--------+----------+            |
              |              |                       |
              |              | kitchen fulfills      | guests order more
              |              v                       |
              |     +-------------------+            |
              |     | PEDIDO_CUMPLIDO   |------------+
              |     |    (blue)         |
              |     +--------+----------+
              |              |
              |              | guests request check
              |              v
              |     +----------+
              |     |  CUENTA  |
              |     | (purple) |
              |     +----+-----+
              |          |
              |          | payment -> archive session -> reset
              +----------+
```

### 2.2 Transition Matrix

| From \ To | libre | ocupada | pedido_solicitado | pedido_cumplido | cuenta | inactiva |
|-----------|-------|---------|-------------------|-----------------|--------|----------|
| libre | - | Y | - | - | - | Y |
| ocupada | Y (cancel) | - | Y | - | - | - |
| pedido_solicitado | - | - | - | Y | - | - |
| pedido_cumplido | - | - | Y (reorder) | - | Y | - |
| cuenta | Y (archive) | - | - | - | - | - |
| inactiva | Y | - | - | - | - | - |

### 2.3 Transition Side Effects

```python
# Service layer logic for each transition
TRANSITION_SIDE_EFFECTS = {
    (TableStatus.LIBRE, TableStatus.OCUPADA): {
        "set_fields": {"occupied_at": "now()"},
        "clear_fields": [],
    },
    (TableStatus.OCUPADA, TableStatus.PEDIDO_SOLICITADO): {
        "set_fields": {"order_requested_at": "now()"},
        "clear_fields": [],
    },
    (TableStatus.PEDIDO_SOLICITADO, TableStatus.PEDIDO_CUMPLIDO): {
        "set_fields": {"order_fulfilled_at": "now()"},
        "clear_fields": [],
    },
    (TableStatus.PEDIDO_CUMPLIDO, TableStatus.PEDIDO_SOLICITADO): {
        "set_fields": {"order_requested_at": "now()"},
        "clear_fields": ["order_fulfilled_at"],
    },
    (TableStatus.PEDIDO_CUMPLIDO, TableStatus.CUENTA): {
        "set_fields": {"check_requested_at": "now()"},
        "clear_fields": [],
    },
    (TableStatus.CUENTA, TableStatus.LIBRE): {
        "action": "archive_session",
        "set_fields": {},
        "clear_fields": ["occupied_at", "order_requested_at", "order_fulfilled_at", "check_requested_at"],
    },
    (TableStatus.OCUPADA, TableStatus.LIBRE): {
        "action": "cancel_session",
        "set_fields": {},
        "clear_fields": ["occupied_at"],
    },
    (TableStatus.LIBRE, TableStatus.INACTIVA): {
        "set_fields": {},
        "clear_fields": [],
    },
    (TableStatus.INACTIVA, TableStatus.LIBRE): {
        "set_fields": {},
        "clear_fields": [],
    },
}
```

### 2.4 Optimistic Locking Implementation

```python
class TableService:
    async def transition_status(
        self, table_id: int, new_status: TableStatus, version: int
    ) -> Table:
        # 1. Load table with FOR UPDATE (row-level lock)
        table = await self.repo.get_for_update(table_id)
        if not table:
            raise NotFoundError("Table not found")

        # 2. Check optimistic lock
        if table.version != version:
            raise ConflictError(
                f"Table was modified. Expected version {version}, current is {table.version}",
                current_version=table.version
            )

        # 3. Validate transition
        allowed = TABLE_TRANSITIONS.get(table.status, [])
        if new_status not in allowed:
            raise ValidationError(
                f"Invalid transition from '{table.status}' to '{new_status}'",
                allowed_transitions=[s.value for s in allowed]
            )

        # 4. Apply side effects
        effects = TRANSITION_SIDE_EFFECTS.get((table.status, new_status))
        now = datetime.now(timezone.utc)

        if effects.get("action") == "archive_session":
            await self._archive_session(table, now)

        for field, value in effects.get("set_fields", {}).items():
            setattr(table, field, now if value == "now()" else value)

        for field in effects.get("clear_fields", []):
            setattr(table, field, None)

        # 5. Update status and version
        table.status = new_status
        table.status_changed_at = now
        table.version += 1

        await self.repo.update(table)
        return table

    async def _archive_session(self, table: Table, now: datetime):
        session = TableSession(
            tenant_id=table.tenant_id,
            table_id=table.id,
            opened_at=table.occupied_at,
            closed_at=now,
            order_requested_at=table.order_requested_at,
            order_fulfilled_at=table.order_fulfilled_at,
            check_requested_at=table.check_requested_at,
            duration_minutes=int((now - table.occupied_at).total_seconds() / 60),
            status="closed",
        )
        await self.session_repo.create(session)
        table.session_count += 1
```

---

## 3. RBAC Rules Per Endpoint

### 3.1 New Permissions to Add

Update the existing RBAC strategies from Sprint 2:

```python
# Add to ManagerStrategy.PERMISSIONS:
"sectors:read", "sectors:write", "sectors:manage",
"tables:read", "tables:write", "tables:manage",
"staff:read", "staff:write", "staff:manage",
"assignments:read", "assignments:write",

# Add to WaiterStrategy.PERMISSIONS:
"sectors:read",
"tables:read", "tables:write",
"assignments:read",

# Add to ReadOnlyStrategy.PERMISSIONS:
"sectors:read",
"tables:read",
"staff:read",
"assignments:read",

# KitchenStrategy — no new permissions (kitchen doesn't manage tables/staff)
```

### 3.2 Endpoint -> Permission Mapping

| Endpoint | Method | Permission | Additional Rules |
|----------|--------|-----------|------------------|
| `/sectors` | GET | `sectors:read` | -- |
| `/sectors` | POST | `sectors:write` | -- |
| `/sectors/{id}` | PUT | `sectors:write` | -- |
| `/sectors/{id}` | DELETE | `sectors:manage` | 409 if active tables |
| `/tables` | GET | `tables:read` | -- |
| `/tables` | POST | `tables:write` | -- |
| `/tables/batch` | POST | `tables:manage` | -- |
| `/tables/{id}` | PUT | `tables:write` | Only when libre/inactiva |
| `/tables/{id}` | DELETE | `tables:manage` | Only when libre/inactiva |
| `/tables/{id}/status` | PATCH | `tables:write` | State machine validation |
| `/staff` | GET | `staff:read` | -- |
| `/staff` | POST | `staff:write` | Role assignment rules |
| `/staff/{id}` | PUT | `staff:write` | Role assignment rules |
| `/staff/{id}` | DELETE | `staff:manage` | 409 if active assignments |
| `/roles/permissions` | GET | `staff:read` | Read-only |
| `/assignments` | GET | `assignments:read` | -- |
| `/assignments/bulk` | POST | `assignments:write` | Validates waiter role |
| `/assignments/{id}` | DELETE | `assignments:write` | -- |

---

## 4. Component Tree (Frontend)

### 4.1 New Routes

```typescript
// router/routes.ts — ADD:
export const ROUTES = {
  // ... existing routes from Sprint 3
  SECTORS: '/sectores',
  TABLES: '/mesas',
  STAFF: '/personal',
  ROLES: '/roles',
  ASSIGNMENTS: '/asignaciones',
} as const;
```

### 4.2 Sidebar Updates

```
<SidebarGroup label="Salon">
  +-- <SidebarItem to="/sectores" icon="LayoutGrid" label="Sectores" />
  +-- <SidebarItem to="/mesas" icon="Square" label="Mesas" />
  +-- <SidebarItem to="/asignaciones" icon="UserCheck" label="Asignaciones" />

<SidebarGroup label="Personal">
  +-- <SidebarItem to="/personal" icon="Users" label="Personal" />
  +-- <SidebarItem to="/roles" icon="Shield" label="Roles" />
```

### 4.3 New Component Tree

```
dashboard/src/
+-- pages/
|   +-- SectorsPage.tsx
|   +-- TablesPage.tsx
|   +-- StaffPage.tsx
|   +-- RolesPage.tsx
|   +-- AssignmentsPage.tsx
|
+-- components/
|   +-- tables/
|   |   +-- TableGrid.tsx
|   |   +-- TableCard.tsx
|   |   +-- TableStatusModal.tsx
|   |   +-- TableCreateForm.tsx
|   |   +-- TableBatchForm.tsx
|   |   +-- TableFilters.tsx
|   |   +-- StatusLegend.tsx
|   |
|   +-- staff/
|   |   +-- StaffForm.tsx
|   |   +-- StaffSearch.tsx
|   |
|   +-- assignments/
|   |   +-- AssignmentMatrix.tsx
|   |   +-- ShiftSelector.tsx
|   |   +-- DatePicker.tsx
|   |
|   +-- roles/
|   |   +-- PermissionsMatrix.tsx
|   |
|   +-- forms/
|       +-- SectorForm.tsx
|
+-- services/
|   +-- sector.service.ts
|   +-- table.service.ts
|   +-- staff.service.ts
|   +-- role.service.ts
|   +-- assignment.service.ts
|
+-- stores/
|   +-- sector.store.ts
|   +-- table.store.ts
|   +-- staff.store.ts
|   +-- assignment.store.ts
|
+-- types/
|   +-- sector.ts
|   +-- table.ts
|   +-- staff.ts
|   +-- role.ts
|   +-- assignment.ts
|
+-- hooks/
    +-- useTableGrid.ts
    +-- useStaffSearch.ts
    +-- useAssignmentMatrix.ts
```

---

## 5. Zustand Store Design

### 5.1 Table Store

```typescript
interface TableState {
  tables: Table[];
  isLoading: boolean;
  sectorFilter: number | null;
  statusFilter: TableStatus | null;
  pollingIntervalMs: number;
  fetchTables: (branchId: number) => Promise<void>;
  setSectorFilter: (sectorId: number | null) => void;
  setStatusFilter: (status: TableStatus | null) => void;
  transitionStatus: (tableId: number, newStatus: TableStatus, version: number) => Promise<void>;
  getSortedTables: () => Table[];
}
// IMPORTANT: Individual selectors only (React 19 rule)
```

### 5.2 Sector Store

```typescript
interface SectorState {
  sectors: Sector[];
  isLoading: boolean;
  fetchSectors: (branchId: number) => Promise<void>;
  createSector: (data: SectorCreate) => Promise<Sector>;
  updateSector: (id: number, data: SectorUpdate) => Promise<Sector>;
  deleteSector: (id: number) => Promise<void>;
}
```

### 5.3 Staff Store

```typescript
interface StaffState {
  staff: Staff[];
  total: number;
  page: number;
  limit: number;
  searchQuery: string;
  roleFilter: string | null;
  isLoading: boolean;
  fetchStaff: () => Promise<void>;
  setSearchQuery: (q: string) => void;
  setRoleFilter: (role: string | null) => void;
  setPage: (page: number) => void;
  createStaff: (data: StaffCreate) => Promise<Staff>;
  updateStaff: (id: number, data: StaffUpdate) => Promise<Staff>;
  deleteStaff: (id: number) => Promise<void>;
}
```

### 5.4 Assignment Store

```typescript
interface AssignmentState {
  assignments: AssignmentsByShift;
  selectedDate: string;
  selectedShift: ShiftType;
  isLoading: boolean;
  isSaving: boolean;
  fetchAssignments: (branchId: number, date: string) => Promise<void>;
  setDate: (date: string) => void;
  setShift: (shift: ShiftType) => void;
  saveBulk: (branchId: number, assignments: AssignmentBulkItem[]) => Promise<void>;
  deleteAssignment: (id: number) => Promise<void>;
}
```

---

## 6. Sector Prefix Generation Algorithm

```python
def generate_sector_prefix(sector_type: SectorType, branch_id: int, db: AsyncSession) -> str:
    base_prefix = SECTOR_PREFIX_MAP[sector_type]
    existing = await db.execute(
        select(Sector.prefix)
        .where(Sector.branch_id == branch_id, Sector.deleted_at.is_(None))
        .where(Sector.prefix.like(f"{base_prefix}%"))
    )
    used_prefixes = {row[0] for row in existing.all()}
    if base_prefix not in used_prefixes:
        return base_prefix
    suffix = 2
    while f"{base_prefix}{suffix}" in used_prefixes:
        suffix += 1
    return f"{base_prefix}{suffix}"
```

---

## 7. Batch Table Creation Algorithm

```python
async def batch_create_tables(
    self, sector_id: int, quantity: int, capacity_base: int, start_number: int | None = None
) -> list[Table]:
    sector = await self.sector_repo.get_by_id(sector_id)
    if not sector:
        raise NotFoundError("Sector not found")
    if start_number is None:
        max_number = await self.table_repo.get_max_number(sector_id)
        start_number = (max_number or 0) + 1
    numbers_to_create = list(range(start_number, start_number + quantity))
    existing_numbers = await self.table_repo.get_existing_numbers(sector_id, numbers_to_create)
    if existing_numbers:
        raise ConflictError("Number collision detected", conflicting_numbers=existing_numbers)
    if quantity > 50:
        raise ValidationError("Maximum batch size is 50 tables")
    tables = []
    for num in numbers_to_create:
        code = f"{sector.prefix}-{num:02d}"
        table = Table(
            tenant_id=get_current_tenant_id(),
            sector_id=sector_id,
            number=num,
            code=code,
            capacity=capacity_base,
            status=TableStatus.LIBRE,
            version=1,
        )
        tables.append(table)
    await self.table_repo.bulk_create(tables)
    return tables
```

---

## 8. Staff Role Assignment Validation

```python
class StaffService:
    def _validate_role_assignment(self, assigner_role: Role, target_role: Role):
        if assigner_role == Role.ADMIN:
            return
        if assigner_role == Role.MANAGER:
            if target_role == Role.ADMIN:
                raise ForbiddenError("Insufficient permissions to assign ADMIN role")
            if target_role not in (Role.MANAGER, Role.KITCHEN, Role.WAITER, Role.READONLY):
                raise ForbiddenError(f"Cannot assign role: {target_role}")
            return
        raise ForbiddenError("Only ADMIN and MANAGER can create staff")
```

---

## 9. Urgency Sorting Algorithm (Frontend)

```typescript
const URGENCY_SCORES: Record<TableStatus, number> = {
  cuenta: 50,
  pedido_solicitado: 40,
  pedido_cumplido: 30,
  ocupada: 20,
  libre: 10,
  inactiva: 0,
};

function sortByUrgency(tables: Table[]): Table[] {
  return [...tables].sort((a, b) => {
    const scoreA = URGENCY_SCORES[a.status] ?? 0;
    const scoreB = URGENCY_SCORES[b.status] ?? 0;
    if (scoreB !== scoreA) return scoreB - scoreA;
    const timeA = a.status_changed_at ? new Date(a.status_changed_at).getTime() : 0;
    const timeB = b.status_changed_at ? new Date(b.status_changed_at).getTime() : 0;
    return timeA - timeB;
  });
}
```

---

## 10. TableCard Color Mapping (Frontend)

```typescript
const STATUS_STYLES: Record<TableStatus, { bg: string; border: string; text: string; label: string }> = {
  libre:              { bg: 'bg-green-500/10',  border: 'border-l-green-500',  text: 'text-green-500',  label: 'Libre' },
  ocupada:            { bg: 'bg-red-500/10',    border: 'border-l-red-500',    text: 'text-red-500',    label: 'Ocupada' },
  pedido_solicitado:  { bg: 'bg-yellow-500/10', border: 'border-l-yellow-500', text: 'text-yellow-500', label: 'Pedido Solicitado' },
  pedido_cumplido:    { bg: 'bg-blue-500/10',   border: 'border-l-blue-500',   text: 'text-blue-500',   label: 'Pedido Cumplido' },
  cuenta:             { bg: 'bg-purple-500/10', border: 'border-l-purple-500', text: 'text-purple-500', label: 'Cuenta' },
  inactiva:           { bg: 'bg-gray-500/10',   border: 'border-l-gray-500',   text: 'text-gray-500',   label: 'Inactiva' },
};
```

---

## 11. Polling Strategy for Table Grid

```typescript
const POLL_INTERVAL_MS = 15_000; // 15 seconds
// Note: In Sprint 6+, polling will be replaced by WebSocket events from ws_gateway.
```

---

## 12. Key Design Decisions

### D1: Optimistic Locking over Pessimistic
Table status changes can come from multiple waiters simultaneously. Optimistic locking (version column) is preferred because no long-held locks in a web context, conflicts are rare, and clear error messages guide the user to refresh.

### D2: Polling over WebSocket for Sprint 5
WebSocket infrastructure (ws_gateway) is not yet implemented. Sprint 5 uses 15s polling as a temporary solution. The store interface is designed to be swapped to WebSocket event handlers in Sprint 6+ without changing components.

### D3: Delete-and-Reinsert for Bulk Assignments
Instead of diffing existing vs. new assignments, the bulk endpoint deletes all assignments for a date+shift and recreates them. This is simpler, atomic, and avoids complex diff logic.

### D4: Sector Prefix Unique per Branch (not per Type)
This prevents confusing codes like two "INT-05" tables from different interior sectors.

### D5: CSS Grid with Order Property for Urgency Sort
Instead of re-rendering the entire grid on sort changes, we use CSS `order` property mapped to urgency score for smooth transitions.

### D6: Staff CRUD Reuses User Model
No separate "staff" table. Staff members ARE users with roles. The `/staff` endpoint is a filtered view of the `users` table.

### D7: Table Code Regeneration on Sector Change
If a table moves to a different sector (only allowed when libre/inactiva), its code is regenerated with the new sector's prefix.

---

## Next Recommended
`sdd-tasks` — Hierarchical task breakdown with acceptance criteria, file paths, and dependencies.
