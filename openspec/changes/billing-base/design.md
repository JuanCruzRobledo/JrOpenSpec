---
sprint: 10
artifact: design
status: complete
---

# Design: Llamados de Servicio y Facturacin Base

## Architecture Decisions

### AD-1: Forward-only State Machine for ServiceCall
- **Decision**: ServiceCall states are strictly forward: ACTIVA → RECONOCIDA → CERRADA. No backward transitions.
- **Rationale**: Simplifies logic, prevents race conditions, ensures audit trail integrity. A waiter can close directly from ACTIVA (skipping RECONOCIDA) for efficiency.
- **Tradeoff**: Cannot "un-acknowledge" — acceptable since the physical action already happened.

### AD-2: Dedup Ring Buffer (100 IDs)
- **Decision**: pwaWaiter maintains a circular buffer of last 100 service call IDs to deduplicate WebSocket messages.
- **Rationale**: WebSocket reconnections and outbox replay can cause duplicate delivery. 100 is sufficient for any realistic burst.
- **Tradeoff**: Memory cost negligible (100 UUIDs = ~3.6KB). Oldest IDs evicted — acceptable since old duplicates are unlikely.

### AD-3: Idempotent Check Generation
- **Decision**: POST /api/sessions/{id}/check returns 201 on first call, 200 on subsequent calls with same data. Uses session_id unique constraint.
- **Rationale**: Network retries, double-taps, and offline replay can cause duplicate requests. Idempotency ensures exactly-once semantics.
- **Tradeoff**: None — purely beneficial.

### AD-4: Frontend-only Split (No Persistence)
- **Decision**: Bill splitting logic runs entirely in pwaMenu frontend. Split configuration is NOT persisted to backend in Sprint 10.
- **Rationale**: Splitting is informational for diners to coordinate. Actual payment tracking (Sprint 11) will persist payment records.
- **Tradeoff**: Split config lost on page refresh — acceptable since it's a transient coordination tool.

### AD-5: Denormalized table_id and branch_id on ServiceCall
- **Decision**: Store table_id and branch_id directly on ServiceCall (denormalized from Session).
- **Rationale**: Enables efficient sector-filtered queries without joining through Session → Table → Sector. Critical for waiter real-time view performance.
- **Tradeoff**: Data duplication — mitigated by immutability (session's table doesn't change).

## DB Schema

### service_calls table
```sql
CREATE TABLE service_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id),
    table_id UUID NOT NULL REFERENCES tables(id),
    branch_id UUID NOT NULL REFERENCES branches(id),
    call_type VARCHAR(20) NOT NULL CHECK (call_type IN ('RECARGA', 'CUENTA', 'QUEJA', 'OTRO')),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVA' CHECK (status IN ('ACTIVA', 'RECONOCIDA', 'CERRADA')),
    created_by UUID REFERENCES users(id),
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    closed_by UUID REFERENCES users(id),
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate active calls of same type per session
    CONSTRAINT uq_active_call_type EXCLUDE USING btree (
        session_id WITH =,
        call_type WITH =
    ) WHERE (status = 'ACTIVA')
);

CREATE INDEX idx_service_calls_branch_status ON service_calls(branch_id, status);
CREATE INDEX idx_service_calls_table ON service_calls(table_id);
CREATE INDEX idx_service_calls_session ON service_calls(session_id);
```

### checks table
```sql
CREATE TABLE checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES sessions(id),  -- one check per session
    branch_id UUID NOT NULL REFERENCES branches(id),
    table_id UUID NOT NULL REFERENCES tables(id),
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0,
    total DECIMAL(12,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'PAID', 'CANCELLED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_checks_session ON checks(session_id);
CREATE INDEX idx_checks_branch ON checks(branch_id);
```

### check_items table
```sql
CREATE TABLE check_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_id UUID NOT NULL REFERENCES checks(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    product_name VARCHAR(255) NOT NULL,      -- snapshot at check time
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL,       -- snapshot at check time
    subtotal DECIMAL(12,2) NOT NULL,         -- quantity * unit_price
    round_number INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_check_items_check ON check_items(check_id);
```

## File Structure

### Backend additions
```
app/
├── models/
│   ├── service_call.py              # ServiceCall SQLAlchemy model
│   └── check.py                     # Check + CheckItem models
├── schemas/
│   ├── service_call.py              # Pydantic schemas
│   └── check.py                     # Pydantic schemas
├── services/
│   ├── service_call_service.py      # Business logic + state machine
│   └── check_service.py             # Check generation + totalization
├── routers/
│   ├── service_calls.py             # REST endpoints
│   └── checks.py                    # REST endpoints
└── events/
    ├── service_call_events.py       # Outbox integration
    └── check_events.py              # Outbox integration
```

