---
sprint: 5
artifact: spec
status: complete
---

# SDD Spec — Sprint 5: Mesas, Sectores y Personal

## Status: APPROVED

---

## 1. Requirements (RFC 2119)

### 1.1 Sector Management

- **SEC-001**: The system MUST support CRUD operations for sectors scoped to a branch.
- **SEC-002**: Each sector MUST have: `name` (string, max 100), `type` (enum: interior, terraza, barra, VIP), `capacity` (positive integer), `is_active` (boolean, default true).
- **SEC-003**: Sector names MUST be unique within a branch (case-insensitive).
- **SEC-004**: A sector MUST NOT be hard-deleted if it has active tables (is_active=true). The system MUST return 409 Conflict.
- **SEC-005**: Soft-deleting a sector SHOULD cascade soft-delete to all its tables.
- **SEC-006**: Each sector MUST auto-generate a `prefix` from its type: `INT` (interior), `TER` (terraza), `BAR` (barra), `VIP` (VIP). If multiple sectors share a type within a branch, append a numeric suffix: `INT`, `INT2`, `INT3`.
- **SEC-007**: The system MUST expose a `GET /sectors` endpoint returning all active sectors for the current branch, ordered by type then name.
- **SEC-008**: Only users with `sectors:read` permission MAY list sectors. Only `sectors:write` MAY create/update. Only `sectors:manage` MAY delete.

### 1.2 Table Management

- **TBL-001**: The system MUST support individual table creation with: `number` (positive integer), `capacity` (positive integer, 1-20), `sector_id` (FK), `status` (enum, default: `libre`).
- **TBL-002**: Each table MUST have an auto-generated `code` following the pattern `{sector_prefix}-{number_zero_padded}`. Example: sector with prefix `TER`, table number 5 → `TER-05`. Zero-pad to 2 digits (01-99).
- **TBL-003**: Table numbers MUST be unique within a sector. The UNIQUE constraint is on `(sector_id, number)`.
- **TBL-004**: The system MUST support batch table creation: input `quantity` (1-50), `sector_id`, `capacity_base` (applied to all), `start_number` (auto-calculated as max existing + 1 if not provided). The system MUST validate no number collisions before inserting.
- **TBL-005**: Batch creation MUST be atomic — if any table fails validation, the entire batch MUST be rolled back.
- **TBL-006**: Table status MUST be one of 6 values: `libre`, `ocupada`, `pedido_solicitado`, `pedido_cumplido`, `cuenta`, `inactiva`.
- **TBL-007**: The system MUST enforce the following state machine transitions:

```
libre → ocupada           (waiter seats guests)
libre → inactiva          (admin disables table)
ocupada → pedido_solicitado   (guests place order)
pedido_solicitado → pedido_cumplido  (kitchen fulfills order)
pedido_cumplido → cuenta       (guests request check)
pedido_cumplido → pedido_solicitado  (guests order more items)
cuenta → libre             (payment processed, table archived)
inactiva → libre           (admin re-enables table)
ocupada → libre            (guests leave without ordering — cancellation)
```

Any transition not in this list MUST be rejected with 422 Unprocessable Entity.

- **TBL-008**: On each status transition, the system MUST record a timestamp in the `status_changed_at` field.
- **TBL-009**: When transitioning to `pedido_solicitado`, the system MUST set `order_requested_at` timestamp.
- **TBL-010**: When transitioning to `pedido_cumplido`, the system MUST set `order_fulfilled_at` timestamp.
- **TBL-011**: When transitioning to `cuenta`, the system MUST set `check_requested_at` timestamp.
- **TBL-012**: When transitioning from `cuenta` to `libre` (archival), the system MUST:
  1. Create a `TableSession` record capturing: table_id, opened_at (when status became `ocupada`), closed_at (now), order_requested_at, order_fulfilled_at, check_requested_at, total duration.
  2. Reset the table: status=`libre`, clear all temporal timestamps, increment `session_count`.
