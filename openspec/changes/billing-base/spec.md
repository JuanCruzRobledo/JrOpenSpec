---
sprint: 10
artifact: spec
status: complete
---

# Spec: Llamados de Servicio y Facturacin Base

## Requirements (RFC 2119)

### Service Calls — Backend
- The system MUST support a ServiceCall entity with types: RECARGA, CUENTA, QUEJA, OTRO
- Each ServiceCall MUST have states: ACTIVA → RECONOCIDA → CERRADA (forward-only state machine)
- The system MUST associate each ServiceCall with a session, table, and branch
- The system MUST record the creating user (diner session) and the acknowledging/closing user (waiter)
- Queries MUST support filtering by sector (via table → sector relationship)
- Each state transition MUST be audited with timestamp and actor
- On creation, the system MUST insert a SERVICE_CALL_CREATED event into the outbox table
- The system MUST NOT allow creating a new RECARGA or CUENTA call if one is already ACTIVA for the same session

### Service Calls — pwaMenu
- The diner app MUST display a "Llamar Mozo" floating action button on the session view
- Tapping the button MUST open a type selector: Recarga, Cuenta, Queja, Otro
- After submission, the UI MUST show visual feedback of call state (ACTIVA → RECONOCIDA → CERRADA)
- The button MUST be disabled while an ACTIVA call of the same type exists
- The app MUST update call state via WebSocket events

### Service Calls — pwaWaiter
- On SERVICE_CALL_CREATED WebSocket event, the waiter app MUST:
  - Trigger Priority 1 animation (red blink 3s) on the affected table card
  - Play an alert sound
  - Fire a browser notification: "Mesa {code}: {callType}"
- The waiter app MUST maintain a deduplication buffer of the last 100 service call IDs
- Duplicate events (same ID) MUST be silently ignored
- The table detail modal MUST show active service calls with "Reconocer" and "Cerrar" buttons
- "Reconocer" MUST PATCH the call to RECONOCIDA state
- "Cerrar" MUST PATCH the call to CERRADA state
- On RECONOCIDA, the Priority 1 animation MUST stop (unless another ACTIVA call exists)

### Check/Bill — Backend
- POST /api/sessions/{sessionId}/check MUST be idempotent: if a Check already exists for the session, return it
- The Check MUST totalize all order rounds: list all items with quantities, unit prices, subtotals, and a grand total
- On check creation, the system MUST transition the table state to PAGO
- On check creation, the system MUST insert a CHECK_REQUESTED event into the outbox table
- The Check MUST NOT include items from cancelled/rejected orders

### Check/Bill — pwaMenu
- The diner app MUST display a "Solicitar Cuenta" button on the session view
- After requesting, the app MUST display the itemized check view:
  - Items grouped by round (Ronda 1, Ronda 2, etc.)
  - Each item: name, quantity, unit price, subtotal
  - Subtotal per round
  - Grand total at bottom
- The button MUST be disabled once a check exists (idempotent — re-tapping shows existing check)

### Bill Splitting — pwaMenu
- The app MUST offer 3 split methods:
  1. **Igualitaria (Equal)**: Grand total / number of people
  2. **Por Consumo (By consumption)**: Each person selects their items, charged accordingly
  3. **Personalizada (Custom)**: Manual amount entry per person, validated against total
- The app MUST offer tip presets: 0%, 10%, 15%, 20%, and a custom percentage field
- Tip MUST be calculated on the pre-split grand total
- In equal split: tip is divided equally
- In consumption/custom split: tip is distributed proportionally to each person's charge
- All amounts MUST be rounded to 2 decimal places
- Rounding remainder (if any) MUST be added to the last person's charge
- The split view is informational only in this sprint (actual payment in Sprint 11)

## Data Models

