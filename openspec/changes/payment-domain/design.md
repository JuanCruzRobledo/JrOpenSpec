---
sprint: 11
artifact: design
status: complete
---

# Design: Pagos y Cierre de Mesa

## Architecture Decisions

### AD-1: SELECT FOR UPDATE Pessimistic Locking
- **Decision**: Use PostgreSQL `SELECT FOR UPDATE` on the check row before any payment processing.
- **Rationale**: Prevents overpayment race conditions when two waiters or a waiter + MP webhook attempt to record payments simultaneously. The lock is held within a single transaction, keeping the critical section short.
- **Tradeoff**: Slight latency increase (~5-10ms) due to row-level locking. Acceptable for payment operations.

### AD-2: FIFO Payment Allocation
- **Decision**: Allocate payments to check items in order: first by round_number (ascending), then by item creation order.
- **Rationale**: Provides a deterministic, auditable allocation trail. Important for partial payment scenarios and potential future refund logic.
- **Tradeoff**: More complex than a simple "check total" approach, but enables per-item payment tracking.

### AD-3: Circuit Breaker Pattern for MP
- **Decision**: Implement a circuit breaker wrapping all Mercado Pago API calls with 5-failure threshold, 30s cooldown, 2-probe semi-open.
- **Rationale**: Prevents cascading failures when MP is down. Returns fast 503 instead of timeout. Auto-recovers when MP comes back.
- **Tradeoff**: State management complexity — implemented as an in-memory singleton with thread-safe locks.

### AD-4: Webhook Retry with Exponential Backoff
- **Decision**: Failed webhook processing retries with: 10s, 20s, 40s, 80s, 160s (capped at 1h), max 5 attempts.
- **Rationale**: MP webhooks can fail due to transient errors. Exponential backoff prevents thundering herd while ensuring eventual consistency.
- **Tradeoff**: Payment confirmation may be delayed up to ~5 minutes in worst case. Acceptable for a restaurant context.

### AD-5: Simulation Mode for Development
- **Decision**: `MERCADOPAGO_SIMULATE=true` env var activates a mock MP client that returns fake preferences and auto-approves after 5s.
- **Rationale**: Developers need to test the full payment flow without real MP credentials or sandbox environment.
- **Tradeoff**: Simulation may not catch MP-specific edge cases — mitigated by also having MP sandbox testing in staging.

## DB Schema