- **TBL-013**: The system MUST expose `GET /tables` returning tables for the current branch with optional filters: `sector_id`, `status`, sorted by urgency score descending.
- **TBL-014**: Urgency score MUST be calculated as: `cuenta=50`, `pedido_solicitado=40`, `pedido_cumplido=30`, `ocupada=20`, `libre=10`, `inactiva=0`. Secondary sort by `status_changed_at` ascending (oldest first within same urgency).
- **TBL-015**: Only users with `tables:read` permission MAY list tables. Only `tables:write` MAY create/update/transition status. Only `tables:manage` MAY delete or batch create.
- **TBL-016**: The system MUST support optimistic locking via a `version` column. On status transition, the client sends the current version; if it doesn't match, return 409 Conflict.

### 1.3 Staff Management

- **STF-001**: The system MUST provide a paginated staff list endpoint (`GET /staff`) returning: id, full_name, email, role, dni, hired_at, is_active. Default page_size=20.
- **STF-002**: The staff list MUST support real-time search by `full_name` or `email` via a `q` query parameter. Search MUST be case-insensitive and use ILIKE pattern matching.
- **STF-003**: The system MUST support creating staff members with: `full_name` (required, max 255), `email` (required, valid format, unique per tenant), `password` (required, min 8 chars), `role` (required, valid Role enum), `dni` (optional, max 20), `hired_at` (optional, defaults to today).
- **STF-004**: Role assignment rules MUST be enforced:
  - ADMIN users MAY assign any role.
  - MANAGER users MAY assign: MANAGER, KITCHEN, WAITER, READONLY.
  - MANAGER users MUST NOT assign ADMIN role. Attempt returns 403 Forbidden with message "Insufficient permissions to assign ADMIN role".
  - No other roles MAY create staff members.
- **STF-005**: Email MUST be unique per tenant (existing constraint from Sprint 2: UNIQUE(tenant_id, email)).
- **STF-006**: Staff update MUST allow modifying: full_name, role (with same assignment rules), dni, hired_at, is_active. Email and password changes require separate endpoints (out of scope for Sprint 5, use Sprint 2 auth endpoints).
- **STF-007**: Staff soft-delete MUST check that the user is not assigned to any active sector assignments for today. If so, return 409 Conflict.
- **STF-008**: Only users with `staff:read` permission MAY list staff. Only `staff:write` MAY create/update. Only `staff:manage` MAY deactivate.

### 1.4 Roles Matrix

- **ROL-001**: The system MUST expose a `GET /roles/permissions` endpoint returning a matrix of all roles and their permissions.
- **ROL-002**: The response format MUST be: `{ roles: [{ role: string, permissions: string[] }] }`.
- **ROL-003**: This endpoint is read-only and available to any authenticated user with `staff:read` permission.
- **ROL-004**: The frontend MUST render this as a table: rows = permissions, columns = roles, cells = checkmark or empty.

### 1.5 Waiter-Sector Assignment

- **ASN-001**: The system MUST support assigning waiters to sectors for a specific date and shift.
- **ASN-002**: Shift MUST be one of: `morning` (06:00-14:00), `afternoon` (14:00-22:00), `night` (22:00-06:00).
- **ASN-003**: Each assignment record MUST contain: `waiter_id` (FK to users), `sector_id` (FK to sectors), `date` (date, not datetime), `shift` (enum).
- **ASN-004**: The UNIQUE constraint MUST be on `(waiter_id, sector_id, date, shift)` — a waiter can be assigned to multiple sectors in the same shift, but not duplicated.
- **ASN-005**: Only users with role WAITER MAY be assigned. Attempting to assign a non-WAITER user MUST return 422.
- **ASN-006**: Only active sectors MAY be assigned. Attempting to assign to an inactive sector MUST return 422.
- **ASN-007**: The system MUST expose `GET /assignments?date=YYYY-MM-DD` returning all assignments for a given date, grouped by shift.
- **ASN-008**: The system MUST expose `POST /assignments/bulk` accepting an array of `{ waiter_id, sector_id, shift }` for a given date. This replaces ALL assignments for that date+shift combination (delete-and-reinsert pattern).
- **ASN-009**: Only today's assignments are considered "active" for operational purposes (waiter routing, responsibility). Past assignments are historical records.
- **ASN-010**: Only users with `assignments:write` permission MAY create/modify assignments. `assignments:read` to view.

---

## 2. Data Models

### 2.1 Enums (in `shared/enums.py`)

