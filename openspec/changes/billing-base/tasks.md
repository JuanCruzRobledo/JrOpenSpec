---
sprint: 10
artifact: tasks
status: complete
---

# Tasks: Llamados de Servicio y Facturacin Base

## Phase 1: Service Calls Backend

### 1.1 ServiceCall model & migration
- Create `ServiceCall` SQLAlchemy model with all fields, constraints, and exclusion constraint for active duplicates
- Create Alembic migration for `service_calls` table with indexes
- **Files**: `app/models/service_call.py`, `alembic/versions/xxx_add_service_calls.py`
- **AC**: Migration runs clean; exclusion constraint prevents duplicate active calls of same type per session

### 1.2 ServiceCall schemas
- Create Pydantic request/response schemas: `ServiceCallCreate`, `ServiceCallResponse`, `ServiceCallListResponse`
- Include validation: call_type must be valid enum, session_id must be UUID
- **Files**: `app/schemas/service_call.py`
- **AC**: Schema validation rejects invalid call types; serialization includes all fields

### 1.3 ServiceCall service layer
- Implement `create_service_call()`: validate session exists, check no duplicate active, create call, insert outbox event
- Implement `acknowledge_call()`: validate ACTIVA state, update to RECONOCIDA, set acknowledgedBy/At, audit
- Implement `close_call()`: validate ACTIVA or RECONOCIDA, update to CERRADA, set closedBy/At, audit
- Implement `get_calls_by_branch()`: filter by branch, optional sector (via table join), optional status
- **Files**: `app/services/service_call_service.py`
- **AC**: State transitions enforce forward-only; 409 on invalid transitions; outbox event created on new call

### 1.4 ServiceCall REST endpoints
- POST /api/sessions/{sessionId}/service-calls — create call
- GET /api/branches/{branchId}/service-calls — list with sector/status filters
- PATCH /api/service-calls/{callId}/acknowledge — acknowledge
- PATCH /api/service-calls/{callId}/close — close
- RBAC: DINER can create; WAITER can create, list, acknowledge, close; ADMIN can list
- **Files**: `app/routers/service_calls.py`
- **AC**: All 4 endpoints return correct status codes; RBAC enforced; sector filtering works

### 1.5 ServiceCall outbox events
- Insert SERVICE_CALL_CREATED event on creation with payload: callId, sessionId, tableId, callType, tableCode
- Insert SERVICE_CALL_UPDATED event on acknowledge/close with payload: callId, newStatus
- **Files**: `app/events/service_call_events.py`
- **AC**: Events appear in outbox table; Gateway publishes to appropriate WebSocket channels

## Phase 2: Service Calls Frontend

### 2.1 pwaMenu — Call waiter UI
- Build `CallWaiterFAB.tsx`: floating button bottom-right, opens type selector modal
- Build `CallTypeSelector.tsx`: 4 type options with icons, disabled state for active calls
- Build `CallStatus.tsx`: shows active call state with animated indicator
- Create `serviceCallStore.ts`: activeCalls map, create/updateStatus actions
- Create `serviceCallService.ts`: createCall(), getActiveCalls() API calls
- **Files**: `pwaMenu/src/service-calls/components/*.tsx`, `pwaMenu/src/service-calls/store/serviceCallStore.ts`, `pwaMenu/src/service-calls/services/serviceCallService.ts`
- **AC**: FAB opens selector; type disabled when active; status updates via WebSocket; feedback shown

### 2.2 pwaWaiter — Service call reception
- Build `useServiceCallDedup.ts`: circular buffer class, add(id) returns boolean (true=new), capacity=100
- Integrate with messageRouter: on SERVICE_CALL_CREATED, check dedup → if new: update store + animate + sound + notify
- Build `ServiceCallAlert.tsx`: inline alert on table card for active calls
- **Files**: `pwaWaiter/src/service-calls/hooks/useServiceCallDedup.ts`, `pwaWaiter/src/service-calls/components/ServiceCallAlert.tsx`
- **AC**: Duplicate IDs ignored; new calls trigger P1 animation + sound + notification; buffer wraps at 100

### 2.3 pwaWaiter — Service call management
- Build `ServiceCallActions.tsx`: "Reconocer" and "Cerrar" buttons in table detail modal
- Create `serviceCallWaiterService.ts`: acknowledge(), close() API calls
- Integrate with table detail modal: show active calls section with actions
- On acknowledge: stop P1 animation (if no other active calls), update call status display
- **Files**: `pwaWaiter/src/service-calls/components/ServiceCallActions.tsx`, `pwaWaiter/src/service-calls/services/serviceCallWaiterService.ts`
- **AC**: Acknowledge/close call API; animation stops on last active call cleared; state updates in real-time

## Phase 3: Check/Bill Backend

### 3.1 Check model & migration
- Create `Check` and `CheckItem` SQLAlchemy models
- Create Alembic migration for `checks` and `check_items` tables with indexes
- Unique constraint on checks.session_id for idempotency
- **Files**: `app/models/check.py`, `alembic/versions/xxx_add_checks.py`
- **AC**: Migration runs clean; session_id unique constraint enforced