### payments table
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_id UUID NOT NULL REFERENCES checks(id),
    payment_type VARCHAR(30) NOT NULL CHECK (payment_type IN (
        'EFECTIVO', 'TARJETA_DEBITO', 'TARJETA_CREDITO', 'TRANSFERENCIA', 'MERCADOPAGO'
    )),
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED'
    )),
    mp_preference_id VARCHAR(255),
    mp_payment_id VARCHAR(255),
    mp_status VARCHAR(50),
    registered_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payments_check ON payments(check_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_mp_preference ON payments(mp_preference_id) WHERE mp_preference_id IS NOT NULL;
CREATE INDEX idx_payments_mp_payment ON payments(mp_payment_id) WHERE mp_payment_id IS NOT NULL;
```

### payment_allocations table
```sql
CREATE TABLE payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    check_item_id UUID NOT NULL REFERENCES check_items(id),
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payment_alloc_payment ON payment_allocations(payment_id);
CREATE INDEX idx_payment_alloc_item ON payment_allocations(check_item_id);
```

### webhook_retries table
```sql
CREATE TABLE webhook_retries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_type VARCHAR(50) NOT NULL,        -- 'mercadopago'
    payload JSONB NOT NULL,
    attempt_count INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    next_retry_at TIMESTAMPTZ NOT NULL,
    last_error TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_webhook_retries_pending ON webhook_retries(next_retry_at) WHERE status = 'PENDING';
```

## File Structure

### Backend additions
```
app/
├── models/
│   ├── payment.py                    # Payment + PaymentAllocation models
│   └── webhook_retry.py             # WebhookRetry model
├── schemas/
│   ├── payment.py                    # Request/response schemas
│   └── webhook.py                    # Webhook payload schemas
├── services/
│   ├── payment_service.py           # Manual payment logic + locking
│   ├── mercadopago_service.py       # MP preference + payment verification
│   ├── mercadopago_client.py        # MP API client (real + simulated)
│   ├── circuit_breaker.py           # Generic circuit breaker implementation
│   ├── payment_allocator.py         # FIFO allocation engine
│   ├── webhook_processor.py         # Webhook handling + retry scheduling
│   └── session_close_service.py     # Table close logic
├── routers/
│   ├── payments.py                   # Manual + MP payment endpoints
│   ├── webhooks.py                   # MP webhook receiver
│   └── session_close.py             # Close endpoint
├── events/
│   └── payment_events.py            # PAYMENT_APPROVED, PAYMENT_REJECTED, CHECK_PAID
├── middleware/
│   └── rate_limiter.py              # Per-check rate limiting
└── tasks/
    └── webhook_retry_worker.py      # Background worker for retry processing
```

### pwaWaiter additions
```
pwaWaiter/src/
├── payments/
│   ├── components/
│   │   ├── RegisterPaymentButton.tsx # Opens payment form
│   │   ├── ManualPaymentForm.tsx    # Type selector + amount input
│   │   ├── PaymentHistory.tsx       # List of payments on check
│   │   └── PaymentSummary.tsx       # Total paid + remaining
│   ├── store/
│   │   └── paymentStore.ts
│   └── services/
│       └── paymentService.ts
├── table-close/
│   ├── components/
│   │   ├── ReleaseTableButton.tsx   # "Liberar Mesa" button
│   │   ├── CloseConfirmation.tsx    # Summary + confirm dialog
│   │   └── CloseSuccess.tsx         # Success feedback
│   └── services/
│       └── closeService.ts
```

### pwaMenu additions
```
pwaMenu/src/
├── payments/
│   ├── components/
│   │   ├── MercadoPagoButton.tsx    # "Pagar con MP" button
│   │   ├── PaymentReturn.tsx        # Return page (success/pending/error)
│   │   └── PaymentPending.tsx       # Polling pending state
│   ├── store/
│   │   └── paymentMenuStore.ts
│   └── services/
│       └── mercadoPagoService.ts
```

## Component Trees

### pwaWaiter — Payments in Table Detail
```
<TableDetailModal>
  ├── ...existing sections...
  ├── <PaymentSummary totalPaid={} remaining={} checkStatus={} />
  ├── <PaymentHistory payments={[]} />
  ├── <RegisterPaymentButton onClick={openForm} disabled={checkPaid} />
  │   └── <ManualPaymentForm> (modal)
  │       ├── <PaymentTypeSelector />
  │       ├── <AmountInput remaining={} />
  │       └── <ConfirmButton />
  └── <ReleaseTableButton disabled={!checkPaid} />
      └── <CloseConfirmation> (modal)
          ├── <SessionSummary duration={} total={} paid={} rounds={} />
          └── <ConfirmRelease />
```

### pwaMenu — Mercado Pago
```
<CheckView>
  ├── ...itemized check...
  ├── <MercadoPagoButton checkId={} remaining={} />
  └── [after redirect return]
      └── <PaymentReturn status={success|pending|error}>
          ├── [success] "Pago aprobado - $15,400"
          ├── [pending] <PaymentPending checkId={} /> (polls every 5s)
          └── [error] "Pago rechazado" + retry button
```

## Sequence Diagrams

### Manual Payment Flow
```
Waiter          pwaWaiter         API              DB               Outbox
  |                |                |                |                 |
  |--select type-->|                |                |                 |
  |--enter amount->|                |                |                 |
  |--confirm------>|                |                |                 |
  |                |--POST /payments/manual--------->|                 |
  |                |                |--BEGIN TX----->|                 |
  |                |                |--SELECT FOR UPDATE check------->|
  |                |                |--verify amount <= remaining      |
  |                |                |--INSERT payment|                 |
  |                |                |--allocate FIFO |                 |
  |                |                |--check balance?|                 |
  |                |                |  [if 0: status→PAID]            |
  |                |                |--INSERT outbox event----------->|
  |                |                |--COMMIT------->|                 |
  |                |<--201 {payment, remaining}------|                 |
  |<--toast success|                |                |                 |
```

### Mercado Pago Flow
```
Diner           pwaMenu           API              MP API          Webhook
  |                |                |                |                |
  |--tap "Pagar"-->|                |                |                |
  |                |--POST /payments/mercadopago---->|                |
  |                |                |--[circuit breaker check]        |
  |                |                |--create preference------------>|
  |                |                |<--preference + init_point------|
  |                |<--{initPoint}--|                |                |
  |                |--redirect to MP|                |                |
  |--pay on MP---->|                |                |                |
  |                |                |                |--webhook------>|
  |                |                |                |                |--verify signature
  |                |                |                |                |--fetch payment detail
  |                |                |--record payment + allocate      |
  |                |                |--emit PAYMENT_APPROVED          |
  |<--redirect back|                |                |                |
  |                |--[return page]->|               |                |
  |                |  shows "Pago aprobado"          |                |
```

### Circuit Breaker State Machine
```
         success
    ┌──────────────┐
    │              │
    ▼              │
┌────────┐  5 failures  ┌────────┐  30s cooldown  ┌───────────┐
│ CLOSED │ ───────────> │  OPEN  │ ──────────────> │ SEMI_OPEN │
└────────┘              └────────┘                 └───────────┘
    ▲                                                   │    │
    │                    2 probes succeed                │    │
    └───────────────────────────────────────────────────┘    │
                                                              │
                         any probe fails                      │
                    ┌────────────────────────────────────────┘
                    ▼
               ┌────────┐
               │  OPEN  │ (reset cooldown timer)
               └────────┘
```

### Table Close Flow
```
Waiter          pwaWaiter         API              DB
  |                |                |                |
  |--tap "Liberar">|                |                |
  |                |--show summary dialog            |
  |--confirm------>|                |                |
  |                |--POST /sessions/{id}/close----->|
  |                |                |--check balance |
  |                |                |  [balance=0]   |
  |                |                |--session→CLOSED|
  |                |                |--table→LIBRE   |
  |                |                |--close service calls
  |                |                |--emit SESSION_CLOSED
  |                |<--200 {summary}|                |
  |<--toast "Mesa liberada"         |                |
  |                |--close modal   |                |
  |                |--update table card→LIBRE        |
```

## Rate Limiting Design

```
Rate limiter uses sliding window algorithm per check_id:

Manual payments: window=60s, max=20
  Key: "rate:payment:manual:{checkId}"
  Storage: Redis sorted set (timestamp scores)

MP preferences: window=60s, max=5
  Key: "rate:payment:mp:{checkId}"
  Storage: Redis sorted set (timestamp scores)

On each request:
  1. Remove entries older than window
  2. Count remaining entries
  3. If count >= max: return 429 with Retry-After header
  4. Else: add current timestamp, proceed
```

## FIFO Allocation Algorithm

```
function allocate(payment_amount, check_items_ordered_by_round):
    remaining = payment_amount
    allocations = []

    for item in check_items_ordered_by_round:
        already_allocated = sum(existing allocations for item)
        item_remaining = item.subtotal - already_allocated

        if item_remaining <= 0:
            continue

        alloc_amount = min(remaining, item_remaining)
        allocations.append({ item_id: item.id, amount: alloc_amount })
        remaining -= alloc_amount

        if remaining <= 0:
            break

    return allocations
```
