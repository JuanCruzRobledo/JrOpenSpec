---
sprint: 9
artifact: spec
status: complete
---

# Spec: pwaWaiter Completo

## Requirements (RFC 2119)

### Authentication
- The app MUST present a branch selection screen before login
- The app MUST authenticate via POST /api/auth/login with email + password
- The app MUST verify the authenticated user is assigned to the selected branch's sector via GET /api/branches/{branchId}/staff/me
- The app MUST redirect to login if JWT token is expired or invalid
- The app MUST store JWT in memory (Zustand) and refresh token in httpOnly cookie
- The app SHOULD display a meaningful error if sector assignment is missing

### Header
- The header MUST display: restaurant logo, branch name, WebSocket status indicator (green=connected, red=disconnected), pending orders counter badge, user email, logout button
- The WebSocket indicator MUST update within 2 seconds of connection state change
- The pending counter MUST reflect unacknowledged orders for the waiter's assigned sector

### Tab Navigation
- The app MUST provide two tabs: "Comensales" (tables) and "Autogestin" (comanda)
- Tab state MUST persist during the session (no re-fetch on tab switch)
- Active tab MUST be visually distinguished

### Tables View
- The tables view MUST display filter options: Todas, Urgentes, Activas, Libres, Fuera de Servicio
- Tables MUST be grouped by sector with sector headers
- Each table card MUST display: table code (large font), background color reflecting current state, active order indicator, badges for rounds count, service calls count, and pending check request
- Filter selection MUST update the view without full page reload
- The view MUST support pull-to-refresh gesture on mobile

### Table Card States & Colors
| State | Color | Description |
|-------|-------|-------------|
| LIBRE | `bg-green-100` | Available, no active session |
| OCUPADA | `bg-blue-100` | Active session, no pending items |
| CON_PEDIDO | `bg-yellow-100` | Has pending order in kitchen |
| ITEMS_LISTOS | `bg-orange-100` | Items ready for pickup |
| PAGO | `bg-purple-100` | Check requested |
| FUERA_DE_SERVICIO | `bg-gray-200` | Disabled |

### Animation Priority System
- The app MUST implement 5 priority animation levels on table cards
- Priority 1 (HIGHEST): Red blink at 3s interval — active service call (llamado)
- Priority 2: Orange blink at 5s interval — items ready AND still items in kitchen
- Priority 3: Blue blink at 1.5s interval — table state just changed (5 second duration)
- Priority 4: Yellow pulse at 2s interval — new order placed
- Priority 5 (LOWEST): Purple pulse — check/bill requested
- Only the HIGHEST priority animation MUST be active at any time (no stacking)
- Animations MUST use CSS animations (not JS intervals) for performance
- Priority 3 animations MUST auto-expire after 5 seconds

### Table Detail Modal
- Tapping a table card MUST open a detail modal
- The modal MUST display: table code, current state, session duration, total items ordered, total amount
- The modal MUST show service calls with acknowledge/close actions
- The modal MUST display an alert banner when items are ready for pickup
- The modal MUST list order rounds with filtering (all / pending / ready / delivered)
- The modal MUST provide action buttons: add order, change state, close session
- The modal MUST be closable via X button, ESC key, or backdrop tap

### Comanda Rapida (Quick Order)
- The comanda tab MUST first require selecting a target table
- After table selection, the interface MUST split into: compact menu (left/top) and cart (right/bottom)
- The menu panel MUST display categories with product cards (name, price, image thumbnail)
- The menu panel MUST include a search bar with debounced input (300ms)
- Adding a product MUST immediately reflect in the cart with quantity controls
- The cart MUST display: item list with quantities, subtotal per item, order total, notes field, submit button
- Submit MUST POST to /api/sessions/{sessionId}/orders and show success/error feedback
- On mobile, the layout MUST stack vertically (menu top, cart bottom) with a collapsible cart

### Real-time Updates
- The app MUST connect via WebSocket to ws(s)://{host}/ws/waiter?branch={branchId}&sector={sectorId}
- WebSocket MUST be the primary update channel for: table state changes, new orders, order status updates, service calls
- The app MUST poll GET /api/branches/{branchId}/tables every 60 seconds as fallback
- The app MUST provide a manual refresh button in the header
- The app MUST support pull-to-refresh on the tables view
- On WebSocket message, the app MUST update Zustand store which triggers React re-render