### 3.2 Check schemas
- Create Pydantic schemas: `CheckResponse`, `CheckItemResponse`
- Include computed fields: items grouped by round_number
- **Files**: `app/schemas/check.py`
- **AC**: Response includes items with round grouping; all decimal fields serialize correctly

### 3.3 Check service layer
- Implement `create_or_get_check()`:
  1. Check if check exists for session → return if yes (200)
  2. Fetch all non-cancelled order rounds for session
  3. Aggregate items: group by product, sum quantities, calculate subtotals
  4. Create Check + CheckItems in transaction
  5. Update table state to PAGO
  6. Insert CHECK_REQUESTED outbox event
- **Files**: `app/services/check_service.py`
- **AC**: First call creates check (201); second call returns existing (200); cancelled orders excluded; table state updated

### 3.4 Check REST endpoints
- POST /api/sessions/{sessionId}/check — create or get check (idempotent)
- GET /api/checks/{checkId} — get check details
- RBAC: DINER and WAITER can create/view
- **Files**: `app/routers/checks.py`
- **AC**: Idempotent behavior verified; items correctly totalized; RBAC enforced

### 3.5 Check outbox events
- Insert CHECK_REQUESTED event with payload: checkId, sessionId, tableId, total
- **Files**: `app/events/check_events.py`
- **AC**: Event in outbox; Gateway publishes to waiter WebSocket channel

## Phase 4: Check/Bill Frontend

### 4.1 pwaMenu — Check request
- Build `RequestCheckButton.tsx`: "Solicitar Cuenta" button, disabled after check exists
- Build `CheckView.tsx`: itemized view container
- Build `RoundSection.tsx`: items grouped by round with subtotal
- Create `billingStore.ts`: check data, split config, tip config
- Create `billingService.ts`: requestCheck(), getCheck() API calls
- **Files**: `pwaMenu/src/billing/components/RequestCheckButton.tsx`, `pwaMenu/src/billing/components/CheckView.tsx`, `pwaMenu/src/billing/components/RoundSection.tsx`, `pwaMenu/src/billing/store/billingStore.ts`, `pwaMenu/src/billing/services/billingService.ts`
- **AC**: Button requests check; itemized view shows items per round with subtotals; total correct

### 4.2 pwaMenu — Bill splitting
- Build `SplitSelector.tsx`: 3 method options (Igualitaria, Por Consumo, Personalizada)
- Build `EqualSplit.tsx`: people count input, auto-calculated per-person amount
- Build `ConsumptionSplit.tsx`: drag/tap items to assign to people, per-person totals
- Build `CustomSplit.tsx`: manual amount entry per person, validation against total
- Implement `useSplit.ts` hook: split calculation logic for all 3 methods, rounding to 2 decimals, remainder to last person
- **Files**: `pwaMenu/src/billing/components/SplitSelector.tsx`, `pwaMenu/src/billing/components/EqualSplit.tsx`, `pwaMenu/src/billing/components/ConsumptionSplit.tsx`, `pwaMenu/src/billing/components/CustomSplit.tsx`, `pwaMenu/src/billing/hooks/useSplit.ts`
- **AC**: All 3 split methods calculate correctly; rounding handles edge cases; amounts sum to total

### 4.3 pwaMenu — Tip calculation
- Build `TipSelector.tsx`: preset buttons (0%, 10%, 15%, 20%) + custom input
- Implement `useTip.ts` hook: tip on pre-split total, proportional distribution per charge
- Build `SplitSummary.tsx`: final charges per person (base + tip = total)
- **Files**: `pwaMenu/src/billing/components/TipSelector.tsx`, `pwaMenu/src/billing/hooks/useTip.ts`, `pwaMenu/src/billing/components/SplitSummary.tsx`
- **AC**: Tip presets work; custom tip validated (0-100%); proportional distribution correct; summary shows per-person breakdown

## Phase 5: Integration

### 5.1 WebSocket event integration
- Add SERVICE_CALL_CREATED, SERVICE_CALL_UPDATED, CHECK_REQUESTED to Gateway WebSocket broadcast
- pwaMenu: handle SERVICE_CALL_UPDATED events to update call status display
- pwaWaiter: handle CHECK_REQUESTED to update table card (Priority 5 purple pulse)
- **Files**: Gateway event handlers, pwaMenu/pwaWaiter message routers
- **AC**: All events flow end-to-end: backend → outbox → Gateway → WebSocket → frontend stores → UI update

### 5.2 End-to-end validation
- Verify: diner creates service call → waiter receives alert → acknowledges → closes
- Verify: diner requests check → itemized view → split calculation → tip
- Verify: idempotent check creation on retry/double-tap
- Verify: dedup buffer prevents duplicate alerts on reconnection
- **AC**: All flows work end-to-end; edge cases handled (duplicate calls, offline replay, reconnection)