```python
class SectorType(str, Enum):
    INTERIOR = "interior"
    TERRAZA = "terraza"
    BARRA = "barra"
    VIP = "vip"

SECTOR_PREFIX_MAP = {
    SectorType.INTERIOR: "INT",
    SectorType.TERRAZA: "TER",
    SectorType.BARRA: "BAR",
    SectorType.VIP: "VIP",
}

class TableStatus(str, Enum):
    LIBRE = "libre"
    OCUPADA = "ocupada"
    PEDIDO_SOLICITADO = "pedido_solicitado"
    PEDIDO_CUMPLIDO = "pedido_cumplido"
    CUENTA = "cuenta"
    INACTIVA = "inactiva"

# Allowed transitions: from_status -> [to_status, ...]
TABLE_TRANSITIONS = {
    TableStatus.LIBRE: [TableStatus.OCUPADA, TableStatus.INACTIVA],
    TableStatus.OCUPADA: [TableStatus.PEDIDO_SOLICITADO, TableStatus.LIBRE],
    TableStatus.PEDIDO_SOLICITADO: [TableStatus.PEDIDO_CUMPLIDO],
    TableStatus.PEDIDO_CUMPLIDO: [TableStatus.CUENTA, TableStatus.PEDIDO_SOLICITADO],
    TableStatus.CUENTA: [TableStatus.LIBRE],
    TableStatus.INACTIVA: [TableStatus.LIBRE],
}

TABLE_URGENCY_SCORE = {
    TableStatus.CUENTA: 50,
    TableStatus.PEDIDO_SOLICITADO: 40,
    TableStatus.PEDIDO_CUMPLIDO: 30,
    TableStatus.OCUPADA: 20,
    TableStatus.LIBRE: 10,
    TableStatus.INACTIVA: 0,
}

class ShiftType(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"
```

### 2.2 Sector Model (update `shared/models/room/sector.py`)

```python
class Sector(Base, AuditMixin, TenantScopedMixin):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[SectorType] = mapped_column(String(20), nullable=False)
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    tables: Mapped[list["Table"]] = relationship(back_populates="sector", lazy="selectin")
    assignments: Mapped[list["WaiterSectorAssignment"]] = relationship(back_populates="sector")

    __table_args__ = (
        UniqueConstraint("branch_id", "name", name="uq_sectors_branch_name"),
        UniqueConstraint("branch_id", "prefix", name="uq_sectors_branch_prefix"),
        CheckConstraint("capacity > 0", name="ck_sector_capacity_positive"),
    )
```

### 2.3 Table Model (update `shared/models/room/table.py`)

```python
class Table(Base, AuditMixin, TenantScopedMixin):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(15), nullable=False)  # e.g. "TER-05"
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TableStatus] = mapped_column(String(25), nullable=False, default=TableStatus.LIBRE)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Temporal tracking
    status_changed_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    occupied_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    order_requested_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    order_fulfilled_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    check_requested_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)

    # Stats
    session_count: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    sector: Mapped["Sector"] = relationship(back_populates="tables")
    sessions: Mapped[list["TableSession"]] = relationship(back_populates="table")

    __table_args__ = (
        UniqueConstraint("sector_id", "number", name="uq_tables_sector_number"),
        CheckConstraint("capacity >= 1 AND capacity <= 20", name="ck_table_capacity_range"),
        CheckConstraint("number > 0", name="ck_table_number_positive"),
        Index("ix_tables_sector_status", "sector_id", "status"),
    )
```

### 2.4 TableSession Model (update `shared/models/room/table_session.py`)

```python
class TableSession(Base, AuditMixin, TenantScopedMixin):
    __tablename__ = "table_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, nullable=False)
    closed_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, nullable=False)
    order_requested_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    order_fulfilled_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    check_requested_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)  # total session duration
    status: Mapped[str] = mapped_column(String(20), default="closed")

    # Relationships
    table: Mapped["Table"] = relationship(back_populates="sessions")

    __table_args__ = (
        Index("ix_table_sessions_table_date", "table_id", "closed_at"),
    )
```

### 2.5 User Model Extensions (add fields to existing `shared/models/core/user.py`)

Add to existing User model:
```python
    dni: Mapped[str | None] = mapped_column(String(20))
    hired_at: Mapped[date | None] = mapped_column(Date)
```

### 2.6 WaiterSectorAssignment Model (update `shared/models/services/waiter_sector_assignment.py`)

