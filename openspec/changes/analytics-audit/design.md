---
sprint: 14
artifact: design
status: complete
---

# Design: Estadsticas, Reportes y Auditora

## Architecture Decisions

### AD-1: Materialized Views for Heavy Aggregations
- **Decision**: Use PostgreSQL materialized views for daily sales and product aggregations, refreshed every 5 minutes via pg_cron or background task.
- **Rationale**: Complex joins across checks, check_items, sessions, and products are expensive. Materialized views pre-compute results for fast reads.
- **Tradeoff**: Data is up to 5 minutes stale. Acceptable for statistics (not real-time accuracy required).

### AD-2: Streaming CSV Response
- **Decision**: Generate CSV exports using Python generators + StreamingResponse, not buffered in memory.
- **Rationale**: Large date ranges (90 days) with many products can produce thousands of rows. Streaming prevents memory exhaustion and allows the browser to start downloading immediately.
- **Tradeoff**: Cannot calculate file size upfront for Content-Length header — use chunked transfer encoding instead.

### AD-3: Generic Audit Logger via SQLAlchemy Events
- **Decision**: Implement audit logging via SQLAlchemy `after_insert`, `after_update`, `after_delete` events on auditable models.
- **Rationale**: Decouples audit logic from business logic. Automatically captures snapshots without modifying service layer code.
- **Tradeoff**: SQLAlchemy events can be tricky with bulk operations — mitigated by disabling audit on bulk imports.

### AD-4: JSONB Snapshots with Lazy Loading
- **Decision**: Store before/after snapshots as JSONB in the audit_log table. Load snapshots only when user expands an entry (lazy).
- **Rationale**: Snapshots are large (full entity state). Loading them for every entry in a list query would be expensive.
- **Tradeoff**: Extra API call to load snapshot detail — but the common case (browsing audit log) is fast.

### AD-5: Chart.js for Dashboard Charts
- **Decision**: Use Chart.js (via react-chartjs-2) for bar charts and visualizations.
- **Rationale**: Lightweight (~60KB), well-maintained, good React integration, sufficient for bar/line charts without the weight of D3.
- **Tradeoff**: Limited customization compared to D3 — acceptable for business dashboards.

## DB Schema

### Materialized Views
```sql
-- Daily sales aggregation
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT
    c.branch_id,
    DATE(c.created_at) AS sale_date,
    COUNT(DISTINCT s.id) AS sessions_count,
    COUNT(DISTINCT c.id) AS orders_count,
    SUM(c.total) AS total_sales,
    CASE WHEN COUNT(DISTINCT s.id) > 0
         THEN SUM(c.total) / COUNT(DISTINCT s.id)
         ELSE 0 END AS average_ticket
FROM checks c
JOIN sessions s ON c.session_id = s.id
WHERE c.status = 'PAID'
GROUP BY c.branch_id, DATE(c.created_at);

CREATE UNIQUE INDEX idx_mv_daily_sales ON mv_daily_sales(branch_id, sale_date);

-- Product sales aggregation
CREATE MATERIALIZED VIEW mv_product_sales AS
SELECT
    ci.product_id,
    ci.product_name,
    p.category_id,
    cat.name AS category_name,
    c.branch_id,
    DATE(c.created_at) AS sale_date,
    SUM(ci.quantity) AS quantity_sold,
    SUM(ci.subtotal) AS revenue
FROM check_items ci
JOIN checks c ON ci.check_id = c.id
JOIN products p ON ci.product_id = p.id
LEFT JOIN categories cat ON p.category_id = cat.id
WHERE c.status = 'PAID'
GROUP BY ci.product_id, ci.product_name, p.category_id, cat.name, c.branch_id, DATE(c.created_at);

CREATE INDEX idx_mv_product_sales ON mv_product_sales(branch_id, sale_date);

-- Refresh command (run every 5 min)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_product_sales;
```

### Peak Hour View
```sql
CREATE MATERIALIZED VIEW mv_peak_hours AS
SELECT
    c.branch_id,
    EXTRACT(HOUR FROM c.created_at) AS hour_of_day,
    COUNT(*) AS order_count
FROM checks c
WHERE c.status = 'PAID'
GROUP BY c.branch_id, EXTRACT(HOUR FROM c.created_at);

CREATE INDEX idx_mv_peak_hours ON mv_peak_hours(branch_id);
```

### audit_log table
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'RESTORE')),
    actor_id UUID NOT NULL REFERENCES users(id),
    actor_email VARCHAR(255) NOT NULL,
    before_snapshot JSONB,
    after_snapshot JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_actor ON audit_log(actor_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);
CREATE INDEX idx_audit_composite ON audit_log(entity_type, action, created_at);
```

## File Structure

### Backend
```
app/
├── models/
│   └── audit_log.py                  # AuditLogEntry model
├── schemas/
│   ├── statistics.py                 # SalesSummary, DailySales, TopProduct
│   ├── reports.py                    # TrendReport, ExportConfig
│   ├── orders_admin.py               # AdminOrderView, OrderSummary
│   └── audit.py                      # AuditLogQuery, AuditLogResponse
├── services/
│   ├── statistics_service.py         # Query materialized views
│   ├── reports_service.py            # Trend comparison + CSV generation
│   ├── orders_admin_service.py       # Order list with filters
│   ├── audit_service.py              # Audit query + restore
│   └── audit_logger.py              # SQLAlchemy event listener
├── routers/
│   ├── statistics.py                 # /statistics/sales, /statistics/sales/export
│   ├── reports.py                    # /reports/trends
│   ├── orders_admin.py               # /orders/admin
│   └── audit.py                      # /audit, /audit/{id}/restore
├── tasks/
│   └── refresh_materialized_views.py # Background task every 5 min
└── migrations/
    └── xxx_add_materialized_views.py # Views + audit_log table
