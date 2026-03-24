---
sprint: 14
artifact: proposal
status: complete
---

# Proposal: Estadsticas, Reportes y Auditora

## Intent

Provide actionable business intelligence through sales statistics, exportable reports, real-time order monitoring, and a comprehensive audit trail — empowering restaurant owners and managers with data-driven decision-making tools.

## Scope

### In Scope
- Sales statistics dashboard: filterable by branch and date range (7/14/30/90 days)
- 5 summary cards: total sales, total orders, total sessions, average ticket, peak hour
- Daily sales bar chart
- Top 10 products by revenue
- Daily breakdown table
- CSV export for all data views
- Reports: date range + branch filters, trend percentages, top 5 products, 3 CSV exports (summary, daily, products)
- Admin orders view: 4 summary cards, Kanban + grid views, real-time WebSocket updates
- Audit trail: query by entity/action/user/dates, before/after snapshots, soft-delete restoration
- All endpoints with RBAC (ADMIN, SUPERADMIN)

### Out of Scope
- Real-time streaming analytics
- Predictive analytics / ML
- Custom dashboard builder
- PDF report generation
- Email scheduled reports
- Financial/accounting reports

## Modules

| Module | Description |
|--------|-------------|
| `statistics` | Sales statistics queries + aggregations |
| `reports` | Report generation + CSV export |
| `orders-admin` | Admin order monitoring view |
| `audit` | Audit trail queries + restoration |
| `dashboard-ui` | All Dashboard frontend pages |

## Approach

1. **Statistics backend** — optimized SQL queries with date range + branch filters, materialized views for heavy aggregations
2. **Statistics UI** — summary cards, Chart.js bar chart, top products table, daily breakdown
3. **Reports backend** — reusable query layer shared with statistics, CSV generation
4. **Reports UI** — filter controls, trend indicators, export buttons
5. **Orders admin backend** — real-time order list with WebSocket subscription
6. **Orders admin UI** — Kanban board + grid toggle, summary cards
7. **Audit backend** — generic audit query with JSONB snapshot support
8. **Audit UI** — searchable log with expandable before/after diff view

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Heavy aggregation queries slowing production DB | High — degraded app performance | Materialized views refreshed every 5 min; separate read replica if needed |
| Large CSV exports timing out | Medium — failed downloads | Streaming CSV response; limit to 10k rows per export; suggest date range reduction |
| Audit snapshots consuming excessive storage | Medium — DB bloat | JSONB compression; retention policy (archive after 90 days); lazy snapshot loading |
| Real-time order view overwhelming Dashboard | Low — browser performance | Virtual scrolling; throttle WebSocket updates to 1/sec for order list |

## Rollback

- All new tables are additive (statistics views, audit_log)
- Dashboard pages are new routes — removal just removes navigation links
- CSV export is a new endpoint — removal is safe
- Audit logging can be disabled via flag without data loss