```python
class WaiterSectorAssignment(Base, AuditMixin, TenantScopedMixin):
    __tablename__ = "waiter_sector_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    waiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    shift: Mapped[ShiftType] = mapped_column(String(15), nullable=False)

    # Relationships
    waiter: Mapped["User"] = relationship()
    sector: Mapped["Sector"] = relationship(back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("waiter_id", "sector_id", "date", "shift", name="uq_assignment_waiter_sector_date_shift"),
        Index("ix_assignments_date_shift", "date", "shift"),
        Index("ix_assignments_waiter_date", "waiter_id", "date"),
    )
```

---

## 3. API Contracts

### 3.1 Sector Endpoints

#### `GET /api/branches/{branch_id}/sectors`
- **Auth**: `sectors:read`
- **Query**: `?include_inactive=false` (boolean)
- **Response 200**:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Salon Principal",
      "type": "interior",
      "prefix": "INT",
      "capacity": 60,
      "is_active": true,
      "table_count": 15,
      "available_tables": 8,
      "created_at": "2026-03-19T10:00:00Z"
    }
  ],
  "total": 4
}
```

#### `POST /api/branches/{branch_id}/sectors`
- **Auth**: `sectors:write`
- **Body**:
```json
{
  "name": "Terraza Norte",
  "type": "terraza",
  "capacity": 40
}
```
- **Response 201**: Created sector object (prefix auto-generated)
- **Response 409**: Duplicate name within branch
- **Response 422**: Validation errors

#### `PUT /api/branches/{branch_id}/sectors/{sector_id}`
- **Auth**: `sectors:write`
- **Body**: `{ "name": "...", "type": "...", "capacity": N }`
- **Note**: If `type` changes, prefix is recalculated. All table codes under this sector MUST be regenerated.
- **Response 200**: Updated sector

#### `DELETE /api/branches/{branch_id}/sectors/{sector_id}`
- **Auth**: `sectors:manage`
- **Response 200**: `{ "message": "Sector deactivated", "tables_deactivated": 12 }`
- **Response 409**: Sector has active tables with non-libre status

### 3.2 Table Endpoints

#### `GET /api/branches/{branch_id}/tables`
- **Auth**: `tables:read`
- **Query**: `?sector_id=1&status=libre&sort=urgency` (all optional)
- **Response 200**:
```json
{
  "data": [
    {
      "id": 1,
      "number": 5,
      "code": "TER-05",
      "capacity": 4,
      "status": "pedido_solicitado",
      "version": 3,
      "sector": { "id": 2, "name": "Terraza", "type": "terraza" },
      "status_changed_at": "2026-03-19T12:30:00Z",
      "occupied_at": "2026-03-19T12:00:00Z",
      "order_requested_at": "2026-03-19T12:30:00Z",
      "order_fulfilled_at": null,
      "check_requested_at": null,
      "session_count": 47,
      "urgency_score": 40
    }
  ],
  "total": 45
}
```

#### `POST /api/branches/{branch_id}/tables`
- **Auth**: `tables:write`
- **Body**:
```json
{
  "number": 5,
  "capacity": 4,
  "sector_id": 2
}
```
- **Response 201**: Created table with auto-generated code
- **Response 409**: Duplicate number in sector

#### `POST /api/branches/{branch_id}/tables/batch`
- **Auth**: `tables:manage`
- **Body**:
```json
{
  "sector_id": 2,
  "quantity": 10,
  "capacity_base": 4,
  "start_number": 1
}
```
- **Response 201**:
```json
{
  "created": 10,
  "tables": [
    { "id": 10, "code": "TER-01", "number": 1, "capacity": 4 },
    { "id": 11, "code": "TER-02", "number": 2, "capacity": 4 }
  ]
}
```
- **Response 409**: Number collision detected (lists conflicting numbers)
- **Response 422**: quantity > 50 or start_number invalid

#### `PATCH /api/branches/{branch_id}/tables/{table_id}/status`
- **Auth**: `tables:write`
- **Body**:
```json
{
  "status": "pedido_solicitado",
  "version": 3
}
```
- **Response 200**: Updated table with new version
- **Response 409**: Version mismatch (optimistic lock conflict)
- **Response 422**: Invalid transition

#### `PUT /api/branches/{branch_id}/tables/{table_id}`
- **Auth**: `tables:write`
- **Body**: `{ "capacity": 6, "sector_id": 3 }`
- **Note**: Moving a table to a different sector regenerates the code. Only allowed when status is `libre` or `inactiva`.
- **Response 200**: Updated table

#### `DELETE /api/branches/{branch_id}/tables/{table_id}`
- **Auth**: `tables:manage`
- **Response 200**: `{ "message": "Table deactivated" }`
- **Response 409**: Table is not in `libre` or `inactiva` status

### 3.3 Staff Endpoints

#### `GET /api/staff`
- **Auth**: `staff:read`
- **Query**: `?q=juan&page=1&limit=20&role=WAITER&is_active=true`
- **Response 200**:
```json
{
  "data": [
    {
      "id": 5,
      "full_name": "Juan Perez",
      "email": "juan@restaurant.com",
      "role": "WAITER",
      "dni": "40123456",
      "hired_at": "2025-06-15",
      "is_active": true,
      "created_at": "2025-06-15T10:00:00Z"
    }
  ],
  "total": 23,
  "page": 1,
  "limit": 20,
  "pages": 2
}
```

#### `POST /api/staff`
- **Auth**: `staff:write` + role assignment rules (STF-004)
- **Body**:
```json
{
  "full_name": "Maria Gonzalez",
  "email": "maria@restaurant.com",
  "password": "securepass123",
  "role": "WAITER",
  "dni": "41234567",
  "hired_at": "2026-03-19"
}
```
- **Response 201**: Created staff (password NOT returned)
- **Response 403**: Insufficient permissions for role assignment
- **Response 409**: Email already exists for tenant

#### `PUT /api/staff/{user_id}`
- **Auth**: `staff:write` + role assignment rules
- **Body**: `{ "full_name": "...", "role": "...", "dni": "...", "hired_at": "...", "is_active": true }`
- **Response 200**: Updated staff

#### `DELETE /api/staff/{user_id}`
- **Auth**: `staff:manage`
- **Response 200**: `{ "message": "Staff member deactivated" }`
- **Response 409**: Staff has active assignments for today

### 3.4 Roles Endpoint

#### `GET /api/roles/permissions`
- **Auth**: `staff:read`
- **Response 200**:
```json
{
  "roles": [
    {
      "role": "ADMIN",
      "label": "Administrador",
      "permissions": ["*"]
    },
    {
      "role": "MANAGER",
      "label": "Gerente",
      "permissions": ["users:read", "menu:read", "menu:write", "menu:manage", "orders:read", "orders:write", "orders:manage", "kitchen:read", "kitchen:write", "reports:read", "settings:read", "tables:read", "tables:write", "tables:manage", "sectors:read", "sectors:write", "sectors:manage", "staff:read", "staff:write", "staff:manage", "assignments:read", "assignments:write"]
    },
    {
      "role": "WAITER",
      "label": "Mozo",
      "permissions": ["orders:read", "orders:write", "tables:read", "tables:write", "menu:read", "sectors:read", "assignments:read"]
    },
    {
      "role": "KITCHEN",
      "label": "Cocina",
      "permissions": ["kitchen:read", "kitchen:write", "menu:read", "orders:read"]
    },
    {
      "role": "READONLY",
      "label": "Solo Lectura",
      "permissions": ["menu:read", "orders:read", "tables:read", "sectors:read", "staff:read", "assignments:read", "kitchen:read", "reports:read"]
    }
  ]
}
```

### 3.5 Assignment Endpoints

#### `GET /api/branches/{branch_id}/assignments`
- **Auth**: `assignments:read`
- **Query**: `?date=2026-03-19` (required)
- **Response 200**:
```json
{
  "date": "2026-03-19",
  "shifts": {
    "morning": [
      {
        "id": 1,
        "waiter": { "id": 5, "full_name": "Juan Perez" },
        "sector": { "id": 2, "name": "Terraza" },
        "shift": "morning"
      }
    ],
    "afternoon": [],
    "night": []
  }
}
```

#### `POST /api/branches/{branch_id}/assignments/bulk`
- **Auth**: `assignments:write`
- **Body**:
```json
{
  "date": "2026-03-19",
  "shift": "morning",
  "assignments": [
    { "waiter_id": 5, "sector_id": 2 },
    { "waiter_id": 5, "sector_id": 3 },
    { "waiter_id": 8, "sector_id": 1 }
  ]
}
```
- **Behavior**: DELETE all existing assignments for this date+shift in this branch, then INSERT the new ones. This is a "replace all" operation for the shift.
- **Response 200**:
```json
{
  "date": "2026-03-19",
  "shift": "morning",
  "created": 3,
  "assignments": [...]
}
```
- **Response 422**: waiter_id is not a WAITER role, or sector_id is inactive

#### `DELETE /api/branches/{branch_id}/assignments/{assignment_id}`
- **Auth**: `assignments:write`
- **Response 200**: `{ "message": "Assignment removed" }`

---

## 4. UI Specifications

### 4.1 Table Grid Layout

```
+-------------------------------------------------------------+
| Mesas                                          [+ Nueva] [Lote] |
+-------------------------------------------------------------+
| Filtros: [Sucursal v] [Sector v] [Estado v]   Buscar         |
+-------------------------------------------------------------+
|                                                             |
|  +----------+ +----------+ +----------+ +----------+        |
|  | TER-01   | | TER-03   | | INT-05   | | INT-02   |        |
|  | Cap: 4   | | Cap: 2   | | Cap: 6   | | Cap: 4   |        |
|  | Cuenta   | | Pedido   | | Cumpl.   | | Ocup.    |        |
|  | 15:23    | | 14:45    | | 13:10    | | 12:00    |        |
|  +----------+ +----------+ +----------+ +----------+        |
|  +----------+ +----------+ +----------+                      |
|  | BAR-01   | | VIP-01   | | INT-01   |                      |
|  | Cap: 2   | | Cap: 8   | | Cap: 4   |                      |
|  | Libre    | | Libre    | | Inact.   |                      |
|  |          | |          | |          |                      |
|  +----------+ +----------+ +----------+                      |
|                                                             |
+-------------------------------------------------------------+
| Leyenda: Libre  Ocupada  Pedido Solicitado                  |
|          Pedido Cumplido  Cuenta  Inactiva                   |
+-------------------------------------------------------------+
```

### 4.2 Color System (TailwindCSS 4 classes)

| Status | Background | Border | Text | TW Classes |
|--------|-----------|--------|------|-----------|
| libre | `#22c55e` (green-500) | `#16a34a` (green-600) | white | `bg-green-500 border-green-600` |
| ocupada | `#ef4444` (red-500) | `#dc2626` (red-600) | white | `bg-red-500 border-red-600` |
| pedido_solicitado | `#eab308` (yellow-500) | `#ca8a04` (yellow-600) | black | `bg-yellow-500 border-yellow-600 text-black` |
| pedido_cumplido | `#3b82f6` (blue-500) | `#2563eb` (blue-600) | white | `bg-blue-500 border-blue-600` |
| cuenta | `#a855f7` (purple-500) | `#9333ea` (purple-600) | white | `bg-purple-500 border-purple-600` |
| inactiva | `#6b7280` (gray-500) | `#4b5563` (gray-600) | white | `bg-gray-500 border-gray-600` |

