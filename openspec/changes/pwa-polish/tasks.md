---
sprint: 15
artifact: tasks
status: complete
---

# Tasks: PWA Polish, Accesibilidad e i18n

## Phase 1: Workbox Caching

### 1.1 pwaMenu Workbox configuration
- Install `vite-plugin-pwa` and configure in `vite.config.ts`
- Set up runtime caching: CacheFirst 30d images (200 entries), NetworkFirst 5s APIs, CacheFirst 1y fonts
- Precache app shell (HTML, CSS, JS bundles)
- Set `registerType: 'prompt'` for user-controlled updates
- **Files**: `pwaMenu/vite.config.ts`, `pwaMenu/src/sw-custom.ts`
- **AC**: Lighthouse PWA audit passes; images served from cache on repeat visits; API falls back to cache after 5s timeout

### 1.2 pwaWaiter Workbox configuration
- Configure Workbox: CacheFirst 7d images (100 entries), NetworkFirst tables (1h fallback), CacheFirst 1y fonts
- Set `registerType: 'autoUpdate'` for automatic updates (critical for waiter)
- Cache table data API specifically: `/api/branches/*/tables`
- **Files**: `pwaWaiter/vite.config.ts`, `pwaWaiter/src/sw-custom.ts`
- **AC**: Table data available from cache when offline; images cached for 7d; auto-update works

### 1.3 Dashboard Workbox configuration
- Configure Workbox: NetworkFirst for all API requests, CacheFirst for static assets
- No aggressive caching — Dashboard should always show fresh data
- **Files**: `dashboard/vite.config.ts`
- **AC**: Dashboard always fetches fresh data; static assets cached for performance

## Phase 2: Advanced Offline — pwaMenu

### 2.1 IndexedDB menu cache
- Implement `MenuCache` class: save full menu (categories + products) to IndexedDB on first load
- On subsequent loads: serve from IDB if network unavailable
- Update IDB when fresh data fetched from network
- **Files**: `pwaMenu/src/offline/MenuCache.ts`
- **AC**: Menu available offline from IDB; IDB updated on fresh fetch; categories and products both cached

### 2.2 Offline cart & queue integration
- Implement `OfflineCart`: all cart operations work without network (add, remove, update, clear)
- Integrate with existing OfflineQueue: queue order submission when offline
- Show queued status in UI: "Pedido en cola - Se enviar al recuperar conexin"
- **Files**: `pwaMenu/src/offline/OfflineCart.ts`, updates to cart store and order submission
- **AC**: Cart fully functional offline; order queued with feedback; replay on reconnection

### 2.3 Update checker & banner
- Implement `UpdateChecker`: HEAD request to menu endpoint every hour
- Compare ETag with cached version
- If different: show `UpdateBanner.tsx` with "Actualizar" button
- On refresh: fetch fresh menu, update IDB, dismiss banner
- **Files**: `pwaMenu/src/offline/UpdateChecker.ts`, `pwaMenu/src/offline/components/UpdateBanner.tsx`
- **AC**: Check fires every hour; banner appears on stale menu; refresh updates cache; non-blocking

## Phase 3: Accessibility — All PWAs

### 3.1 Shared accessibility components
- Build `SkipToContent.tsx`: hidden link, visible on focus, jumps to `<main id="main-content">`
- Build `FocusTrap.tsx` + `useFocusTrap.ts`: traps focus within container, wraps on Tab/Shift-Tab, restores focus on unmount
- Build `AriaLive.tsx` + `useAnnounce.ts`: hidden live regions for screen reader announcements
- Build `useKeyboardNavigation.ts`: ESC handler for topmost modal
- **Files**: `shared/accessibility/*.tsx`, `shared/accessibility/hooks/*.ts`
- **AC**: Skip link visible on Tab; focus trapped in modals; ESC closes topmost; announcements reach screen readers

### 3.2 pwaMenu accessibility remediation
- Add `SkipToContent` to app root
- Add ARIA roles to all landmarks: `nav`, `main`, `complementary` (cart)
- Add `FocusTrap` to all modals (product detail, order confirmation, etc.)
- Verify all touch targets >= 44x44px (add padding where needed)
- Add `alt` text to all product images; decorative images get `alt=""`
- Associate form labels with inputs; add `aria-describedby` for errors
- **Files**: Multiple pwaMenu component files
- **AC**: axe-core audit passes with 0 violations; keyboard navigation complete; touch targets measured

### 3.3 pwaWaiter accessibility remediation
- Same checklist as pwaMenu: skip link, ARIA landmarks, focus traps, touch targets, alt text, form labels
- Ensure table cards are keyboard-navigable (arrow keys for grid navigation, Enter to open detail)
- Ensure animation classes don't interfere with screen readers
- **Files**: Multiple pwaWaiter component files
- **AC**: axe-core audit passes; table grid navigable by keyboard; animations don't confuse screen readers

### 3.4 Dashboard accessibility remediation
- Add skip link, ARIA landmarks, focus traps on all modals
- Verify contrast ratios on all color-coded elements (status badges, chart colors)
- Ensure all data tables have proper `<thead>`, `<th scope>`, and caption
- Ensure form inputs in all CRUD forms have visible labels
- **Files**: Multiple Dashboard component files
- **AC**: axe-core audit passes; tables accessible; forms properly labeled; contrast verified