### Offline & Retry Queue
- The app MUST detect offline state via `navigator.onLine` + failed fetch detection
- When offline, write operations MUST be queued in IndexedDB
- Each queued operation MUST store: id (UUID), endpoint, method, payload, timestamp, retryCount
- On reconnection, queued operations MUST be replayed in FIFO order
- Each operation MUST retry up to 3 times with exponential backoff (1s, 2s, 4s)
- The queue MUST deduplicate operations by endpoint + payload hash
- The app MUST display a banner indicating offline mode and queued operation count

### Notifications
- The app MUST request browser notification permission on first relevant event
- Notifications MUST fire for: service calls (Priority 1), items ready (Priority 2), new orders in sector
- Each notification MUST include a sound alert (configurable)
- Notifications MUST be grouped by type to avoid flooding
- The app SHOULD use the Notification API with `tag` for deduplication

### PWA Configuration
- The app MUST include a valid manifest.json with: name, short_name, icons (192x192, 512x512), start_url, display: standalone, theme_color, background_color
- The app MUST register a service worker for asset caching
- The manifest MUST define shortcuts: "Mesas" (tables view), "Comanda" (quick order)
- The app MUST handle the `beforeinstallprompt` event for install promotion

## Data Models

### WaiterTableView
```typescript
interface WaiterTableView {
  id: string;                    // UUID
  code: string;                  // e.g., "A-01"
  sectorId: string;              // UUID
  sectorName: string;            // e.g., "Terraza"
  state: TableState;             // enum
  sessionId: string | null;      // UUID if active session
  sessionStartedAt: string | null; // ISO 8601
  activeOrderCount: number;
  pendingItemCount: number;
  readyItemCount: number;
  roundCount: number;
  activeServiceCallCount: number;
  checkRequested: boolean;
  totalAmount: number;           // decimal
}

type TableState = 'LIBRE' | 'OCUPADA' | 'CON_PEDIDO' | 'ITEMS_LISTOS' | 'PAGO' | 'FUERA_DE_SERVICIO';
```

### WaiterOrderRound
```typescript
interface WaiterOrderRound {
  id: string;                    // UUID
  roundNumber: number;
  createdAt: string;             // ISO 8601
  items: WaiterOrderItem[];
  status: RoundStatus;
}

interface WaiterOrderItem {
  id: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  notes: string | null;
  status: ItemStatus;
}

type RoundStatus = 'PENDING' | 'IN_PROGRESS' | 'READY' | 'DELIVERED';
type ItemStatus = 'PENDING' | 'PREPARING' | 'READY' | 'DELIVERED';
```

### OfflineOperation
```typescript
interface OfflineOperation {
  id: string;                    // UUID
  endpoint: string;              // e.g., "/api/sessions/123/orders"
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  payload: unknown;
  payloadHash: string;           // SHA-256 for dedup
  timestamp: number;             // Unix ms
  retryCount: number;            // 0..3
  status: 'QUEUED' | 'RETRYING' | 'FAILED';
}
```

### WebSocketMessage
```typescript
interface WaiterWSMessage {
  type: WaiterWSEventType;
  tableId: string;
  data: Record<string, unknown>;
  timestamp: string;             // ISO 8601
}

type WaiterWSEventType =
  | 'TABLE_STATE_CHANGED'
  | 'ORDER_CREATED'
  | 'ORDER_STATUS_CHANGED'
  | 'ITEM_STATUS_CHANGED'
  | 'SERVICE_CALL_CREATED'
  | 'SERVICE_CALL_UPDATED'
  | 'CHECK_REQUESTED';
```

## API Contracts

### GET /api/branches/{branchId}/tables
**Auth**: Bearer JWT (role: WAITER)
**Query**: `?sector={sectorId}` (optional filter)
**Response 200**:
```json
{
  "tables": [WaiterTableView],
  "lastUpdated": "2026-03-19T10:00:00Z"
}
```