### ServiceCall
```python
class ServiceCall(BaseModel):
    id: UUID
    session_id: UUID                    # FK to Session
    table_id: UUID                      # FK to Table (denormalized for query perf)
    branch_id: UUID                     # FK to Branch (denormalized)
    call_type: ServiceCallType          # RECARGA | CUENTA | QUEJA | OTRO
    status: ServiceCallStatus           # ACTIVA | RECONOCIDA | CERRADA
    created_by: UUID | None             # diner user or null (anonymous)
    acknowledged_by: UUID | None        # waiter user
    acknowledged_at: datetime | None
    closed_by: UUID | None              # waiter user
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

class ServiceCallType(str, Enum):
    RECARGA = "RECARGA"
    CUENTA = "CUENTA"
    QUEJA = "QUEJA"
    OTRO = "OTRO"

class ServiceCallStatus(str, Enum):
    ACTIVA = "ACTIVA"
    RECONOCIDA = "RECONOCIDA"
    CERRADA = "CERRADA"
```

### Check
```python
class Check(BaseModel):
    id: UUID
    session_id: UUID                    # FK to Session (unique — one check per session)
    branch_id: UUID                     # FK to Branch
    table_id: UUID                      # FK to Table
    items: list[CheckItem]              # Totalized items
    subtotal: Decimal                   # Sum of all items
    total: Decimal                      # = subtotal (taxes/discounts in future sprints)
    status: CheckStatus                 # OPEN | PAID | CANCELLED
    created_at: datetime
    updated_at: datetime

class CheckItem(BaseModel):
    id: UUID
    check_id: UUID
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal                   # quantity * unit_price
    round_number: int                   # Which round this came from

class CheckStatus(str, Enum):
    OPEN = "OPEN"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
```

### Split (Frontend only — not persisted in Sprint 10)
```typescript
interface SplitConfig {
  method: 'equal' | 'by_consumption' | 'custom';
  people: number;
  tipPercentage: number;              // 0, 10, 15, 20, or custom
  charges: SplitCharge[];
}

interface SplitCharge {
  personIndex: number;
  items: CheckItem[];                 // Only for 'by_consumption'
  baseAmount: number;                 // Pre-tip amount
  tipAmount: number;                  // Proportional tip
  totalAmount: number;                // base + tip
}
```

## API Contracts

### POST /api/sessions/{sessionId}/service-calls
**Auth**: Bearer JWT (role: DINER or WAITER)
**Request**:
```json
{
  "callType": "RECARGA"
}
```
**Response 201**:
```json
{
  "id": "uuid",
  "sessionId": "uuid",
  "tableId": "uuid",
  "callType": "RECARGA",
  "status": "ACTIVA",
  "createdAt": "ISO8601"
}
```
**Response 409**: Active call of same type already exists

### GET /api/branches/{branchId}/service-calls
**Auth**: Bearer JWT (role: WAITER, ADMIN)
**Query**: `?sector={sectorId}&status=ACTIVA`
**Response 200**:
```json
{
  "serviceCalls": [
    {
      "id": "uuid",
      "sessionId": "uuid",
      "tableId": "uuid",
      "tableCode": "A-05",
      "callType": "RECARGA",
      "status": "ACTIVA",
      "createdAt": "ISO8601"
    }
  ]
}
```

### PATCH /api/service-calls/{callId}/acknowledge
**Auth**: Bearer JWT (role: WAITER)
**Response 200**:
```json
{
  "id": "uuid",
  "status": "RECONOCIDA",
  "acknowledgedBy": "uuid",
  "acknowledgedAt": "ISO8601"
}
```
**Response 409**: Call not in ACTIVA state

### PATCH /api/service-calls/{callId}/close
**Auth**: Bearer JWT (role: WAITER)
**Response 200**:
```json
{
  "id": "uuid",
  "status": "CERRADA",
  "closedBy": "uuid",
  "closedAt": "ISO8601"
}
```
**Response 409**: Call not in ACTIVA or RECONOCIDA state

