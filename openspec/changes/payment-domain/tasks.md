---
sprint: 11
artifact: tasks
status: complete
---

# Tasks: Pagos y Cierre de Mesa

## Phase 1: Payment Infrastructure

### 1.1 Payment models & migration
- Create `Payment` and `PaymentAllocation` SQLAlchemy models
- Create `WebhookRetry` model for retry queue
- Create Alembic migration for `payments`, `payment_allocations`, `webhook_retries` tables with all indexes
- **Files**: `app/models/payment.py`, `app/models/webhook_retry.py`, `alembic/versions/xxx_add_payments.py`
- **AC**: Migration runs clean; all constraints and indexes created; FK relationships valid

### 1.2 Payment schemas
- Create Pydantic schemas: `ManualPaymentRequest`, `PaymentResponse`, `PaymentListResponse`, `MercadoPagoPreferenceResponse`
- Include validation: amount > 0, paymentType in enum, decimal precision
- **Files**: `app/schemas/payment.py`, `app/schemas/webhook.py`
- **AC**: Schema validation rejects invalid amounts and types; serialization handles Decimal correctly

### 1.3 Rate limiter middleware
- Implement sliding window rate limiter using Redis sorted sets
- Support configurable window (seconds) and max requests per key
- Return 429 with `Retry-After` header when exceeded
- **Files**: `app/middleware/rate_limiter.py`
- **AC**: Rate limiting enforced per check_id; Redis sorted set cleaned on each request; 429 returned with correct Retry-After

### 1.4 FIFO payment allocator
- Implement allocation algorithm: order items by round_number + creation order
- For each item: calculate remaining (subtotal - already allocated), allocate min(remaining, payment_remaining)
- Return list of PaymentAllocation records
- **Files**: `app/services/payment_allocator.py`
- **AC**: Allocation distributes payment across items in FIFO order; no over-allocation; remainder correctly handled

## Phase 2: Manual Payments

### 2.1 Manual payment service
- Implement `create_manual_payment()`:
  1. BEGIN transaction
  2. SELECT FOR UPDATE on check row
  3. Calculate remaining balance (total - sum of APPROVED payments)
  4. Validate amount <= remaining
  5. Create Payment with status APPROVED (manual = instant approval)
  6. Run FIFO allocator
  7. If remaining becomes 0: update check status to PAID
  8. Insert PAYMENT_APPROVED outbox event
  9. If check PAID: insert CHECK_PAID outbox event
  10. COMMIT
- **Files**: `app/services/payment_service.py`
- **AC**: Locking prevents race conditions; overpayment returns 422; balance calculation correct; events emitted

### 2.2 Manual payment endpoint
- POST /api/checks/{checkId}/payments/manual with rate limit 20/min
- RBAC: WAITER only
- Return 201 with payment details + remaining balance
- Return 422 on overpayment with remaining balance
- **Files**: `app/routers/payments.py`
- **AC**: Endpoint works end-to-end; rate limit enforced; RBAC checked; correct status codes

### 2.3 pwaWaiter manual payment UI
- Build `RegisterPaymentButton.tsx`: disabled when check is PAID
- Build `ManualPaymentForm.tsx`: type selector (4 options), amount input with remaining balance display, confirm button
- Build `PaymentHistory.tsx`: list of recorded payments with type icon, amount, timestamp
- Build `PaymentSummary.tsx`: total paid, remaining balance, progress bar
- Create `paymentStore.ts` and `paymentService.ts`
- **Files**: `pwaWaiter/src/payments/components/*.tsx`, `pwaWaiter/src/payments/store/paymentStore.ts`, `pwaWaiter/src/payments/services/paymentService.ts`
- **AC**: Form validates amount; success updates remaining; 422 shows correct remaining; payment history renders

## Phase 3: Mercado Pago Integration

### 3.1 Circuit breaker implementation
- Implement generic `CircuitBreaker` class with states: CLOSED, OPEN, SEMI_OPEN
- Thread-safe with asyncio Lock
- Configurable: failure_threshold, open_duration_seconds, probe_count
- Expose `execute(async_fn)` method that wraps the call
- On OPEN state: raise `CircuitBreakerOpenError` immediately
- **Files**: `app/services/circuit_breaker.py`
- **AC**: State transitions correct (5 failures→OPEN, 30s→SEMI_OPEN, 2 probes→CLOSED); thread-safe; metrics exposed

### 3.2 Mercado Pago client
- Implement `MercadoPagoClient` with methods: `create_preference()`, `get_payment()`, `verify_webhook_signature()`
- Implement `SimulatedMercadoPagoClient` for dev mode: returns mock preference, auto-approves after 5s
- Factory function: returns real or simulated client based on `MERCADOPAGO_SIMULATE` env var
- All real client methods wrapped in circuit breaker
- **Files**: `app/services/mercadopago_client.py`
- **AC**: Real client calls MP API; simulated client returns mocks; circuit breaker wraps all calls; factory selects correctly

