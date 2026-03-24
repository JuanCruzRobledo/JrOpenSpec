---
sprint: 9
artifact: tasks
status: complete
---

# Tasks: pwaWaiter Completo

## Phase 1: Project Scaffold & Auth

### 1.1 Initialize Vite project
- Create React 19 + TypeScript + Vite project in `pwaWaiter/`
- Configure `tsconfig.json` with strict mode, path aliases (`@/`)
- Configure `vite.config.ts` with PWA plugin, proxy for API
- Install dependencies: react, react-dom, zustand, tailwindcss, @tailwindcss/vite, idb, uuid
- **Files**: `pwaWaiter/package.json`, `pwaWaiter/vite.config.ts`, `pwaWaiter/tsconfig.json`, `pwaWaiter/tailwind.config.ts`
- **AC**: `npm run dev` starts without errors, TypeScript strict compiles clean

### 1.2 TailwindCSS setup with animation keyframes
- Configure Tailwind with custom colors for table states
- Add all 5 priority animation keyframes in `src/index.css`
- Define animation utility classes: `animate-blink-red`, `animate-blink-orange`, `animate-blink-blue`, `animate-pulse-yellow`, `animate-pulse-purple`
- **Files**: `pwaWaiter/tailwind.config.ts`, `pwaWaiter/src/index.css`
- **AC**: All 5 animation classes render correctly when applied to a div

### 1.3 Shared components & API client
- Build `Modal` component with ESC close, backdrop click, focus trap
- Build `Button`, `Badge`, `Toast`, `Spinner`, `ErrorBoundary` components
- Build `client.ts` fetch wrapper with Bearer token injection, 401 redirect, offline detection
- **Files**: `pwaWaiter/src/shared/components/*.tsx`, `pwaWaiter/src/shared/api/client.ts`, `pwaWaiter/src/shared/api/interceptors.ts`
- **AC**: Modal opens/closes via ESC and backdrop; API client adds auth header; 401 triggers redirect

### 1.4 Auth store & service
- Create `authStore.ts` with: user, token, branch, sector, login/logout/refreshToken actions
- Create `authService.ts` with: login(), getStaffAssignment(), refreshToken() API calls
- Token stored in Zustand (memory), refresh token in httpOnly cookie (handled by backend)
- **Files**: `pwaWaiter/src/auth/store/authStore.ts`, `pwaWaiter/src/auth/services/authService.ts`
- **AC**: Login sets token in store; logout clears state; expired token triggers refresh

### 1.5 Auth UI components
- Build `BranchSelector.tsx`: fetches branches, displays as selectable cards, stores selection
- Build `LoginForm.tsx`: email + password inputs, submit, error display, loading state
- Build `SectorGate.tsx`: checks sector assignment on mount, redirects if not assigned
- Build `useAuth.ts` hook combining store + navigation logic
- **Files**: `pwaWaiter/src/auth/components/*.tsx`, `pwaWaiter/src/auth/hooks/useAuth.ts`
- **AC**: Full login flow works: select branch → login → sector verified → redirect to app

## Phase 2: Layout & Navigation

### 2.1 App shell & header
- Build `AppShell.tsx` as main layout wrapper with header + content area
- Build `Header.tsx` with: logo, branch name, WsIndicator, pending badge, user email, logout button
- Build `WsIndicator.tsx`: green dot when connected, red dot when disconnected, tooltip with details
- **Files**: `pwaWaiter/src/layout/components/AppShell.tsx`, `pwaWaiter/src/layout/components/Header.tsx`, `pwaWaiter/src/layout/components/WsIndicator.tsx`
- **AC**: Header renders all 6 elements; WsIndicator toggles color based on realtimeStore.connected

### 2.2 Tab navigation
- Build `TabNav.tsx` with Comensales and Autogestin tabs
- Implement `useTabNavigation.ts` hook managing active tab state
- Active tab has visual indicator (underline + bold), inactive is muted
- Tab content area lazy-loads the selected view
- **Files**: `pwaWaiter/src/layout/components/TabNav.tsx`, `pwaWaiter/src/layout/hooks/useTabNavigation.ts`
- **AC**: Tabs switch without page reload; state persists within session; active tab is visually distinct

