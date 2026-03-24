---
sprint: 9
artifact: design
status: complete
---

# Design: pwaWaiter Completo

## Architecture Decisions

### AD-1: React 19 + Vite + TypeScript Strict
- **Decision**: Use React 19 with Vite bundler, TypeScript in strict mode
- **Rationale**: React 19 concurrent features enable smooth animations + transitions. Vite provides fast HMR for development. TypeScript strict catches type errors early.
- **Tradeoff**: React 19 is newer — fewer community examples, but stable for production

### AD-2: Zustand over Redux
- **Decision**: Zustand for state management
- **Rationale**: Lighter bundle, simpler API, no boilerplate, built-in devtools, works with React 19 concurrent mode via `useSyncExternalStore`
- **Tradeoff**: Less structured than Redux — team must follow store-per-domain convention

### AD-3: CSS Animations over JS Intervals
- **Decision**: All priority animations via CSS `@keyframes` + dynamic class toggling
- **Rationale**: CSS animations run on compositor thread, don't block main thread, perform well on low-end mobile devices
- **Tradeoff**: Less programmatic control — priority logic lives in a React hook that manages class names

### AD-4: IndexedDB via idb Wrapper
- **Decision**: Use `idb` (Jake Archibald's wrapper) for IndexedDB operations
- **Rationale**: Promise-based API, tiny bundle (1.2KB), handles versioning and migrations
- **Tradeoff**: Extra dependency, but justified by DX improvement

### AD-5: Single WebSocket with Store Dispatch
- **Decision**: One WebSocket connection per session, messages dispatched to Zustand stores
- **Rationale**: Avoid multiple connections. Central message router parses event type and updates relevant store slice
- **Tradeoff**: Single point of failure — mitigated by polling fallback

## File Structure

```
pwaWaiter/
├── public/
│   ├── manifest.json
│   ├── icons/
│   │   ├── icon-192x192.png
│   │   └── icon-512x512.png
│   └── sounds/
│       ├── notification.mp3
│       └── urgent.mp3
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── vite-env.d.ts
│   ├── index.css                          # Tailwind imports + animations
│   ├── sw.ts                              # Service worker
│   ├── auth/
│   │   ├── components/
│   │   │   ├── BranchSelector.tsx         # Pre-login branch picker
│   │   │   ├── LoginForm.tsx              # Email + password form
│   │   │   └── SectorGate.tsx             # Sector assignment check
│   │   ├── store/
│   │   │   └── authStore.ts               # Auth state + actions
│   │   ├── hooks/
│   │   │   └── useAuth.ts                 # Auth convenience hook
│   │   └── services/
│   │       └── authService.ts             # API calls
│   ├── layout/
│   │   ├── components/
│   │   │   ├── AppShell.tsx               # Main layout wrapper
│   │   │   ├── Header.tsx                 # Top bar with all indicators
│   │   │   ├── TabNav.tsx                 # Comensales / Autogestin tabs
│   │   │   └── WsIndicator.tsx            # Green/red connection dot
│   │   └── hooks/
│   │       └── useTabNavigation.ts
│   ├── tables/
│   │   ├── components/
│   │   │   ├── TablesView.tsx             # Main tables container
│   │   │   ├── TableFilters.tsx           # Filter bar (Todas/Urgentes/...)
│   │   │   ├── SectorGroup.tsx            # Sector header + table grid
│   │   │   ├── TableCard.tsx              # Individual table card
│   │   │   ├── TableBadges.tsx            # Rounds/calls/check badges
│   │   │   └── PullToRefresh.tsx          # Pull-to-refresh wrapper
│   │   ├── store/
│   │   │   └── tablesStore.ts             # Tables state + filters
│   │   ├── hooks/
│   │   │   ├── useTableFilters.ts         # Filter logic
│   │   │   ├── useTableAnimation.ts       # Priority animation resolver
│   │   │   └── useTablePolling.ts         # 60s fallback polling
│   │   └── services/
│   │       └── tablesService.ts           # API calls
│   ├── table-detail/
│   │   ├── components/
│   │   │   ├── TableDetailModal.tsx        # Full detail modal
│   │   │   ├── SessionMetrics.tsx          # Duration, items, amount
│   │   │   ├── ServiceCallList.tsx         # Calls with ack/close
│   │   │   ├── ReadyAlert.tsx             # Items ready banner
│   │   │   ├── RoundList.tsx              # Filterable round list
│   │   │   ├── RoundCard.tsx              # Single round with items
│   │   │   └── TableActions.tsx           # Action buttons
│   │   ├── store/
│   │   │   └── tableDetailStore.ts
│   │   └── hooks/
│   │       └── useTableDetail.ts
│   ├── comanda/
│   │   ├── components/
│   │   │   ├── ComandaView.tsx            # Main comanda container
│   │   │   ├── TablePicker.tsx            # Target table selector
│   │   │   ├── MenuPanel.tsx              # Left: categories + products
│   │   │   ├── CategoryTabs.tsx           # Category navigation
│   │   │   ├── ProductCard.tsx            # Compact product card
│   │   │   ├── MenuSearch.tsx             # Debounced search bar
│   │   │   ├── CartPanel.tsx              # Right: cart items + total
│   │   │   ├── CartItem.tsx               # Item with qty controls
│   │   │   └── CartSummary.tsx            # Total + notes + submit
│   │   ├── store/
│   │   │   └── comandaStore.ts            # Cart state + actions
│   │   ├── hooks/
│   │   │   ├── useMenuSearch.ts           # Debounced search
│   │   │   └── useCart.ts                 # Cart operations
│   │   └── services/
│   │       └── comandaService.ts          # Order submission API
│   ├── realtime/
│   │   ├── WaiterWebSocket.ts             # WebSocket manager class
│   │   ├── messageRouter.ts               # Route messages to stores
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts            # Connection lifecycle hook
│   │   └── types.ts                       # WS message types
│   ├── offline/
│   │   ├── db.ts                          # IndexedDB setup (idb)
│   │   ├── OfflineQueue.ts               # Queue manager class
│   │   ├── hooks/
│   │   │   └── useOfflineStatus.ts        # Online/offline detection
│   │   ├── components/
│   │   │   └── OfflineBanner.tsx          # "Sin conexin" banner
│   │   └── services/
│   │       └── queueReplay.ts             # Replay logic with retries
│   ├── notifications/
│   │   ├── NotificationManager.ts         # Permission + dispatch
│   │   ├── sounds.ts                      # Audio playback
│   │   └── hooks/
│   │       └── useNotifications.ts        # Permission + event binding
│   └── shared/
│       ├── components/
│       │   ├── Button.tsx
│       │   ├── Modal.tsx                  # Reusable modal with ESC/backdrop
│       │   ├── Badge.tsx
│       │   ├── Toast.tsx
│       │   ├── Spinner.tsx
│       │   └── ErrorBoundary.tsx
│       ├── hooks/
│       │   ├── usePullToRefresh.ts
│       │   └── useDebounce.ts
│       ├── api/
│       │   ├── client.ts                  # Fetch wrapper with auth
│       │   └── interceptors.ts            # Token refresh, offline detect
│       └── types/
│           └── index.ts                   # Shared TypeScript types
├── tailwind.config.ts
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── package.json
└── index.html
```

## Component Tree

```
<App>
  ├── <ErrorBoundary>
  │   ├── [unauthenticated]
  │   │   ├── <BranchSelector />
  │   │   └── <LoginForm />
  │   ├── [sector check]
  │   │   └── <SectorGate />
  │   └── [authenticated]
  │       └── <AppShell>
  │           ├── <Header>
  │           │   ├── <Logo />
  │           │   ├── <BranchName />
  │           │   ├── <WsIndicator />
  │           │   ├── <PendingBadge />
  │           │   ├── <UserEmail />
  │           │   └── <LogoutButton />
  │           ├── <TabNav tabs={["Comensales","Autogestin"]} />
  │           ├── [tab=Comensales]
  │           │   └── <TablesView>
  │           │       ├── <PullToRefresh>
  │           │       │   ├── <TableFilters />
  │           │       │   └── <SectorGroup> (per sector)
  │           │       │       └── <TableCard> (per table)
  │           │       │           └── <TableBadges />
  │           │       └── <TableDetailModal> (conditional)
  │           │           ├── <SessionMetrics />
  │           │           ├── <ReadyAlert />
  │           │           ├── <ServiceCallList />
  │           │           ├── <RoundList>
  │           │           │   └── <RoundCard> (per round)
  │           │           └── <TableActions />
  │           └── [tab=Autogestin]
  │               └── <ComandaView>
  │                   ├── <TablePicker />
  │                   ├── <MenuPanel>
  │                   │   ├── <MenuSearch />
  │                   │   ├── <CategoryTabs />
  │                   │   └── <ProductCard> (per product)
  │                   └── <CartPanel>
  │                       ├── <CartItem> (per item)
  │                       └── <CartSummary />
  └── <OfflineBanner /> (global overlay)
  └── <Toast /> (global)
```

## DB Schema (IndexedDB)

```
Database: pwaWaiter
Version: 1

Object Store: offlineQueue
  keyPath: id
  Indexes:
    - timestamp (for FIFO ordering)
    - status (for filtering QUEUED items)
    - payloadHash (for deduplication)

Object Store: tablesCache
  keyPath: id
  Indexes:
    - branchId
    - sectorId
    - state

Object Store: menuCache
  keyPath: id
  Indexes:
    - categoryId
    - name (for search)
```

## Sequence Diagrams

### Login Flow
```
Waiter          BranchSelector    LoginForm       SectorGate       API            AuthStore
  |                  |                |               |               |               |
  |--select branch-->|                |               |               |               |
  |                  |--setBranch---->|               |               |               |
  |                  |                |               |               |            setBranch
  |                  |                |               |               |               |
  |                  |  email+pass--->|               |               |               |
  |                  |                |--POST /auth/login------------>|               |
  |                  |                |<--200 {token, user}-----------|               |
  |                  |                |--setAuth----->|               |            setAuth
  |                  |                |               |               |               |
  |                  |                |               |--GET /branches/{id}/staff/me->|
  |                  |                |               |<--200 {sector}----------------|
  |                  |                |               |--setSector--->|            setSector
  |                  |                |               |               |               |
  |<-----------redirect to AppShell--|               |               |               |
```

### WebSocket Message Flow
```
Server          WaiterWebSocket    messageRouter    tablesStore    tableCard    animationHook
  |                  |                  |               |              |              |
  |--WS message----->|                  |               |              |              |
  |                  |--parse+validate->|               |              |              |
  |                  |                  |--dispatch---->|              |              |
  |                  |                  |  (by type)    |--setState--->|              |
  |                  |                  |               |              |--resolve---->|
  |                  |                  |               |              |  priority    |
  |                  |                  |               |              |<--cssClass---|
  |                  |                  |               |              |--re-render-->|
```

### Offline Queue Replay
```
Browser         OfflineQueue     queueReplay      API           tablesStore
  |                  |                |               |               |
  |--online event--->|                |               |               |
  |                  |--getQueued---->|               |               |
  |                  |  (FIFO order)  |               |               |
  |                  |                |--POST op[0]-->|               |
  |                  |                |<--200---------|               |
  |                  |                |--remove(id)-->|               |
  |                  |                |--POST op[1]-->|               |
  |                  |                |<--500---------|               |
  |                  |                |--retry+1----->|               |
  |                  |                |  (wait 2s)    |               |
  |                  |                |--POST op[1]-->|               |
  |                  |                |<--200---------|               |
  |                  |                |--remove(id)-->|               |
  |                  |                |            refresh tables---->|
```

## Animation System Design

### CSS Keyframes
```css
/* Priority 1: Red blink - Service call */
@keyframes blink-red {
  0%, 100% { background-color: var(--table-bg); }
  50% { background-color: rgb(239 68 68 / 0.6); }
}

/* Priority 2: Orange blink - Items ready + kitchen */
@keyframes blink-orange {
  0%, 100% { background-color: var(--table-bg); }
  50% { background-color: rgb(249 115 22 / 0.6); }
}

/* Priority 3: Blue blink - State change (temporary) */
@keyframes blink-blue {
  0%, 100% { background-color: var(--table-bg); }
  50% { background-color: rgb(59 130 246 / 0.5); }
}

/* Priority 4: Yellow pulse - New order */
@keyframes pulse-yellow {
  0%, 100% { box-shadow: 0 0 0 0 rgb(234 179 8 / 0.4); }
  50% { box-shadow: 0 0 0 8px rgb(234 179 8 / 0); }
}

/* Priority 5: Purple pulse - Check requested */
@keyframes pulse-purple {
  0%, 100% { box-shadow: 0 0 0 0 rgb(168 85 247 / 0.4); }
  50% { box-shadow: 0 0 0 8px rgb(168 85 247 / 0); }
}
```

### Priority Resolution Hook
```typescript
// useTableAnimation.ts — resolves highest priority animation class
function useTableAnimation(table: WaiterTableView): string {
  const [tempAnimations, setTempAnimations] = useState<Map<string, number>>();

  // Priority 1: Active service call
  if (table.activeServiceCallCount > 0) return 'animate-blink-red';
  // Priority 2: Items ready + items still cooking
  if (table.readyItemCount > 0 && table.pendingItemCount > 0) return 'animate-blink-orange';
  // Priority 3: Recent state change (auto-expires via setTimeout)
  if (tempAnimations?.has(table.id)) return 'animate-blink-blue';
  // Priority 4: New order
  if (table.state === 'CON_PEDIDO') return 'animate-pulse-yellow';
  // Priority 5: Check requested
  if (table.checkRequested) return 'animate-pulse-purple';

  return '';
}
```

## Zustand Store Architecture

```
stores/
├── authStore.ts        → { user, token, branch, sector, login(), logout(), refreshToken() }
├── tablesStore.ts      → { tables[], filter, setFilter(), updateTable(), refreshAll() }
├── tableDetailStore.ts → { selectedTable, session, rounds, open(), close(), refresh() }
├── comandaStore.ts     → { selectedTable, cart[], addItem(), removeItem(), updateQty(), submit(), clear() }
├── realtimeStore.ts    → { connected, lastMessage, reconnectAttempts }
└── offlineStore.ts     → { isOnline, queueCount, queue[] }
```

Each store is independent. The `messageRouter` in the realtime module dispatches to the appropriate store based on WebSocket event type.