### 4.3 Table Card Component

Each card is 160x120px (responsive), with:
- Top: Table code (bold, 16px) + sector name (muted, 12px)
- Middle: Capacity icon + number
- Bottom: Status label + time elapsed since `status_changed_at` (e.g., "hace 23 min")
- Border: 3px left border in status color
- Background: subtle tint of status color (10% opacity)
- Click: Opens status transition modal
- Hover: Scale 1.02 + shadow elevation

### 4.4 Status Transition Modal

When clicking a table card, a modal shows current status details and only valid transitions as buttons.

### 4.5 Batch Creation Modal

Shows sector selection, quantity, capacity, start number, and a preview of generated codes.

### 4.6 Staff Page Layout

Paginated table with search, role filter, status filter. Columns: name, email, role, DNI, hire date, status, actions.

### 4.7 Assignment Page Layout

Matrix UI where rows = waiters, columns = sectors, cells = shift toggles. Date picker and shift selector at top.

### 4.8 Roles Matrix Page

Read-only table where rows = permissions, columns = roles, cells = checkmark or empty.

### 4.9 Animations

- Table card status change: `transition-colors duration-300 ease-in-out` on background + border
- Table card hover: `transition-transform duration-150 hover:scale-[1.02] hover:shadow-lg`
- Modal open/close: `animate-in fade-in slide-in-from-bottom-4 duration-200`
- Grid reorder (after urgency sort): CSS Grid with `transition: all 300ms ease` on grid items
- Toast notifications: existing pattern from Sprint 3