## Phase 3: Tables View

### 3.1 Tables store & service
- Create `tablesStore.ts` with: tables array, activeFilter, setFilter(), updateTable(), refreshAll()
- Create `tablesService.ts` with: fetchTables(branchId, sectorId?) API call
- Filter logic: TODAS=all, URGENTES=serviceCalls>0 OR readyItems>0, ACTIVAS=has session, LIBRES=no session, FUERA_DE_SERVICIO=disabled
- **Files**: `pwaWaiter/src/tables/store/tablesStore.ts`, `pwaWaiter/src/tables/services/tablesService.ts`
- **AC**: Store holds tables; filters produce correct subsets; updateTable merges single table update

### 3.2 Table filters component
- Build `TableFilters.tsx`: horizontal scrollable pill/chip bar with 5 filter options
- Active filter highlighted, tap to select, single-select behavior
- Show count badge per filter (e.g., "Urgentes (3)")
- **Files**: `pwaWaiter/src/tables/components/TableFilters.tsx`, `pwaWaiter/src/tables/hooks/useTableFilters.ts`
- **AC**: Tapping filter updates store; count badges are accurate; horizontal scroll on mobile

### 3.3 Sector grouping & table grid
- Build `SectorGroup.tsx`: sector name header + CSS grid of table cards
- Build `TablesView.tsx`: fetches tables on mount, groups by sectorId, renders SectorGroups
- Grid: 2 columns on mobile, 3 on tablet, 4 on desktop
- **Files**: `pwaWaiter/src/tables/components/TablesView.tsx`, `pwaWaiter/src/tables/components/SectorGroup.tsx`
- **AC**: Tables grouped under sector headers; responsive grid adapts to screen size

### 3.4 Table card with animations
- Build `TableCard.tsx`: large code text, bg color by state, order indicator icon, badges
- Build `TableBadges.tsx`: rounds count, service calls count, check requested icon
- Implement `useTableAnimation.ts`: resolves highest priority animation class per table
- Apply animation class to card root element
- **Files**: `pwaWaiter/src/tables/components/TableCard.tsx`, `pwaWaiter/src/tables/components/TableBadges.tsx`, `pwaWaiter/src/tables/hooks/useTableAnimation.ts`
- **AC**: Cards show correct bg color per state; highest priority animation plays; lower priority suppressed

### 3.5 Pull-to-refresh
- Build `PullToRefresh.tsx` wrapper component
- Implement `usePullToRefresh.ts` hook: touch start/move/end tracking, threshold 60px, spinner trigger
- On trigger: call tablesStore.refreshAll()
- Also add manual refresh button in header (calls same function)
- **Files**: `pwaWaiter/src/tables/components/PullToRefresh.tsx`, `pwaWaiter/src/shared/hooks/usePullToRefresh.ts`
- **AC**: Pull gesture shows spinner and refreshes data; manual button does the same

## Phase 4: Table Detail Modal

### 4.1 Table detail store & data loading
- Create `tableDetailStore.ts`: selectedTable, session data, rounds, open/close/refresh actions
- On open: GET /api/tables/{tableId}/detail → populate store
- **Files**: `pwaWaiter/src/table-detail/store/tableDetailStore.ts`, `pwaWaiter/src/table-detail/hooks/useTableDetail.ts`
- **AC**: Opening table detail fetches and stores full session data

### 4.2 Table detail modal UI
- Build `TableDetailModal.tsx`: modal wrapper using shared Modal component
- Build `SessionMetrics.tsx`: session duration (live timer), total items, total amount
- Build `ReadyAlert.tsx`: orange banner "X items listos para servir" when readyItemCount > 0
- Build `ServiceCallList.tsx`: list of active calls with "Reconocer" and "Cerrar" buttons
- Build `RoundList.tsx` + `RoundCard.tsx`: filterable list (all/pending/ready/delivered), items with status icons
- Build `TableActions.tsx`: "Agregar Pedido", "Cambiar Estado", "Cerrar Mesa" buttons
- **Files**: `pwaWaiter/src/table-detail/components/*.tsx`
- **AC**: Modal shows all sections; service call actions call API; round filter works; actions trigger navigation/API calls

