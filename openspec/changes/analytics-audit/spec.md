---
sprint: 14
artifact: spec
status: complete
---

# Spec: Estadsticas, Reportes y Auditora

## Requirements (RFC 2119)

### Sales Statistics
- The Dashboard MUST display a statistics page with branch and date range filters
- Date range options MUST include: 7, 14, 30, and 90 days, plus custom range
- The page MUST display 5 summary cards:
  1. **Total Ventas**: sum of all check totals in the period, formatted as ARS currency
  2. **Total Pedidos**: count of orders (not rounds, orders/sessions)
  3. **Total Sesiones**: count of closed sessions
  4. **Ticket Promedio**: total sales / total sessions
  5. **Hora Pico**: hour of day with most orders (e.g., "20:00 - 21:00")
- The page MUST display a bar chart showing daily sales totals for the selected range
- The page MUST display a "Top 10 Productos" table: rank, product name, quantity sold, revenue, percentage of total revenue
- The page MUST display a daily breakdown table: date, orders count, sessions count, total sales, average ticket
- All data views MUST be exportable as CSV

### Reports
- The Dashboard MUST provide a reports page with date range and branch filters
- Reports MUST include trend percentages compared to the previous equivalent period (e.g., 30d vs previous 30d)
- Reports MUST include a "Top 5 Productos" section with revenue and quantity
- The system MUST generate 3 CSV files:
  1. **Resumen**: period, branch, total sales, total orders, total sessions, avg ticket, peak hour
  2. **Diario**: date, orders, sessions, sales, avg ticket (one row per day)
  3. **Productos**: product name, category, quantity sold, revenue, avg price, percentage of total
- CSV exports MUST use streaming response to handle large datasets
- CSV MUST use UTF-8 BOM for Excel compatibility

### Orders Admin View
- The Dashboard MUST provide an orders monitoring page
- The page MUST display 4 summary cards: Pendientes, En Preparacin, Listos, Entregados (counts)
- The page MUST support 2 view modes: Kanban (columns by status) and Grid (table view)
- Kanban columns: PENDING → IN_PROGRESS → READY → DELIVERED
- Each order card MUST show: table code, round number, items summary, elapsed time, waiter name
- The view MUST update in real-time via WebSocket (ORDER_CREATED, ORDER_STATUS_CHANGED events)
- Updates MUST be throttled to 1/second for the order list to prevent UI thrashing

### Audit Trail
- The system MUST log all create/update/delete operations on auditable entities
- Auditable entities MUST include: products, categories, branches, users, promotions, recipes, ingredients
- Each audit entry MUST store: entity_type, entity_id, action (CREATE/UPDATE/DELETE), actor_id, actor_email, timestamp, before_snapshot (JSONB), after_snapshot (JSONB)
- The Dashboard MUST provide an audit query page with filters: entity type, action, user, date range
- Each audit entry MUST be expandable to show before/after diff
- For soft-deleted entities, the audit page MUST provide a "Restaurar" (restore) button
- Restore MUST re-activate the entity and create a new RESTORE audit entry

### RBAC
- Statistics and Reports: ADMIN, SUPERADMIN
- Orders Admin: ADMIN, SUPERADMIN
- Audit Trail: SUPERADMIN only (or ADMIN with explicit audit permission)

## Data Models

### SalesStatistics (computed, not stored)
```python
class SalesSummary:
    total_sales: Decimal
    total_orders: int
    total_sessions: int
    average_ticket: Decimal
    peak_hour: str                      # "20:00 - 21:00"
    period_start: date
    period_end: date
    branch_id: UUID | None              # null = all branches

class DailySales:
    date: date
    orders_count: int
    sessions_count: int
    total_sales: Decimal
    average_ticket: Decimal

class TopProduct:
    rank: int
    product_id: UUID
    product_name: str
    category_name: str
    quantity_sold: int
    revenue: Decimal
    percentage_of_total: Decimal        # 0-100
```

### AuditLogEntry
```python
class AuditLogEntry(BaseModel):
    id: UUID
    entity_type: str                    # "product", "category", "branch", etc.
    entity_id: UUID
    action: AuditAction                 # CREATE | UPDATE | DELETE | RESTORE
    actor_id: UUID                      # FK to users
    actor_email: str                    # denormalized for display
    before_snapshot: dict | None        # JSONB — null on CREATE
    after_snapshot: dict | None         # JSONB — null on DELETE
    metadata: dict | None              # extra context (e.g., reason for delete)
    created_at: datetime

class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    RESTORE = "RESTORE"
```

## API Contracts

### GET /api/statistics/sales
**Auth**: Bearer JWT (role: ADMIN, SUPERADMIN)
**Query**: `?branchId={uuid}&days=30` or `?branchId={uuid}&startDate=2026-01-01&endDate=2026-03-19`
**Response 200**:
```json
{
  "summary": {
    "totalSales": 2450000.00,
    "totalOrders": 890,
    "totalSessions": 654,
    "averageTicket": 3746.18,
    "peakHour": "20:00 - 21:00"
  },
  "dailySales": [
    { "date": "2026-03-19", "ordersCount": 32, "sessionsCount": 25, "totalSales": 89000.00, "averageTicket": 3560.00 }
  ],
  "topProducts": [
    { "rank": 1, "productName": "Milanesa Napolitana", "categoryName": "Platos Principales", "quantitySold": 234, "revenue": 1053000.00, "percentageOfTotal": 43.0 }
  ]
}
```