### POST /api/sessions/{sessionId}/check
**Auth**: Bearer JWT (role: DINER or WAITER)
**Response 201** (first call):
```json
{
  "id": "uuid",
  "sessionId": "uuid",
  "items": [
    {
      "id": "uuid",
      "productName": "Milanesa Napolitana",
      "quantity": 2,
      "unitPrice": 4500.00,
      "subtotal": 9000.00,
      "roundNumber": 1
    }
  ],
  "subtotal": 15400.00,
  "total": 15400.00,
  "status": "OPEN",
  "createdAt": "ISO8601"
}
```
**Response 200** (subsequent calls — idempotent): Same body as above

### GET /api/checks/{checkId}
**Auth**: Bearer JWT
**Response 200**: Same schema as POST response

## Scenarios

### Scenario: Diner calls waiter for recharge
```
Given a diner has an active session at table "A-05"
When the diner taps "Llamar Mozo" and selects "Recarga"
Then POST /api/sessions/{id}/service-calls is called with callType "RECARGA"
And a ServiceCall is created with status ACTIVA
And an outbox event SERVICE_CALL_CREATED is inserted
And the "Llamar Mozo" button for RECARGA becomes disabled
And the UI shows "Llamado activo: Recarga - Esperando..."
```

### Scenario: Waiter receives and handles service call
```
Given the waiter is viewing tables in sector "Terraza"
When a SERVICE_CALL_CREATED WebSocket message arrives for table "A-05"
And the service call ID is not in the dedup buffer
Then table "A-05" starts Priority 1 animation (red blink)
And an alert sound plays
And a browser notification shows "Mesa A-05: Recarga"
When the waiter opens table "A-05" detail and taps "Reconocer"
Then PATCH /api/service-calls/{id}/acknowledge is called
And the call status updates to RECONOCIDA
And the red blink animation stops (if no other ACTIVA calls)
And the diner sees "Llamado reconocido - El mozo viene en camino"
When the waiter taps "Cerrar" after serving
Then PATCH /api/service-calls/{id}/close is called
And the call status updates to CERRADA
```

### Scenario: Duplicate WebSocket message ignored
```
Given the waiter's dedup buffer contains service call ID "abc-123"
When a SERVICE_CALL_CREATED WebSocket message arrives with ID "abc-123"
Then the message is silently discarded
And no animation, sound, or notification is triggered
And the dedup buffer remains unchanged
```

### Scenario: Diner requests check
```
Given a diner has completed ordering (2 rounds, 5 items total)
When the diner taps "Solicitar Cuenta"
Then POST /api/sessions/{id}/check is called
And a Check is created totalizing all items across rounds
And the table state transitions to PAGO
And a CHECK_REQUESTED outbox event is inserted
And the diner sees the itemized view:
  - Ronda 1: Milanesa x2 ($9,000), Coca-Cola x2 ($3,000) — Subtotal: $12,000
  - Ronda 2: Flan x1 ($3,400) — Subtotal: $3,400
  - Total: $15,400
```

### Scenario: Equal bill split with tip
```
Given a check total of $15,400 for 4 people
When the diner selects "Igualitaria" split with 10% tip
Then tip = $15,400 * 0.10 = $1,540
And total with tip = $16,940
And each person pays = $16,940 / 4 = $4,235.00
And the split view shows 4 charges of $4,235.00 each
```

### Scenario: Consumption-based split with tip
```
Given a check with items: Milanesa ($4,500), Ensalada ($3,200), 2x Cerveza ($2,400 each)
And Person 1 claims: Milanesa + Cerveza = $6,900
And Person 2 claims: Ensalada + Cerveza = $5,600
When 15% tip is applied
Then tip = $12,500 * 0.15 = $1,875
And Person 1 tip = $1,875 * (6,900/12,500) = $1,035.00
And Person 2 tip = $1,875 * (5,600/12,500) = $840.00
And Person 1 total = $6,900 + $1,035 = $7,935.00
And Person 2 total = $5,600 + $840 = $6,440.00
```

### Scenario: Idempotent check request
```
Given a check already exists for session "xyz"
When the diner taps "Solicitar Cuenta" again
Then POST /api/sessions/{id}/check returns 200 with the existing check
And no new Check is created
And no duplicate outbox event is inserted
```