### pwaMenu additions
```
pwaMenu/src/
├── service-calls/
│   ├── components/
│   │   ├── CallWaiterFAB.tsx        # Floating action button
│   │   ├── CallTypeSelector.tsx     # Type picker modal
│   │   └── CallStatus.tsx           # Active call status indicator
│   ├── store/
│   │   └── serviceCallStore.ts
│   └── services/
│       └── serviceCallService.ts
├── billing/
│   ├── components/
│   │   ├── RequestCheckButton.tsx   # "Solicitar Cuenta" button
│   │   ├── CheckView.tsx            # Itemized check display
│   │   ├── RoundSection.tsx         # Items grouped by round
│   │   ├── SplitSelector.tsx        # Split method picker
│   │   ├── EqualSplit.tsx           # Equal division view
│   │   ├── ConsumptionSplit.tsx     # By-consumption assignment
│   │   ├── CustomSplit.tsx          # Manual amount entry
│   │   ├── TipSelector.tsx          # Tip percentage presets
│   │   └── SplitSummary.tsx         # Final charges per person
│   ├── store/
│   │   └── billingStore.ts
│   ├── hooks/
│   │   ├── useSplit.ts              # Split calculation logic
│   │   └── useTip.ts                # Tip calculation logic
│   └── services/
│       └── billingService.ts
```

### pwaWaiter additions
```
pwaWaiter/src/
├── service-calls/
│   ├── components/
│   │   ├── ServiceCallAlert.tsx     # In-card alert indicator
│   │   └── ServiceCallActions.tsx   # Acknowledge + Close buttons
│   ├── hooks/
│   │   └── useServiceCallDedup.ts   # 100-ID ring buffer
│   └── services/
│       └── serviceCallWaiterService.ts
```

## Component Trees

### pwaMenu — Service Calls
```
<SessionView>
  └── <CallWaiterFAB>
        └── <CallTypeSelector> (modal)
              ├── <TypeOption label="Recarga" />
              ├── <TypeOption label="Cuenta" />
              ├── <TypeOption label="Queja" />
              └── <TypeOption label="Otro" />
  └── <CallStatus> (when active call exists)
```

### pwaMenu — Billing
```
<SessionView>
  └── <RequestCheckButton />
  └── <CheckView> (after check requested)
        ├── <RoundSection> (per round)
        │   └── item rows (name, qty, price, subtotal)
        ├── <TotalBar subtotal={} total={} />
        ├── <SplitSelector method={} onChange={} />
        ├── [method=equal]    <EqualSplit people={} total={} />
        ├── [method=consumption] <ConsumptionSplit items={} people={} />
        ├── [method=custom]   <CustomSplit people={} total={} />
        ├── <TipSelector percentage={} onChange={} />
        └── <SplitSummary charges={} />
```

## Sequence Diagrams

### Service Call Flow
```
Diner           pwaMenu           API             Outbox          Gateway         pwaWaiter
  |                |                |                |               |               |
  |--tap "Llamar"->|                |                |               |               |
  |                |--POST /service-calls----------->|               |               |
  |                |                |--insert call-->|               |               |
  |                |                |--insert event->|               |               |
  |                |<--201 {call}---|                |               |               |
  |                |                |                |--publish------>|               |
  |                |                |                |               |--WS message--->|
  |                |                |                |               |               |--dedup check
  |                |                |                |               |               |--animate P1
  |                |                |                |               |               |--play sound
  |                |                |                |               |               |--notify
  |                |                |                |               |               |
  |                |                |<--PATCH /acknowledge-----------|               |
  |                |                |--update call-->|               |               |
  |                |                |--insert event->|               |               |
  |                |<--WS: RECONOCIDA|               |               |               |
  |--"Reconocido"->|                |                |               |               |
```

### Check Generation Flow
```
Diner           pwaMenu           API             DB              Outbox
  |                |                |                |               |
  |--"Solicitar Cuenta"->|         |                |               |
  |                |--POST /check->|                |               |
  |                |                |--check exists? |               |
  |                |                |  NO            |               |
  |                |                |--fetch rounds->|               |
  |                |                |--totalize items|               |
  |                |                |--insert check->|               |
  |                |                |--insert items->|               |
  |                |                |--update table  |               |
  |                |                |  state=PAGO    |               |
  |                |                |--insert event--|-------------->|
  |                |<--201 {check}--|                |               |
  |                |--render CheckView               |               |
  |<--itemized bill|                |                |               |
```

### Split Calculation (Frontend Only)
```
Diner           SplitSelector     useSplit          useTip          SplitSummary
  |                |                |                  |               |
  |--select "Equal, 4 people"----->|                  |               |
  |                |                |--total/4-------->|               |
  |--select "15% tip"------------>|                   |               |
  |                |                |<--tip/4----------|               |
  |                |                |--charges[]------>|               |
  |                |                |                  |   render charges
  |<--see per-person totals--------|                  |               |
```

## State Machine Diagram

```
ServiceCall States:
                    ┌──────────────────┐
                    │                  │
    ┌───────┐  create  ┌─────────┐  ack   ┌─────────────┐  close  ┌─────────┐
    │ (new) │ ───────> │ ACTIVA  │ ──────> │ RECONOCIDA  │ ──────> │ CERRADA │
    └───────┘          └─────────┘         └─────────────┘         └─────────┘
                            │                                           ▲
                            │              close (skip ack)             │
                            └───────────────────────────────────────────┘

Check States:
    ┌───────┐  create  ┌──────┐   all paid   ┌──────┐
    │ (new) │ ───────> │ OPEN │ ───────────> │ PAID │
    └───────┘          └──────┘              └──────┘
                           │
                           │  cancel
                           ▼
                       ┌───────────┐
                       │ CANCELLED │
                       └───────────┘
```
