---
sprint: 11
artifact: spec
status: complete
---

# Spec: Pagos y Cierre de Mesa

## Requirements (RFC 2119)

### Manual Payment — Backend
- The system MUST support recording manual payments via POST /api/checks/{checkId}/payments/manual
- The endpoint MUST acquire a SELECT FOR UPDATE lock on the check row before processing
- The system MUST verify the payment amount does not exceed the remaining balance (total - sum of approved payments)
- If the payment would cause overpayment, the system MUST return 422 with the remaining balance
- Payments MUST be allocated to check items in FIFO order (by round_number, then item creation order)
- Each payment MUST record: type (EFECTIVO, TARJETA_DEBITO, TARJETA_CREDITO, TRANSFERENCIA), amount, registered_by (waiter)
- The system MUST create an audit log entry for each payment
- Rate limiting MUST cap manual payment creation at 20 per minute per check
- When the check balance reaches zero, the system MUST update check status to PAID and emit CHECK_PAID event

### Manual Payment — pwaWaiter
- The waiter app MUST display a "Registrar Pago" button on the check view within the table detail modal
- The payment form MUST include: payment type selector (4 options), amount input (numeric, 2 decimals), remaining balance display
- The form MUST validate that amount > 0 and amount <= remaining balance before submission
- On success, the form MUST show a confirmation toast and update the remaining balance
- On 422 (overpayment), the form MUST display the server-reported remaining balance

### Mercado Pago — Backend
- POST /api/checks/{checkId}/payments/mercadopago MUST create an MP preference in ARS currency
- The preference MUST include: check items as line items, external_reference = checkId, back_urls for success/pending/failure
- All MP API calls MUST be wrapped in a circuit breaker:
  - Closed → Open: after 5 consecutive failures
  - Open state: return 503 immediately, no API calls
  - Open → Semi-Open: after 30 seconds cooldown
  - Semi-Open: allow 2 probe requests; if both succeed → Closed; if either fails → Open
- Failed webhook processing MUST retry with exponential backoff: base 10s, multiplier 2x, max interval 1h, max 5 attempts
- Rate limiting MUST cap MP preference creation at 5 per minute per check
- Webhook endpoint MUST verify MP signature header before processing
- The system MUST support a `MERCADOPAGO_SIMULATE=true` environment variable for dev mode:
  - Preference creation returns a mock preference with a local redirect URL
  - Simulated webhook delivers APPROVED status after 5 seconds

### Mercado Pago — pwaMenu
- The diner app MUST display a "Pagar con Mercado Pago" button on the check view
- Tapping the button MUST call POST /api/checks/{checkId}/payments/mercadopago to get the preference
- The app MUST redirect the user to the MP checkout URL (init_point)
- On return, the app MUST handle 3 states:
  - Success: show "Pago aprobado" with payment details
  - Pending: show "Pago pendiente" with instructions to wait
  - Failure: show "Pago rechazado" with option to retry
- The app MUST poll payment status if the return page shows pending (every 5s, max 60s)

### Table Close
- POST /api/sessions/{sessionId}/close MUST verify the check balance is zero (all payments cover the total)
- If balance > 0, the system MUST return 422 with remaining balance
- On successful close:
  - Session status MUST be set to CLOSED with closed_at timestamp
  - Table state MUST be set to LIBRE
  - All active service calls for the session MUST be auto-closed
- The system MUST emit SESSION_CLOSED outbox event

### Table Close — pwaWaiter
- The table detail modal MUST show a "Liberar Mesa" button when check status is PAID
- Tapping MUST show a confirmation dialog with session summary: duration, total ordered, total paid, rounds count
- On confirm, the system calls POST /api/sessions/{sessionId}/close
- On success: toast "Mesa {code} liberada", close modal, table card updates to LIBRE state

### Events
- PAYMENT_APPROVED: emitted when any payment (manual or MP) is approved — payload: paymentId, checkId, amount, type
- PAYMENT_REJECTED: emitted when MP payment is rejected — payload: paymentId, checkId, reason
- CHECK_PAID: emitted when check balance reaches zero — payload: checkId, sessionId, totalPaid
- All events MUST be inserted into the outbox table within the same transaction as the state change

## Data Models

### Payment
```python
class Payment(BaseModel):
    id: UUID
    check_id: UUID                       # FK to Check
    payment_type: PaymentType            # EFECTIVO | TARJETA_DEBITO | TARJETA_CREDITO | TRANSFERENCIA | MERCADOPAGO
    amount: Decimal                      # positive, max 2 decimals
    status: PaymentStatus                # PENDING | APPROVED | REJECTED | CANCELLED
    mp_preference_id: str | None         # Mercado Pago preference ID
    mp_payment_id: str | None            # Mercado Pago payment ID
    mp_status: str | None                # Raw MP status string
    registered_by: UUID | None           # Waiter who registered (manual only)
    created_at: datetime
    updated_at: datetime

class PaymentType(str, Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA_DEBITO = "TARJETA_DEBITO"
    TARJETA_CREDITO = "TARJETA_CREDITO"
    TRANSFERENCIA = "TRANSFERENCIA"
    MERCADOPAGO = "MERCADOPAGO"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
```

### PaymentAllocation
```python
class PaymentAllocation(BaseModel):
    id: UUID
    payment_id: UUID                     # FK to Payment
    check_item_id: UUID                  # FK to CheckItem
    amount: Decimal                      # Amount allocated to this item
    created_at: datetime
```