## Phase 5: Comanda Rapida

### 5.1 Comanda store & menu service
- Create `comandaStore.ts`: selectedTableId, cart items, addItem/removeItem/updateQty/clear/submit actions
- Create `comandaService.ts`: fetchMenu(branchId), submitOrder(sessionId, items) API calls
- **Files**: `pwaWaiter/src/comanda/store/comandaStore.ts`, `pwaWaiter/src/comanda/services/comandaService.ts`
- **AC**: Cart operations work correctly; submit calls API with correct payload

### 5.2 Table picker
- Build `TablePicker.tsx`: dropdown or grid showing active tables for the waiter's sector
- Selecting a table enables the comanda interface
- Show table code + current state as visual indicator
- **Files**: `pwaWaiter/src/comanda/components/TablePicker.tsx`
- **AC**: Lists only tables with active sessions; selection stored in comandaStore

### 5.3 Menu panel
- Build `MenuPanel.tsx`: container for category tabs + product grid
- Build `CategoryTabs.tsx`: horizontal scrollable category chips
- Build `ProductCard.tsx`: compact card with name, price, thumbnail, tap-to-add
- Build `MenuSearch.tsx` + `useMenuSearch.ts`: debounced search (300ms), filters products by name
- **Files**: `pwaWaiter/src/comanda/components/MenuPanel.tsx`, `pwaWaiter/src/comanda/components/CategoryTabs.tsx`, `pwaWaiter/src/comanda/components/ProductCard.tsx`, `pwaWaiter/src/comanda/components/MenuSearch.tsx`, `pwaWaiter/src/comanda/hooks/useMenuSearch.ts`
- **AC**: Categories filter products; search debounces at 300ms; tapping product adds to cart

### 5.4 Cart panel
- Build `CartPanel.tsx`: scrollable item list + summary footer
- Build `CartItem.tsx`: product name, quantity +/- controls, subtotal, remove button
- Build `CartSummary.tsx`: total amount, notes textarea, "Enviar Pedido" button
- Responsive: side-by-side on tablet+, stacked on mobile with collapsible cart
- **Files**: `pwaWaiter/src/comanda/components/CartPanel.tsx`, `pwaWaiter/src/comanda/components/CartItem.tsx`, `pwaWaiter/src/comanda/components/CartSummary.tsx`
- **AC**: Quantity controls update total; notes field captured; submit sends order; responsive layout works

## Phase 6: Real-time Layer

### 6.1 WebSocket manager
- Build `WaiterWebSocket.ts` class: connect(url), disconnect(), onMessage callback, auto-reconnect with exponential backoff + jitter
- Max 50 reconnect attempts, backoff: min 1s, max 30s, jitter 0-500ms
- Update realtimeStore on connect/disconnect/error
- **Files**: `pwaWaiter/src/realtime/WaiterWebSocket.ts`, `pwaWaiter/src/realtime/types.ts`
- **AC**: Connects on mount; reconnects on drop; updates store status; caps at 50 attempts

### 6.2 Message router
- Build `messageRouter.ts`: parses WaiterWSMessage, dispatches to correct store
- TABLE_STATE_CHANGED → tablesStore.updateTable()
- ORDER_CREATED, ORDER_STATUS_CHANGED, ITEM_STATUS_CHANGED → tablesStore.updateTable() + tableDetailStore.refresh() if open
- SERVICE_CALL_CREATED, SERVICE_CALL_UPDATED → tablesStore.updateTable() + trigger notification
- CHECK_REQUESTED → tablesStore.updateTable()
- **Files**: `pwaWaiter/src/realtime/messageRouter.ts`
- **AC**: Each event type updates the correct store(s); unknown types logged but don't crash

