---
sprint: 9
artifact: proposal
status: complete
---

# Proposal: pwaWaiter Completo

## Intent

Deliver a fully functional Progressive Web App for restaurant waiters (mozos) that enables real-time table management, quick order entry, offline operation, and instant notifications — replacing paper-based workflows entirely.

## Scope

### In Scope
- Complete pwaWaiter application: React 19 + Vite + TypeScript + Zustand + TailwindCSS
- Authentication flow with branch pre-selection, login, and sector assignment verification
- Real-time table monitoring with WebSocket primary + polling fallback
- Quick order entry (comanda rapida) with split-panel interface
- 5-level priority animation system for visual alerts
- Offline operation with IndexedDB cache and retry queue
- Browser notifications with sound alerts
- PWA manifest with app shortcuts
- Pull-to-refresh and manual sync capabilities

### Out of Scope
- Payment processing (Sprint 11)
- Service call handling (Sprint 10)
- Backend API changes (assumes existing endpoints from Sprints 1-8)
- Analytics/reporting views
- Multi-language support (Sprint 15)

## Modules

| Module | Description |
|--------|-------------|
| `auth` | Branch selection, login, sector verification |
| `layout` | Header, tab navigation, responsive shell |
| `tables` | Table grid, filters, grouping, card rendering |
| `table-detail` | Modal with metrics, round management, actions |
| `comanda` | Quick order interface with menu + cart |
| `realtime` | WebSocket manager, polling fallback, sync |
| `offline` | IndexedDB cache, retry queue, deduplication |
| `notifications` | Browser notifications, sound system |
| `animations` | Priority-based animation engine (5 levels) |
| `pwa` | Service worker, manifest, shortcuts |

## Approach

1. **Scaffold** the Vite + React 19 project with TypeScript strict mode, TailwindCSS, and Zustand stores
2. **Auth flow** first — branch selection screen → login → sector verification gate
3. **Layout shell** with header (logo, branch, WebSocket indicator, pending counter, user menu) and tab navigation
4. **Tables view** with filter bar, sector grouping, and animated table cards
5. **Table detail modal** with full round/order management
6. **Comanda rapida** as second tab with split-panel (compact menu left / cart right)
7. **Real-time layer** — WebSocket primary with 60s polling fallback and manual refresh
8. **Offline layer** — IndexedDB caching, operation queue with 3x retry and deduplication
9. **Notifications** — browser permission flow, sound alerts, notification grouping
10. **PWA finalization** — manifest, icons, shortcuts, install prompt

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| WebSocket connection instability on mobile networks | High — stale data shown to waiter | Exponential backoff reconnection + 60s polling fallback + visual indicator |
| IndexedDB storage limits on older devices | Medium — offline queue overflow | Cap queue at 100 operations, FIFO eviction, warn user |
| Browser notification permission denied | Medium — missed alerts | Fallback to in-app visual + sound alerts, explain value proposition on permission request |
| React 19 concurrent features causing render tearing with animations | Medium — visual glitches | Use `useSyncExternalStore` for animation state, test on low-end devices |
| Large menu catalog slowing comanda search | Low — UX friction | Virtual scrolling, debounced search, category pre-filtering |

## Rollback

- pwaWaiter is a standalone PWA — rollback is simply not deploying or reverting the Docker image
- No backend changes required, so no database migrations to reverse
- If critical bugs found post-deploy, revert to previous container tag
- Feature flags per branch can disable the app while keeping the deployment
