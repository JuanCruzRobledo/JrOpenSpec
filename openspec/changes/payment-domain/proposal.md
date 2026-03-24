---
sprint: 11
artifact: proposal
status: complete
---

# Proposal: Pagos y Cierre de Mesa

## Intent

Implement the complete payment lifecycle: manual payments registered by waiters, Mercado Pago online payments by diners, and the table close/release flow that completes the dining session cycle.

## Scope

### In Scope
- Manual payment backend: record cash/card/transfer payments against a check
- SELECT FOR UPDATE locking to prevent overpayment race conditions
- FIFO allocation of payments to check items
- Manual payment UI in pwaWaiter
- Mercado Pago integration: preference creation, webhook handling, payment verification
- Circuit breaker for Mercado Pago API (5 failures → open → 503, 30s → semi-open → 2 probes)
- Exponential backoff retries for webhook processing (10s base → max 1h, 5 attempts)
- Rate limiting: manual payments 20/min, MP preference creation 5/min
- Simulated mode for development (no real MP calls)
- Mercado Pago payment flow in pwaMenu (redirect + return handling)
- Table close: verify zero balance, close session, release table
- Table close UI in pwaWaiter with summary and confirmation
- Outbox events: PAYMENT_APPROVED, PAYMENT_REJECTED, CHECK_PAID

### Out of Scope
- Fiscal invoice generation
- Refund processing
- Multi-currency support
- Partial check cancellation
- Payment receipts via email/SMS

## Modules

| Module | Description |
|--------|-------------|
| `payments-manual-backend` | Manual payment recording with locking |
| `payments-manual-pwawaiter` | Waiter UI for registering payments |
| `payments-mp-backend` | Mercado Pago integration, webhooks, circuit breaker |
| `payments-mp-pwamenu` | Diner payment flow with redirect |
| `table-close-backend` | Session close, table release |
| `table-close-pwawaiter` | Close flow UI |

## Approach

1. **Manual payment backend** with pessimistic locking (SELECT FOR UPDATE) and FIFO allocation
2. **Manual payment UI** in pwaWaiter: select type, enter amount, confirm
3. **Mercado Pago backend**: preference creation, webhook receiver with signature verification
4. **Circuit breaker** wrapping all MP API calls
5. **Retry mechanism** for webhook processing failures
6. **MP payment flow** in pwaMenu: initiate → redirect → return page
7. **Dev simulation mode** for MP (flag-based, returns mock responses)
8. **Table close backend**: balance verification, session close, table state reset
9. **Table close UI**: summary, confirmation dialog, success feedback
10. **Outbox events** for all payment state changes

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Race condition on concurrent payments | Critical — overpayment | SELECT FOR UPDATE on check row; serializable within transaction |
| Mercado Pago API downtime | High — diners can't pay online | Circuit breaker prevents cascading; fallback to manual payment |
| Webhook delivery failure/delay | High — payment not recorded | Exponential backoff retries; manual reconciliation endpoint |
| MP redirect URL manipulation | Medium — CSRF/payment hijack | Verify payment via server-side API call, not redirect params |
| Rate limiting false positives on busy nights | Medium — blocked legitimate payments | Separate limits per check, not per user; generous thresholds |

## Rollback

- Payment tables are new — drop tables and remove endpoints
- Mercado Pago integration is behind feature flag — disable flag
- Manual payments are independent of MP — can ship separately
- Table close logic adds a new endpoint but doesn't modify existing close behavior
- Outbox events are append-only; consumers ignore unknown types