```

### Dashboard Frontend
```
dashboard/src/
├── statistics/
│   ├── pages/
│   │   └── StatisticsPage.tsx
│   ├── components/
│   │   ├── StatsFilters.tsx           # Branch + date range selectors
│   │   ├── SummaryCards.tsx           # 5 KPI cards
│   │   ├── DailySalesChart.tsx        # Bar chart (Chart.js)
│   │   ├── TopProductsTable.tsx       # Top 10 table
│   │   ├── DailyBreakdownTable.tsx    # Daily detail table
│   │   └── ExportButton.tsx           # CSV export trigger
│   ├── store/
│   │   └── statisticsStore.ts
│   └── services/
│       └── statisticsService.ts
├── reports/
│   ├── pages/
│   │   └── ReportsPage.tsx
│   ├── components/
│   │   ├── TrendCard.tsx              # Metric + trend arrow
│   │   ├── TopProductsCard.tsx        # Top 5 products
│   │   └── ExportPanel.tsx            # 3 CSV buttons
│   └── services/
│       └── reportsService.ts
├── orders-admin/
│   ├── pages/
│   │   └── OrdersAdminPage.tsx
│   ├── components/
│   │   ├── OrderSummaryCards.tsx       # 4 status cards
│   │   ├── OrderKanban.tsx            # Kanban board
│   │   ├── OrderKanbanColumn.tsx      # Status column
│   │   ├── OrderCard.tsx              # Individual order card
│   │   ├── OrderGrid.tsx              # Table view
│   │   └── ViewToggle.tsx             # Kanban/Grid switch
│   ├── store/
│   │   └── ordersAdminStore.ts
│   └── hooks/
│       └── useOrdersWebSocket.ts      # Real-time updates
├── audit/
│   ├── pages/
│   │   └── AuditPage.tsx
│   ├── components/
│   │   ├── AuditFilters.tsx           # Entity type, action, user, dates
│   │   ├── AuditList.tsx              # Paginated entry list
│   │   ├── AuditEntry.tsx             # Expandable row
│   │   ├── SnapshotDiff.tsx           # Before/after comparison
│   │   └── RestoreButton.tsx          # Restore soft-deleted
│   ├── store/
│   │   └── auditStore.ts
│   └── services/
│       └── auditService.ts
```

## Component Trees

### Statistics Page
```
<StatisticsPage>
  ├── <StatsFilters branch={} dateRange={} onChange={} />
  ├── <SummaryCards>
  │   ├── <Card title="Total Ventas" value="$2,450,000" icon={DollarSign} />
  │   ├── <Card title="Total Pedidos" value="890" icon={ShoppingCart} />
  │   ├── <Card title="Sesiones" value="654" icon={Users} />
  │   ├── <Card title="Ticket Promedio" value="$3,746" icon={Receipt} />
  │   └── <Card title="Hora Pico" value="20:00-21:00" icon={Clock} />
  ├── <DailySalesChart data={dailySales} />
  ├── <TopProductsTable products={topProducts} />
  ├── <DailyBreakdownTable data={dailySales} />
  └── <ExportButton onExport={type => downloadCSV(type)} />
```

### Orders Admin — Kanban
```
<OrdersAdminPage>
  ├── <OrderSummaryCards pending={12} inProgress={8} ready={3} delivered={145} />
  ├── <ViewToggle mode={kanban|grid} />
  └── [kanban mode]
      <OrderKanban>
        ├── <OrderKanbanColumn title="Pendientes" status="PENDING">
        │   └── <OrderCard> (per order, sorted by elapsed time desc)
        ├── <OrderKanbanColumn title="En Preparacin" status="IN_PROGRESS">
        ├── <OrderKanbanColumn title="Listos" status="READY">
        └── <OrderKanbanColumn title="Entregados" status="DELIVERED">
```

## Sequence Diagrams

### Statistics Query Flow
```
Admin           Dashboard         API              StatsService     MV (PostgreSQL)
  |                |                |                  |               |
  |--select filters>|               |                  |               |
  |                |--GET /statistics/sales?days=30---->|               |
  |                |                |                  |--query mv_daily_sales
  |                |                |                  |--query mv_product_sales
  |                |                |                  |--query mv_peak_hours
  |                |                |                  |<--results------|
  |                |                |                  |--aggregate---->|
  |                |<--200 {summary, daily, top10}------|               |
  |                |--render charts + tables            |               |
  |<--see dashboard|                |                  |               |
```

### CSV Export Flow
```
Admin           Dashboard         API              ReportsService
  |                |                |                  |
  |--click export->|                |                  |
  |                |--GET /statistics/sales/export?type=daily-->|
  |                |                |                  |--create generator
  |                |                |<--StreamingResponse (chunked)--|
  |                |<--download starts immediately      |
  |                |  (browser shows download progress) |
  |<--file saved---|                |                  |
```

### Audit Logger Flow
```
Admin           API              Service          SQLAlchemy       AuditLogger      DB
  |                |                |                |                |               |
  |--DELETE product>|               |                |                |               |
  |                |--delete()----->|                |                |               |
  |                |                |--soft delete-->|                |               |
  |                |                |                |--after_update->|               |
  |                |                |                |                |--serialize before
  |                |                |                |                |--serialize after
  |                |                |                |                |--INSERT audit_log
  |                |                |                |                |-------------->|
  |                |<--200----------|                |                |               |
```