---

## 5. Scenarios (Given/When/Then)

### Scenario 1: Table Status Transition (Happy Path)
```
GIVEN a table TER-05 with status "ocupada" and version 3
WHEN the waiter submits PATCH /tables/TER-05/status with {"status": "pedido_solicitado", "version": 3}
THEN the system:
  - Validates the transition (ocupada -> pedido_solicitado) is allowed
  - Sets status to "pedido_solicitado"
  - Sets order_requested_at to current timestamp
  - Sets status_changed_at to current timestamp
  - Increments version to 4
  - Returns 200 with updated table
```

### Scenario 2: Optimistic Lock Conflict
```
GIVEN table INT-01 with version 5
WHEN waiter A reads version 5
AND waiter B transitions the table (version becomes 6)
AND waiter A submits a transition with version 5
THEN the system returns 409 Conflict with:
  {"detail": "Table was modified by another user. Please refresh.", "current_version": 6}
```

### Scenario 3: Table Archival (cuenta -> libre)
```
GIVEN table BAR-03 with status "cuenta", occupied_at=12:00, order_requested_at=12:15, order_fulfilled_at=12:45, check_requested_at=13:00
WHEN the cashier transitions to "libre"
THEN the system:
  - Creates a TableSession: opened_at=12:00, closed_at=now(), duration_minutes=65, order_requested_at=12:15, order_fulfilled_at=12:45, check_requested_at=13:00
  - Resets the table: status=libre, version++, clears all temporal fields, increments session_count
  - Returns 200
```