### GET /api/statistics/sales/export
**Auth**: Bearer JWT (role: ADMIN, SUPERADMIN)
**Query**: Same as /statistics/sales + `type=summary|daily|products`
**Response 200**: `Content-Type: text/csv; charset=utf-8` with BOM
**Headers**: `Content-Disposition: attachment; filename="ventas-resumen-2026-03-19.csv"`

### GET /api/reports/trends
**Auth**: Bearer JWT (role: ADMIN, SUPERADMIN)
**Query**: `?branchId={uuid}&days=30`
**Response 200**:
```json
{
  "currentPeriod": { "totalSales": 2450000.00, "totalOrders": 890 },
  "previousPeriod": { "totalSales": 2100000.00, "totalOrders": 780 },
  "trends": {
    "salesChange": 16.67,
    "ordersChange": 14.10
  },
  "topProducts": [
    { "rank": 1, "productName": "Milanesa Napolitana", "revenue": 1053000.00, "quantitySold": 234 }
  ]
}
```

### GET /api/orders/admin
**Auth**: Bearer JWT (role: ADMIN, SUPERADMIN)
**Query**: `?branchId={uuid}&status=PENDING,IN_PROGRESS`
**Response 200**:
```json
{
  "summary": {
    "pending": 12,
    "inProgress": 8,
    "ready": 3,
    "delivered": 145
  },
  "orders": [
    {
      "id": "uuid",
      "tableCode": "A-05",
      "roundNumber": 2,
      "status": "IN_PROGRESS",
      "items": [{ "name": "Milanesa", "quantity": 2, "status": "PREPARING" }],
      "elapsedMinutes": 15,
      "waiterName": "Carlos",
      "createdAt": "ISO8601"
    }
  ]
}
```

### GET /api/audit
**Auth**: Bearer JWT (role: SUPERADMIN)
**Query**: `?entityType=product&action=DELETE&actorId={uuid}&startDate=2026-03-01&endDate=2026-03-19&page=1&pageSize=20`
**Response 200**:
```json
{
  "entries": [
    {
      "id": "uuid",
      "entityType": "product",
      "entityId": "uuid",
      "action": "DELETE",
      "actorEmail": "admin@buensabor.com",
      "beforeSnapshot": { "name": "Hamburguesa Clsica", "price": 5200.00, "state": "ACTIVE" },
      "afterSnapshot": null,
      "createdAt": "ISO8601"
    }
  ],
  "total": 45,
  "page": 1,
  "pageSize": 20
}
```

### POST /api/audit/{entryId}/restore
**Auth**: Bearer JWT (role: SUPERADMIN)
**Response 200**: `{ "restored": true, "entityType": "product", "entityId": "uuid" }`
**Response 409**: Entity not in deleted state

## Scenarios

### Scenario: Manager reviews weekly sales
```
Given the admin opens the Statistics page
And selects branch "Sucursal Centro" and "ltimos 7 das"
When the data loads
Then 5 summary cards display: $890,000 sales, 312 orders, 245 sessions, $3,632 avg ticket, "20:00-21:00" peak
And a bar chart shows daily sales for 7 days
And Top 10 products table lists Milanesa Napolitana at #1 with 43% of revenue
And a daily breakdown table shows each day's metrics
```

### Scenario: Export daily sales CSV
```
Given the admin is viewing 30-day statistics for "Sucursal Centro"
When the admin clicks "Exportar CSV" and selects "Diario"
Then a streaming CSV download starts
And the file is named "ventas-diario-2026-03-19.csv"
And the file contains UTF-8 BOM for Excel compatibility
And each row has: fecha, pedidos, sesiones, ventas, ticket_promedio
And the file contains 30 rows (one per day)
```

### Scenario: Real-time order monitoring in Kanban
```
Given the admin is viewing the Orders page in Kanban mode
And there are 12 pending, 8 in-progress, 3 ready orders
When a new ORDER_CREATED WebSocket event arrives
Then the Pending column adds a new card at the top
And the Pending count updates to 13
When an ORDER_STATUS_CHANGED event moves order X to IN_PROGRESS
Then the card moves from Pending to In Progress with animation
And counts update: Pending=11, In Progress=9
```

### Scenario: Audit trail with restore
```
Given the superadmin opens the Audit page
And filters by entityType="product", action="DELETE", last 7 days
When results load, showing 3 deleted products
Then each entry shows: product name, who deleted it, when
When the superadmin expands entry for "Hamburguesa Clsica"
Then the before_snapshot shows all product fields at time of deletion
When the superadmin clicks "Restaurar"
Then POST /api/audit/{id}/restore is called
And the product is reactivated with original data
And a new RESTORE audit entry is created
And a success toast shows "Hamburguesa Clsica restaurada"
```

### Scenario: Trend comparison
```
Given the admin opens Reports for "ltimos 30 das"
When data loads comparing March to February
Then trends show: "+16.67% ventas", "+14.10% pedidos"
And positive trends are shown in green with up arrows
And negative trends (if any) are shown in red with down arrows
```