### GET /api/tables/{tableId}/detail
**Auth**: Bearer JWT (role: WAITER)
**Response 200**:
```json
{
  "table": WaiterTableView,
  "session": {
    "id": "uuid",
    "startedAt": "ISO8601",
    "diners": 4,
    "rounds": [WaiterOrderRound],
    "serviceCalls": [ServiceCallView],
    "totalAmount": 15400.00
  }
}
```

### POST /api/sessions/{sessionId}/orders
**Auth**: Bearer JWT (role: WAITER)
**Request**:
```json
{
  "items": [
    {
      "productId": "uuid",
      "quantity": 2,
      "notes": "sin sal"
    }
  ]
}
```
**Response 201**:
```json
{
  "orderId": "uuid",
  "roundNumber": 3,
  "items": [{ "id": "uuid", "productName": "Milanesa", "quantity": 2, "status": "PENDING" }]
}
```
**Response 409**: Session closed or table not in valid state

### WebSocket ws(s)://{host}/ws/waiter
**Query params**: `branch={branchId}&sector={sectorId}&token={jwt}`
**Messages (server → client)**:
```json
{
  "type": "TABLE_STATE_CHANGED",
  "tableId": "uuid",
  "data": { "previousState": "OCUPADA", "newState": "CON_PEDIDO" },
  "timestamp": "ISO8601"
}
```

## Scenarios

### Scenario: Waiter logs in and sees assigned tables
```
Given the waiter selects branch "Sucursal Centro"
And enters valid credentials
When the login succeeds
Then the app verifies sector assignment via /api/branches/{id}/staff/me
And displays the tables view filtered to the waiter's assigned sector
And the WebSocket connects with branch and sector parameters
And the header shows branch name "Sucursal Centro" with green WebSocket indicator
```

### Scenario: Table receives a service call
```
Given the waiter is viewing the tables grid
When a SERVICE_CALL_CREATED WebSocket message arrives for table "A-05"
Then table "A-05" card starts Priority 1 animation (red blink, 3s interval)
And a browser notification fires with sound: "Mesa A-05: Llamado de servicio"
And the service call badge on the card increments by 1
And any lower-priority animation on "A-05" is suppressed
```

### Scenario: Waiter creates a quick order
```
Given the waiter is on the "Autogestin" tab
And selects table "B-02" from the table picker
When the waiter searches "milane" in the menu search bar
Then products matching "milane" appear after 300ms debounce
When the waiter taps "Milanesa Napolitana" and sets quantity to 2
Then the cart shows "Milanesa Napolitana x2" with subtotal
When the waiter taps "Enviar Pedido"
Then POST /api/sessions/{sessionId}/orders is called
And success toast appears: "Pedido enviado - Ronda #3"
And the table card updates to CON_PEDIDO state
```

### Scenario: Offline order queuing
```
Given the waiter's device loses network connectivity
And the offline banner shows "Sin conexin - 0 operaciones pendientes"
When the waiter creates an order for table "C-01"
Then the operation is saved to IndexedDB with status QUEUED
And the offline banner updates to "Sin conexin - 1 operacin pendiente"
When connectivity is restored
Then the queued operation is replayed via POST /api/sessions/{sessionId}/orders
And on success, the operation is removed from IndexedDB
And the offline banner disappears
```

### Scenario: Animation priority resolution
```
Given table "A-03" has a pending check request (Priority 5 purple pulse)
When items become ready for that table (Priority 2 orange blink)
Then the purple pulse stops
And the orange blink animation starts at 5s interval
When a service call arrives for "A-03" (Priority 1 red blink)
Then the orange blink stops
And the red blink animation starts at 3s interval
When the waiter acknowledges the service call
Then the red blink stops
And the orange blink resumes (items still ready)
```

### Scenario: Pull-to-refresh syncs data
```
Given the waiter is on the tables view
When the waiter pulls down on the table grid
Then a loading spinner appears at the top
And GET /api/branches/{branchId}/tables is called
And the table grid re-renders with fresh data
And the spinner disappears
And the last-updated timestamp in the store is refreshed
```
