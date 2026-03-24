---
sprint: 14
artifact: tasks
status: complete
---

# Tasks: Estadsticas, Reportes y Auditora

## Phase 1: Database & Materialized Views

### 1.1 Materialized views migration
- Create Alembic migration for: `mv_daily_sales`, `mv_product_sales`, `mv_peak_hours`
- Include unique indexes for CONCURRENTLY refresh
- Create `audit_log` table with all indexes
- **Files**: `alembic/versions/xxx_add_analytics_views.py`, `alembic/versions/xxx_add_audit_log.py`
- **AC**: Migration runs clean; materialized views queryable; concurrent refresh works

### 1.2 Materialized view refresh task
- Implement background task that refreshes all 3 materialized views every 5 minutes
- Use `REFRESH MATERIALIZED VIEW CONCURRENTLY` (non-blocking)
- Log refresh duration for monitoring
- **Files**: `app/tasks/refresh_materialized_views.py`
- **AC**: Views refresh every 5 min; concurrent refresh doesn't block reads; duration logged

## Phase 2: Statistics Backend

### 2.1 Statistics service
- Implement `get_sales_summary()`: query mv_daily_sales for date range + branch, aggregate into SalesSummary
- Implement `get_daily_sales()`: query mv_daily_sales, return list ordered by date
- Implement `get_top_products()`: query mv_product_sales, aggregate by product, rank by revenue, top 10
- Implement `get_peak_hour()`: query mv_peak_hours for date range + branch, return top hour
- **Files**: `app/services/statistics_service.py`, `app/schemas/statistics.py`
- **AC**: All queries return correct aggregations; empty date ranges return zero values; branch filter works

### 2.2 Statistics endpoints
- GET /api/statistics/sales — returns summary + daily + topProducts
- GET /api/statistics/sales/export — streaming CSV with type param (summary|daily|products)
- CSV uses UTF-8 BOM, streaming response, Content-Disposition header
- RBAC: ADMIN, SUPERADMIN
- **Files**: `app/routers/statistics.py`
- **AC**: JSON endpoint returns all 3 data sections; CSV downloads correctly; Excel opens without encoding issues

## Phase 3: Reports Backend

### 3.1 Reports service with trend comparison
- Implement `get_trends()`: query current period + previous equivalent period, calculate percentage changes
- Implement `get_top_products_report()`: top 5 with revenue + quantity
- Reuse statistics service queries with different date ranges
- **Files**: `app/services/reports_service.py`, `app/schemas/reports.py`
- **AC**: Trend percentages correct (positive/negative); top 5 matches stats; previous period correctly calculated

### 3.2 Reports endpoint
- GET /api/reports/trends — returns current/previous periods + trend percentages + top 5
- RBAC: ADMIN, SUPERADMIN
- **Files**: `app/routers/reports.py`
- **AC**: Trend data correct; top 5 products included; RBAC enforced

## Phase 4: Orders Admin Backend

### 4.1 Orders admin service
- Implement `get_orders_summary()`: count orders by status for branch
- Implement `get_orders_list()`: query orders with joins (table, waiter, items), filter by status, paginate
- Include elapsed_minutes calculation (now - created_at)
- **Files**: `app/services/orders_admin_service.py`, `app/schemas/orders_admin.py`
- **AC**: Summary counts accurate; order list includes all needed fields; elapsed time calculated correctly

### 4.2 Orders admin endpoint
- GET /api/orders/admin — returns summary + order list
- Query params: branchId, status (comma-separated), page, pageSize
- RBAC: ADMIN, SUPERADMIN
- **Files**: `app/routers/orders_admin.py`
- **AC**: Endpoint returns summary + paginated orders; status filter works; RBAC enforced

## Phase 5: Audit System

### 5.1 Audit logger (SQLAlchemy event listener)
- Implement `AuditLogger` class that registers SQLAlchemy `after_insert`, `after_update`, `after_delete` events
- Serialize entity state to JSONB (before/after snapshots)
- Register on auditable models: Product, Category, Branch, User, Promotion, Recipe, Ingredient
- Skip audit during bulk operations (configurable flag)
- **Files**: `app/services/audit_logger.py`, `app/models/audit_log.py`
- **AC**: CREATE/UPDATE/DELETE operations generate audit entries; snapshots accurate; no impact on bulk operations