### 6.3 WebSocket hook & polling fallback
- Build `useWebSocket.ts`: connects on mount, disconnects on unmount, passes messages to router
- Build `useTablePolling.ts`: polls every 60s as fallback, pauses when WebSocket connected
- Manual refresh button and pull-to-refresh both call refreshAll()
- **Files**: `pwaWaiter/src/realtime/hooks/useWebSocket.ts`, `pwaWaiter/src/tables/hooks/useTablePolling.ts`
- **AC**: WebSocket connects on app mount; polling runs every 60s when WS disconnected; manual refresh works

## Phase 7: Offline & Retry Queue

### 7.1 IndexedDB setup
- Build `db.ts` using `idb`: open database "pwaWaiter" v1, create object stores (offlineQueue, tablesCache, menuCache)
- Define indexes per store as specified in design
- **Files**: `pwaWaiter/src/offline/db.ts`
- **AC**: Database opens cleanly; object stores and indexes created

### 7.2 Offline queue manager
- Build `OfflineQueue.ts` class: enqueue(op), dequeue(), peek(), remove(id), getAll(), deduplicate(hash)
- SHA-256 hash of endpoint + JSON.stringify(payload) for dedup
- Build `queueReplay.ts`: on online event, replay FIFO, retry 3x with backoff (1s, 2s, 4s), remove on success, mark FAILED on 3rd failure
- **Files**: `pwaWaiter/src/offline/OfflineQueue.ts`, `pwaWaiter/src/offline/services/queueReplay.ts`
- **AC**: Operations enqueue with dedup; replay processes FIFO; retries 3x; failed ops marked

### 7.3 Offline detection & UI
- Build `useOfflineStatus.ts`: listens to online/offline events + fetch failure detection, updates offlineStore
- Build `OfflineBanner.tsx`: fixed bottom banner showing "Sin conexin - N operaciones pendientes"
- Integrate with API client: on fetch failure when offline, enqueue operation
- **Files**: `pwaWaiter/src/offline/hooks/useOfflineStatus.ts`, `pwaWaiter/src/offline/components/OfflineBanner.tsx`
- **AC**: Banner appears when offline; shows queue count; disappears when online; operations auto-replay

## Phase 8: Notifications & PWA

### 8.1 Notification system
- Build `NotificationManager.ts`: requestPermission(), show(title, body, tag, sound)
- Build `sounds.ts`: preload audio files, play(soundName) function
- Build `useNotifications.ts`: binds to realtime events, triggers notifications for Priority 1-2 events
- Group notifications by tag (e.g., "service-call-{tableId}") to avoid flooding
- **Files**: `pwaWaiter/src/notifications/NotificationManager.ts`, `pwaWaiter/src/notifications/sounds.ts`, `pwaWaiter/src/notifications/hooks/useNotifications.ts`
- **AC**: Permission requested on first event; notifications fire with sound; grouped by tag; works when app backgrounded

### 8.2 PWA manifest & service worker
- Create `manifest.json` with: name "Buen Sabor - Mozo", icons, start_url "/", display "standalone", shortcuts for Mesas and Comanda
- Configure Vite PWA plugin for service worker generation
- Build install prompt handler for `beforeinstallprompt` event
- Add asset caching strategy (CacheFirst for static, NetworkFirst for API)
- **Files**: `pwaWaiter/public/manifest.json`, `pwaWaiter/public/icons/*`, `pwaWaiter/src/sw.ts`, `pwaWaiter/vite.config.ts`
- **AC**: Lighthouse PWA audit passes; install prompt works; app works offline with cached assets; shortcuts appear

## Phase 9: Integration & Polish

### 9.1 End-to-end flow testing
- Verify: login → tables view → tap table → detail modal → comanda → order submit → real-time update
- Verify: offline mode → queue operations → reconnect → replay → sync
- Verify: all 5 animation priorities resolve correctly under concurrent events
- **AC**: Full happy path works; offline resilience verified; animations don't stack

### 9.2 Responsive & touch optimization
- Verify all touch targets >= 44x44px
- Test on mobile viewport (375px), tablet (768px), desktop (1024px+)
- Ensure pull-to-refresh doesn't conflict with native browser pull-to-refresh
- **AC**: Usable on all viewport sizes; no accidental taps; smooth gestures