### CircuitBreakerState
```python
class CircuitBreakerState:
    state: Literal['CLOSED', 'OPEN', 'SEMI_OPEN']
    failure_count: int                   # consecutive failures
    last_failure_at: datetime | None
    probe_success_count: int             # for semi-open probing
    config: CircuitBreakerConfig

class CircuitBreakerConfig:
    failure_threshold: int = 5
    open_duration_seconds: int = 30
    probe_count: int = 2
```

## API Contracts

### POST /api/checks/{checkId}/payments/manual
**Auth**: Bearer JWT (role: WAITER)
**Rate Limit**: 20/min per check
**Request**:
```json
{
  "paymentType": "EFECTIVO",
  "amount": 8000.00
}
```
**Response 201**:
```json
{
  "id": "uuid",
  "checkId": "uuid",
  "paymentType": "EFECTIVO",
  "amount": 8000.00,
  "status": "APPROVED",
  "registeredBy": "uuid",
  "remainingBalance": 7400.00,
  "checkStatus": "OPEN",
  "createdAt": "ISO8601"
}
```
**Response 422**: `{ "error": "OVERPAYMENT", "remainingBalance": 7400.00 }`
**Response 429**: Rate limited

### POST /api/checks/{checkId}/payments/mercadopago
**Auth**: Bearer JWT (role: DINER)
**Rate Limit**: 5/min per check
**Request**: (no body needed — check items are used)
**Response 201**:
```json
{
  "paymentId": "uuid",
  "preferenceId": "mp-pref-123",
  "initPoint": "https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=mp-pref-123",
  "sandboxInitPoint": "https://sandbox.mercadopago.com.ar/..."
}
```
**Response 503**: Circuit breaker open — `{ "error": "PAYMENT_PROVIDER_UNAVAILABLE", "retryAfter": 30 }`

### POST /api/webhooks/mercadopago
**Auth**: MP signature verification (X-Signature header)
**Request** (from MP):
```json
{
  "action": "payment.updated",
  "data": { "id": "mp-payment-123" }
}
```
**Response 200**: Acknowledged
**Response 400**: Invalid signature

### GET /api/checks/{checkId}/payments
**Auth**: Bearer JWT
**Response 200**:
```json
{
  "payments": [Payment],
  "totalPaid": 8000.00,
  "remainingBalance": 7400.00,
  "checkStatus": "OPEN"
}
```

### POST /api/sessions/{sessionId}/close
**Auth**: Bearer JWT (role: WAITER)
**Response 200**:
```json
{
  "sessionId": "uuid",
  "tableId": "uuid",
  "tableCode": "A-05",
  "tableState": "LIBRE",
  "sessionDuration": "01:45:32",
  "totalPaid": 15400.00,
  "closedAt": "ISO8601"
}
```
**Response 422**: `{ "error": "UNPAID_BALANCE", "remainingBalance": 7400.00 }`

## Scenarios

### Scenario: Waiter registers cash payment
```
Given check "CHK-001" has total $15,400 and $0 paid
When the waiter selects "Efectivo" and enters amount $8,000
Then POST /api/checks/{id}/payments/manual is called
And the server acquires SELECT FOR UPDATE on the check
And verifies $8,000 <= $15,400 remaining
And creates payment with status APPROVED
And allocates $8,000 to items in FIFO order
And emits PAYMENT_APPROVED event
And returns remaining balance $7,400
And the waiter sees "Pago registrado - Resta: $7,400"
```

### Scenario: Concurrent payment race condition prevented
```
Given check "CHK-001" has $2,000 remaining
When Waiter A submits $2,000 manual payment
And Waiter B simultaneously submits $2,000 manual payment
Then Waiter A's transaction acquires the lock first
And records $2,000 payment, balance becomes $0, check status → PAID
And Waiter B's transaction acquires the lock second
And sees remaining balance = $0
And returns 422 "OVERPAYMENT" with remainingBalance = $0
```

### Scenario: Diner pays with Mercado Pago
```
Given check "CHK-001" has $15,400 remaining
When the diner taps "Pagar con Mercado Pago"
Then POST /api/checks/{id}/payments/mercadopago creates an MP preference
And the diner is redirected to MP checkout
When the diner completes payment on MP
Then MP sends a webhook to POST /api/webhooks/mercadopago
And the server verifies the signature
And fetches payment details from MP API
And creates payment with status APPROVED
And emits PAYMENT_APPROVED event
And the diner's return page shows "Pago aprobado"
```

### Scenario: Circuit breaker opens after MP failures
```
Given the circuit breaker is CLOSED with 4 consecutive failures
When a 5th MP API call fails
Then the circuit breaker transitions to OPEN
And all subsequent MP preference requests return 503
And pwaMenu shows "Servicio de pago temporalmente no disponible"
After 30 seconds, the circuit breaker transitions to SEMI_OPEN
When the next 2 MP API calls succeed
Then the circuit breaker transitions to CLOSED
And MP preference creation works normally
```

### Scenario: Table close after full payment
```
Given check "CHK-001" is PAID (balance = $0)
When the waiter taps "Liberar Mesa" on table "A-05"
Then a confirmation dialog shows: "Duracin: 1h 45m | Total: $15,400 | Pagado: $15,400"
When the waiter confirms
Then POST /api/sessions/{id}/close is called
And the session status is set to CLOSED
And the table state is set to LIBRE
And active service calls are auto-closed
And SESSION_CLOSED event is emitted
And the table card updates to green (LIBRE)
```

### Scenario: Table close blocked by unpaid balance
```
Given check "CHK-001" has $3,000 remaining
When the waiter taps "Liberar Mesa"
Then POST /api/sessions/{id}/close returns 422
And the waiter sees "No se puede liberar - Resta: $3,000"
And the "Liberar Mesa" button remains available
```