### 5.2 Audit service
- Implement `query_audit_log()`: filter by entity_type, action, actor_id, date range; paginate; lazy-load snapshots
- Implement `get_audit_detail()`: full entry with snapshots
- Implement `restore_entity()`: reactivate soft-deleted entity from before_snapshot, create RESTORE audit entry
- **Files**: `app/services/audit_service.py`, `app/schemas/audit.py`
- **AC**: Query filters work; pagination correct; restore re-activates entity; RESTORE entry created

### 5.3 Audit endpoints
- GET /api/audit — query with filters + pagination
- GET /api/audit/{id} — full detail with snapshots
- POST /api/audit/{id}/restore — restore soft-deleted entity
- RBAC: SUPERADMIN (or ADMIN with audit permission)
- **Files**: `app/routers/audit.py`
- **AC**: All endpoints work; RBAC enforced; restore returns 409 if not deleted

## Phase 6: Dashboard Frontend — Statistics

### 6.1 Statistics page
- Build `StatisticsPage.tsx` with filter bar and data sections
- Build `StatsFilters.tsx`: branch dropdown + date range pills (7/14/30/90/custom)
- Build `SummaryCards.tsx`: 5 KPI cards with icons and formatted values (currency, numbers)
- Build `DailySalesChart.tsx`: Chart.js bar chart with daily totals, responsive
- Build `TopProductsTable.tsx`: ranked table with percentage bars
- Build `DailyBreakdownTable.tsx`: sortable table with all daily metrics
- Build `ExportButton.tsx`: dropdown with 3 CSV options, triggers download
- **Files**: `dashboard/src/statistics/pages/StatisticsPage.tsx`, `dashboard/src/statistics/components/*.tsx`, `dashboard/src/statistics/store/statisticsStore.ts`, `dashboard/src/statistics/services/statisticsService.ts`
- **AC**: Filters update all views; chart renders correctly; tables sortable; CSV downloads work

## Phase 7: Dashboard Frontend — Reports & Orders

### 7.1 Reports page
- Build `ReportsPage.tsx` with filters and trend display
- Build `TrendCard.tsx`: metric value + percentage change + up/down arrow (green/red)
- Build `TopProductsCard.tsx`: top 5 with revenue bars
- Build `ExportPanel.tsx`: 3 CSV export buttons
- **Files**: `dashboard/src/reports/pages/ReportsPage.tsx`, `dashboard/src/reports/components/*.tsx`, `dashboard/src/reports/services/reportsService.ts`
- **AC**: Trends show correct direction/color; top 5 matches data; CSV exports work

### 7.2 Orders admin page
- Build `OrdersAdminPage.tsx` with summary cards and view toggle
- Build `OrderSummaryCards.tsx`: 4 status count cards with color coding
- Build `OrderKanban.tsx` + `OrderKanbanColumn.tsx` + `OrderCard.tsx`: Kanban board with drag-less columns
- Build `OrderGrid.tsx`: table view with all order fields
- Build `ViewToggle.tsx`: Kanban/Grid switch
- Implement `useOrdersWebSocket.ts`: subscribe to ORDER_CREATED + ORDER_STATUS_CHANGED, throttle UI updates to 1/sec
- **Files**: `dashboard/src/orders-admin/pages/OrdersAdminPage.tsx`, `dashboard/src/orders-admin/components/*.tsx`, `dashboard/src/orders-admin/store/ordersAdminStore.ts`, `dashboard/src/orders-admin/hooks/useOrdersWebSocket.ts`
- **AC**: Kanban shows orders in correct columns; real-time updates appear within 1s; grid view shows all data; throttling prevents UI thrashing

## Phase 8: Dashboard Frontend — Audit

### 8.1 Audit page
- Build `AuditPage.tsx` with filters and paginated list
- Build `AuditFilters.tsx`: entity type dropdown, action dropdown, user search, date range
- Build `AuditList.tsx`: paginated entry list with expandable rows
- Build `AuditEntry.tsx`: summary row (entity, action, actor, timestamp) + expandable detail
- Build `SnapshotDiff.tsx`: side-by-side or inline diff of before/after JSONB (highlight changes)
- Build `RestoreButton.tsx`: visible only on DELETE entries, confirm dialog, calls restore API
- **Files**: `dashboard/src/audit/pages/AuditPage.tsx`, `dashboard/src/audit/components/*.tsx`, `dashboard/src/audit/store/auditStore.ts`, `dashboard/src/audit/services/auditService.ts`
- **AC**: Filters narrow results; pagination works; expand loads snapshots lazily; diff highlights changes; restore works with confirmation