### 3.3 Mercado Pago service
- Implement `create_mp_preference()`: create Payment (PENDING), create MP preference with check items, return init_point
- Implement `process_mp_webhook()`: verify signature, fetch payment from MP, update Payment status, run allocator if APPROVED
- Currency: ARS; external_reference: checkId
- **Files**: `app/services/mercadopago_service.py`
- **AC**: Preference created with correct items and back_urls; webhook updates payment correctly; APPROVED triggers allocation

### 3.4 Webhook endpoint & retry worker
- POST /api/webhooks/mercadopago: verify signature, process or schedule retry
- Implement `webhook_retry_worker.py`: background task polling `webhook_retries` table, processes due retries
- Exponential backoff: base 10s, multiplier 2x, max 1h, max 5 attempts
- On max attempts reached: mark FAILED, log alert
- **Files**: `app/routers/webhooks.py`, `app/tasks/webhook_retry_worker.py`, `app/services/webhook_processor.py`
- **AC**: Valid webhook processed immediately; invalid signature returns 400; failed processing scheduled for retry; backoff timing correct

### 3.5 MP payment endpoints
- POST /api/checks/{checkId}/payments/mercadopago with rate limit 5/min
- GET /api/checks/{checkId}/payments (list all payments + summary)
- RBAC: DINER can create MP payment; both roles can list
- 503 when circuit breaker is open
- **Files**: `app/routers/payments.py` (additions)
- **AC**: Preference creation returns init_point; 503 when CB open; payment list includes all types

### 3.6 pwaMenu Mercado Pago UI
- Build `MercadoPagoButton.tsx`: "Pagar con Mercado Pago" button, shows remaining amount
- Build `PaymentReturn.tsx`: handles return from MP redirect, shows success/pending/error based on URL params
- Build `PaymentPending.tsx`: polls GET /api/checks/{id}/payments every 5s for up to 60s while pending
- Create `paymentMenuStore.ts` and `mercadoPagoService.ts`
- **Files**: `pwaMenu/src/payments/components/*.tsx`, `pwaMenu/src/payments/store/paymentMenuStore.ts`, `pwaMenu/src/payments/services/mercadoPagoService.ts`
- **AC**: Button initiates flow; redirect works; return page handles all 3 states; pending polling updates UI

## Phase 4: Table Close

### 4.1 Session close service
- Implement `close_session()`:
  1. Verify check exists and status is PAID (balance = 0)
  2. If unpaid balance: return 422
  3. Update session status to CLOSED, set closed_at
  4. Update table state to LIBRE
  5. Auto-close any remaining ACTIVA/RECONOCIDA service calls
  6. Insert SESSION_CLOSED outbox event
- **Files**: `app/services/session_close_service.py`
- **AC**: Only closes when fully paid; table state transitions correctly; service calls auto-closed; event emitted

### 4.2 Session close endpoint
- POST /api/sessions/{sessionId}/close
- RBAC: WAITER only
- Return 200 with session summary on success
- Return 422 with remaining balance on failure
- **Files**: `app/routers/session_close.py`
- **AC**: Endpoint works; RBAC enforced; correct status codes

### 4.3 pwaWaiter table close UI
- Build `ReleaseTableButton.tsx`: enabled only when check status is PAID
- Build `CloseConfirmation.tsx`: dialog showing session summary (duration, total, paid, rounds)
- Build `CloseSuccess.tsx`: success toast/animation
- On success: close modal, update table card to LIBRE
- Create `closeService.ts`
- **Files**: `pwaWaiter/src/table-close/components/*.tsx`, `pwaWaiter/src/table-close/services/closeService.ts`
- **AC**: Button enabled only when paid; confirmation shows correct summary; close updates table state; modal closes

## Phase 5: Events & Integration

### 5.1 Payment outbox events
- PAYMENT_APPROVED: on manual approval or MP webhook approval
- PAYMENT_REJECTED: on MP webhook rejection
- CHECK_PAID: when check balance reaches zero
- SESSION_CLOSED: on session close
- All within same transaction as state change
- **Files**: `app/events/payment_events.py`
- **AC**: Events emitted atomically; Gateway broadcasts to relevant WebSocket channels

### 5.2 WebSocket event handling
- pwaWaiter: handle PAYMENT_APPROVED/CHECK_PAID to update payment summary in real-time
- pwaMenu: handle PAYMENT_APPROVED to update check view (e.g., MP payment confirmed)
- pwaWaiter: handle SESSION_CLOSED from other waiters (multi-device scenario)
- **Files**: Message routers in both PWAs
- **AC**: Real-time payment updates flow to both apps; table state sync on close

### 5.3 End-to-end validation
- Full flow: order → check → manual payment → MP payment → close table
- Circuit breaker: verify OPEN/SEMI_OPEN/CLOSED transitions
- Race condition: simulate concurrent manual payments
- Offline: manual payment queued and replayed
- **AC**: Complete lifecycle works; no data loss; concurrent safety verified