### Scenario 4: Batch Table Creation
```
GIVEN sector "Terraza" (id=2, prefix="TER") with existing tables TER-01 through TER-05
WHEN admin POSTs /tables/batch with {"sector_id": 2, "quantity": 5, "capacity_base": 4}
THEN start_number auto-calculates as 6
AND creates TER-06, TER-07, TER-08, TER-09, TER-10 atomically
AND returns 201 with all 5 tables
```

### Scenario 5: Batch Creation Collision
```
GIVEN sector "Terraza" has tables TER-01 through TER-10
WHEN admin POSTs /tables/batch with {"sector_id": 2, "quantity": 5, "capacity_base": 4, "start_number": 8}
THEN system detects numbers 8, 9, 10 already exist
AND returns 409 with {"detail": "Number collision", "conflicting_numbers": [8, 9, 10]}
```

### Scenario 6: MANAGER Cannot Assign ADMIN Role
```
GIVEN a MANAGER user creates a new staff member
WHEN they submit {"role": "ADMIN", ...}
THEN the system returns 403 with {"detail": "Insufficient permissions to assign ADMIN role"}
```

### Scenario 7: Invalid Table Transition
```
GIVEN table VIP-01 with status "libre"
WHEN someone attempts to transition to "cuenta"
THEN the system returns 422 with {"detail": "Invalid transition from 'libre' to 'cuenta'", "allowed_transitions": ["ocupada", "inactiva"]}
```

### Scenario 8: Bulk Assignment Replace
```
GIVEN morning shift on 2026-03-19 has assignments: Juan->Terraza, Carlos->Barra
WHEN admin POSTs /assignments/bulk with date=2026-03-19, shift=morning, assignments=[Juan->Salon, Ana->Terraza]
THEN the system:
  - Deletes existing morning assignments for this branch+date
  - Creates Juan->Salon and Ana->Terraza
  - Returns 200 with 2 created assignments
```

### Scenario 9: Staff Search Real-time
```
GIVEN 50 staff members in the tenant
WHEN user types "gon" in the search field
THEN after 300ms debounce, GET /staff?q=gon is called
AND returns staff matching "gon" in full_name OR email (case-insensitive)
```

### Scenario 10: Sector Soft Delete Cascade
```
GIVEN sector "Terraza" with 10 tables (8 libre, 2 inactiva)
WHEN admin deletes the sector
THEN all 10 tables are soft-deleted (is_active=false)
AND the sector is soft-deleted
AND returns 200 with tables_deactivated=10
```

---

## Next Recommended
`sdd-design` — DB schema physical design, component tree, state machine diagram, RBAC rules per endpoint.