### 3.5 Typography & zoom audit
- Convert all font-size declarations to rem (base 16px)
- Test all 3 PWAs at 200% browser zoom — no horizontal scrolling
- Ensure line heights are at least 1.5x font size for body text
- **Files**: CSS files across all 3 PWAs
- **AC**: All sizes in rem; 200% zoom produces no horizontal scroll; readable line heights

## Phase 4: i18n — pwaMenu

### 4.1 i18next setup & string extraction
- Install `i18next`, `react-i18next`, `i18next-browser-languagedetector`
- Initialize with Spanish (es-AR) as default, fallback to es-AR
- Extract ALL user-facing strings from pwaMenu components into `locales/es-AR.json`
- Use dot notation keys: `menu.title`, `cart.submit`, `order.success`, etc.
- **Files**: `pwaMenu/src/i18n/index.ts`, `pwaMenu/src/i18n/locales/es-AR.json`
- **AC**: All visible strings come from translation file; no hardcoded strings in JSX; t() works throughout

### 4.2 Replace hardcoded strings
- Replace every hardcoded string in pwaMenu components with `t('key')` calls
- Handle pluralization: `t('cart.items', { count })`
- Handle interpolation: `t('order.round', { number })`
- **Files**: All pwaMenu component files with user-facing text
- **AC**: Changing es-AR.json updates the UI; no hardcoded Spanish strings remain; pluralization works

### 4.3 Locale-aware formatting
- Implement `formatCurrency(amount, locale)`: uses `Intl.NumberFormat` for ARS
- Implement `formatDate(date, locale)`: uses `Intl.DateTimeFormat`
- Replace all raw number/date displays with formatted versions
- **Files**: `pwaMenu/src/i18n/utils/formatCurrency.ts`, `pwaMenu/src/i18n/utils/formatDate.ts`
- **AC**: Currency shows "$15.400,00" for es-AR; dates show "19 de marzo de 2026"; formatting adapts to locale

## Phase 5: Import/Export — Dashboard

### 5.1 Export endpoint & UI
- Implement POST /api/branches/{branchId}/export: serialize restaurant + categories + products to JSON with version and timestamp
- Build `ExportButton.tsx`: triggers download of JSON file
- **Files**: `app/routers/import_export.py`, `app/services/export_service.py`, `dashboard/src/import-export/components/ExportButton.tsx`
- **AC**: JSON file downloads with correct schema; includes all categories and products; version field present

### 5.2 Import endpoint & UI
- Implement POST /api/branches/{branchId}/import: validate JSON (Zod on frontend, Pydantic on backend), preview mode, apply mode with backup + atomic transaction
- Build `ImportUpload.tsx`: file input (max 5MB), upload on select
- Build `ImportPreview.tsx`: show entity counts + warnings
- Build `ImportConfirm.tsx`: confirmation dialog with warning
- Build `exportSchema.ts`: Zod schema for client-side validation
- **Files**: `app/routers/import_export.py`, `app/services/import_service.py`, `dashboard/src/import-export/components/*.tsx`, `dashboard/src/import-export/schemas/exportSchema.ts`
- **AC**: Preview shows accurate counts; import is atomic; backup created; caches cleaned; 5MB limit enforced; invalid JSON rejected

## Phase 6: Help System, Toasts & Animations

### 6.1 Contextual help system
- Build `HelpButton.tsx`: (?) icon button per screen, positioned top-right
- Build `HelpPanel.tsx`: slide-out panel with title, description, actions, tips
- Create help JSON files for all Dashboard screens (products, categories, statistics, orders, promotions, recipes, ingredients, audit)
- Implement `useHelp.ts`: lazy-load help content on demand
- **Files**: `dashboard/src/help/components/*.tsx`, `dashboard/src/help/content/*.json`, `dashboard/src/help/hooks/useHelp.ts`
- **AC**: (?) button on every Dashboard screen; panel loads correct content; dismissible via X/ESC/backdrop

### 6.2 Toast system refinement
- Build `ToastContainer.tsx`: max 5 visible, stacks bottom-right (desktop), bottom-center (mobile)
- Build `Toast.tsx`: icon (success/error/warning/info), message, optional action, close button
- Build `toastStore.ts`: queue management, urgent flag for persistence, 5s auto-close for normal
- Add `aria-live="polite"` for normal toasts, `aria-live="assertive"` for urgent
- Apply across all 3 PWAs (shared component)
- **Files**: `shared/toasts/ToastContainer.tsx`, `shared/toasts/Toast.tsx`, `shared/toasts/toastStore.ts`
- **AC**: Max 5 visible; oldest dismissed on overflow; urgent persists; 5s auto-close; screen reader announces

### 6.3 Production animations
- Create `animations.css`: modal fade+scale (200ms), button press feedback (200ms), CSS spinner, order success celebration
- Create `reduced-motion.css`: `@media (prefers-reduced-motion: reduce)` overrides all animations to instant
- Use `will-change: transform, opacity` hints; only animate transforms and opacity (GPU composited)
- **Files**: `shared/animations/animations.css`, `shared/animations/reduced-motion.css`
- **AC**: Modal animates on open/close; button feedback on click; spinner visible on loading; celebration on order success; all disabled with prefers-reduced-motion
