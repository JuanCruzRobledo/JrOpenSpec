---
sprint: 6
artifact: proposal
status: complete
---

# SDD Proposal — Sprint 6: pwaMenu Base — Ingreso y Navegacion

## Status: APPROVED

## Executive Summary

Sprint 6 delivers the customer-facing Progressive Web App ("pwaMenu") for "Buen Sabor". Customers scan a QR code at their table, enter a lightweight session (name + avatar color, no auth required), browse the restaurant's menu organized by 3-level hierarchy (category -> subcategory -> product), filter by allergens (3 severity modes), dietary preferences, and cooking methods, and search with debounced text input. The app is fully installable as a PWA with offline fallback, uses aggressive caching strategies (CacheFirst for images, NetworkFirst for APIs), and supports i18n in 3 languages (es/en/pt) with automatic browser detection.

## 1. Intent

Build the foundational customer experience layer:
- **QR -> Session**: Zero-friction entry. No account creation, no passwords. Just scan, optionally enter a name, pick a color, and you're in.
- **Menu Browsing**: Fast, visual, mobile-first menu with horizontal category scrolling, product grid with images/badges, and modal product detail with allergen information.
- **Smart Filtering**: Allergen filtering with 3 strictness modes (standard, strict, very strict) that respects cross-reactions. Dietary and cooking method filters.
- **PWA**: Installable, offline-capable, fast first paint. Workbox strategies optimized for a restaurant context (images cached aggressively, API data fresh but with fallback).
- **i18n**: Spanish-first with English and Portuguese support. Auto-detection + manual override.

## 2. Scope

### In Scope
- Project scaffolding: React 19.2 + Vite 7.2 + TypeScript 5.9 + Zustand 5 + TailwindCSS 4 + i18next
- React Compiler via babel-plugin-react-compiler
- QR landing page with session join flow (POST /api/sessions/join)
- HMAC session token (3h expiry, 8h localStorage TTL from last activity)
- Menu navigation: 3-level hierarchy with horizontal category scroll
- Product grid (image, name, price, badges) + product detail modal
- Allergen display with traffic-light colors (red/yellow/green) + cross-reactions
- Search with 300ms debounce
- Allergen filtering: 3 modes (off / strict / very strict)
- Dietary preference filtering
- Cooking method filtering
- PWA: manifest.json, Workbox service worker, install prompt
- Cache: CacheFirst 30d for images, NetworkFirst 5s for APIs, SPA offline fallback
- Menu data cache: 5min TTL with background refresh
- i18n: es (complete), en, pt -- auto-detection + manual flag selector
- Bottom bar with placeholder buttons (call waiter, history, bill)
- Accessibility: semantic HTML, ARIA labels, 44x44px touch targets

### Out of Scope (Future Sprints)
- Cart / ordering flow
- Payment integration
- Call waiter functionality (placeholder only)
- Order history (placeholder only)
- Bill viewing (placeholder only)
- Push notifications
- Waiter PWA (pwaWaiter)
- WebSocket real-time updates

## 3. Dependencies

### Backend (from Sprint 4)
- `GET /api/public/menu/{slug}` -- Full menu with categories, products, allergens, dietary, badges
- `GET /api/public/menu/{slug}/product/{id}` -- Product detail with cross-reactions, ingredients
- `GET /api/public/allergens?tenant={slug}` -- Allergen catalog with cross-reactions
- `GET /api/public/branches?tenant={slug}` -- Branch listing

### New Backend Endpoint (Sprint 6)
- `POST /api/sessions/join` -- Create anonymous customer session (new endpoint)

### Infrastructure (from Sprint 1)
- PostgreSQL 16, Redis 7, Docker Compose
- Backend cache layer (5min TTL on public endpoints)

## 4. Technical Approach

### 4.1 Session Model
Anonymous sessions using HMAC tokens. No JWT, no user accounts. The token encodes: branch_id, table_id, session_id, created_at. Signed with HMAC-SHA256 server-side secret. 3-hour server expiry. Client stores in localStorage with 8-hour sliding window (reset on any activity).

### 4.2 Menu Data Strategy
- First load: fetch full menu from `/api/public/menu/{slug}`, store in Zustand + localStorage
- Cache TTL: 5 minutes. After TTL, background fetch (stale-while-revalidate pattern)
- Filtering happens client-side on cached menu data (no server roundtrip for filter changes)
- Product detail modal fetches from `/api/public/menu/{slug}/product/{id}` (cross-reactions + ingredients not in list response)

### 4.3 Allergen Filtering Algorithm
Three modes:
1. **Off**: No filtering, all products shown. Allergen badges still visible.
2. **Strict**: Hides products where presence_type = "contains" for selected allergens.
3. **Very Strict**: Hides products where presence_type = "contains" OR "may_contain" for selected allergens. Also checks cross-reactions (cached 5min).

### 4.4 PWA Strategy
- `vite-plugin-pwa` with Workbox
- CacheFirst for images (CDN patterns, 30d max-age)
- NetworkFirst with 5s timeout for API calls (falls back to cached response)
- Precache the app shell (HTML, JS, CSS)
- Offline fallback page: "Estas sin conexion. Podes ver el menu guardado."
- Install prompt: custom banner after 30s on page (not the browser default)

### 4.5 i18n Strategy
- i18next with react-i18next
- Namespace-based lazy loading: `common`, `menu`, `session`, `filters`, `allergens`
- Detection order: localStorage -> navigator.language -> fallback "es"
- Manual override via flag selector in header (AR, US, BR)
- Spanish is complete, English and Portuguese translations

## 5. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large menu payloads on slow 4G | Slow first load | Compress response (gzip), paginate if >200 products, lazy load images |
| Service worker caching stale menu | Customer sees old prices | 5min cache + background refresh + version header check |
| Cross-reaction data growing | Complex filter computation | Cache allergen catalog 5min, compute filter client-side with memoization |
| QR code leading to wrong branch | Session mismatch | Validate branch slug in QR URL, show branch name prominently on landing |
| i18n missing keys | Broken UI in en/pt | Fallback chain: requested -> es -> key name. CI check for missing keys |

## 6. Estimates

| Phase | Effort |
|-------|--------|
| Scaffolding + PWA + i18n setup | 1 session |
| Session flow (QR -> join -> token) | 1 session |
| Menu navigation + product grid | 1-2 sessions |
| Product detail modal | 1 session |
| Search + all filters | 1-2 sessions |
| Bottom bar + accessibility pass | 1 session |
| **Total** | **6-8 sessions** |

## Next Recommended
-> `sdd-spec` (Requirements RFC 2119, API contracts, scenarios)
