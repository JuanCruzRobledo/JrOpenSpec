---
sprint: 6
artifact: tasks
status: complete
---

# SDD Tasks — Sprint 6: pwaMenu Base — Ingreso y Navegacion

## Status: APPROVED

---

## Phase 1: Project Scaffolding & Configuration

### Task 1.1: Initialize Vite + React 19 Project
**Files**: `pwa_menu/package.json`, `pwa_menu/tsconfig.json`, `pwa_menu/tsconfig.app.json`, `pwa_menu/tsconfig.node.json`, `pwa_menu/index.html`, `pwa_menu/.env.example`, `pwa_menu/.env`
**Acceptance Criteria**:
- Dependencies: react@19.2, react-dom@19.2, react-router-dom@7, zustand@5, i18next, react-i18next, axios, clsx, tailwind-merge, etc.
- `pnpm install` and `pnpm dev` succeed
- TypeScript strict mode, path alias `@/` -> `src/`

### Task 1.2: Vite Configuration (React Compiler + PWA)
**Files**: `pwa_menu/vite.config.ts`
**Acceptance Criteria**:
- babel-plugin-react-compiler active
- vite-plugin-pwa with manifest, workbox runtime caching (images CacheFirst 30d, API NetworkFirst 5s, fonts StaleWhileRevalidate 1y)
- registerType: 'prompt'

### Task 1.3: TailwindCSS 4 Theme Setup
**Files**: `pwa_menu/src/index.css`
**Acceptance Criteria**:
- @theme with all dark+orange color tokens, allergen traffic-light colors, Inter font
- prefers-reduced-motion support

### Task 1.4: Shared Utilities
**Files**: `pwa_menu/src/lib/cn.ts`, `format.ts`, `text.ts`
**Acceptance Criteria**:
- formatPrice(1500) -> "$1.500", removeAccents("Noquis") -> "Noquis", normalizeSearch works

### Task 1.5: Constants Configuration
**Files**: `pwa_menu/src/config/constants.ts`
**Acceptance Criteria**:
- All constants: API_URL, CACHE_TTL_MS (300000), SESSION_INACTIVITY_MS (28800000), DEBOUNCE_MS (300), AVATAR_COLORS (16 colors)

---

## Phase 2: TypeScript Types

### Task 2.1: Menu Types
**Files**: `pwa_menu/src/types/menu.ts`

### Task 2.2: Product Detail Types
**Files**: `pwa_menu/src/types/product-detail.ts`

### Task 2.3: Session & Filter Types
**Files**: `pwa_menu/src/types/session.ts`, `filters.ts`, `allergen-catalog.ts`, `api.ts`

---

## Phase 3: i18n Setup

### Task 3.1: i18next Configuration
**Files**: `pwa_menu/src/i18n/index.ts`, `types.ts`
**Acceptance Criteria**:
- Detection: localStorage -> navigator -> fallback 'es'
- Namespaces: common (eager), session/menu/filters/allergens (lazy)
- useSuspense: true

### Task 3.2: Spanish Translation Files (Complete)
**Files**: `pwa_menu/src/i18n/locales/es/common.json`, `session.json`, `menu.json`, `filters.json`, `allergens.json`
**Acceptance Criteria**:
- All 14 EU allergen names in Spanish
- All presence types and risk levels translated

### Task 3.3: English Translation Files
**Files**: `pwa_menu/src/i18n/locales/en/` (5 files)

### Task 3.4: Portuguese Translation Files
**Files**: `pwa_menu/src/i18n/locales/pt/` (5 files)
**Acceptance Criteria**:
- Brazilian Portuguese, default name: "Anonimo"

---

## Phase 4: Services & API Client

### Task 4.1: API Client with Session Token
**Files**: `pwa_menu/src/services/api-client.ts`
**Acceptance Criteria**:
- X-Session-Token header from session store
- 401/403 clears session, no JWT refresh

### Task 4.2: Service Layer
**Files**: `pwa_menu/src/services/session.service.ts`, `menu.service.ts`, `allergen.service.ts`
**Acceptance Criteria**:
- joinSession -> POST /api/sessions/join
- getMenu -> GET /api/public/menu/{slug}
- getProductDetail -> GET /api/public/menu/{slug}/product/{id}
- getAllergenCatalog -> GET /api/public/allergens?tenant={slug}

---

## Phase 5: Zustand Stores

### Task 5.1: Session Store
**Files**: `pwa_menu/src/stores/session.store.ts`
**Acceptance Criteria**:
- Persist as 'buen-sabor-session', 8h inactivity expiry, individual selectors only

### Task 5.2: Menu Store
**Files**: `pwa_menu/src/stores/menu.store.ts`
**Acceptance Criteria**:
- Persist as 'buen-sabor-menu-cache', 5min TTL, stale-while-revalidate

### Task 5.3: Filter Store
**Files**: `pwa_menu/src/stores/filter.store.ts`
**Acceptance Criteria**:
- NOT persisted, auto-sets 'strict' mode on allergen toggle, clearAll resets everything

### Task 5.4: Allergen Catalog Store
**Files**: `pwa_menu/src/stores/allergen-catalog.store.ts`
**Acceptance Criteria**:
- Builds bidirectional cross-reaction map, 5min TTL

### Task 5.5: Product Detail Store
**Files**: `pwa_menu/src/stores/product-detail.store.ts`

### Task 5.6: UI Store
**Files**: `pwa_menu/src/stores/ui.store.ts`
**Acceptance Criteria**:
- Toast auto-remove 4s, max 5, install banner dismiss with localStorage timestamp

---

## Phase 6: Hooks

### Task 6.1: Session Hooks
**Files**: `pwa_menu/src/hooks/useSessionGuard.ts`, `useActivityTracker.ts`
**Acceptance Criteria**:
- Activity tracker throttled to 1 write/60s, cleans up on unmount

### Task 6.2: Menu Data Hook
**Files**: `pwa_menu/src/hooks/useMenuData.ts`

### Task 6.3: Filter Hook (Core Filtering Logic)
**Files**: `pwa_menu/src/lib/filter-engine.ts`, `pwa_menu/src/hooks/useFilteredProducts.ts`
**Acceptance Criteria**:
- Pure filter function, memoized hook, search accent-insensitive
- Allergen strict/very_strict modes with cross-reaction expansion
- Dietary AND, Cooking OR, empty categories removed

### Task 6.4: Category Scroll Sync Hook
**Files**: `pwa_menu/src/hooks/useCategoryScroll.ts`
**Acceptance Criteria**:
- IntersectionObserver threshold 0.3, smooth scroll, cleanup on unmount

### Task 6.5: Utility Hooks
**Files**: `pwa_menu/src/hooks/useDebounce.ts`, `useFocusTrap.ts`

### Task 6.6: PWA Hooks
**Files**: `pwa_menu/src/hooks/usePWAInstall.ts`, `useSWUpdate.ts`, `pwa_menu/src/config/pwa.ts`
**Acceptance Criteria**:
- Install banner after 30s, 7-day dismiss cooldown
- SW update toast with skip waiting + reload

---

## Phase 7: UI Components (Atoms)

### Task 7.1: Base UI Components
**Files**: `pwa_menu/src/components/ui/Button.tsx`, `Input.tsx`, `Chip.tsx`, `Skeleton.tsx`, `Toast.tsx`, `ToastContainer.tsx`, `Badge.tsx`, `SealBadge.tsx`
**Acceptance Criteria**:
- All 44x44px min touch targets, aria-labels, cn() class merging

### Task 7.2: Modal Component (Bottom Sheet)
**Files**: `pwa_menu/src/components/ui/Modal.tsx`
**Acceptance Criteria**:
- Slide up, swipe dismiss >100px, backdrop click, Escape, focus trap, aria-modal

### Task 7.3: Drawer Component
**Files**: `pwa_menu/src/components/ui/Drawer.tsx`
**Acceptance Criteria**:
- Right-side desktop, bottom-sheet mobile, focus trap, scrollable

---

## Phase 8: Session Flow (Landing Page)

### Task 8.1: Landing Page Components
**Files**: `pwa_menu/src/components/session/BranchHeader.tsx`, `NameInput.tsx`, `ColorPalette.tsx`, `JoinButton.tsx`, `LandingPage.tsx`
**Acceptance Criteria**:
- Random initial color, optional name (defaults to locale-aware anonymous)
- Successful join navigates to menu, error shows toast

### Task 8.2: Language Selector
**Files**: `pwa_menu/src/components/layout/LanguageSelector.tsx`

### Task 8.3: Session Guard Route
**Files**: `pwa_menu/src/router/SessionGuard.tsx`

### Task 8.4: Layouts
**Files**: `pwa_menu/src/layouts/LandingLayout.tsx`, `MenuLayout.tsx`

---

## Phase 9: Menu Navigation

### Task 9.1: Menu Header
**Files**: `pwa_menu/src/components/layout/MenuHeader.tsx`

### Task 9.2: Category Tabs
**Files**: `pwa_menu/src/components/menu/CategoryTabs.tsx`
**Acceptance Criteria**:
- Horizontal scroll, no scrollbar, role="tablist", arrow key nav

### Task 9.3: Product Card
**Files**: `pwa_menu/src/components/menu/ProductCard.tsx`
**Acceptance Criteria**:
- Lazy image, line-clamp-2 name, formatted price, max 3 badges, availability overlay

### Task 9.4: Product Grid & Section Components
**Files**: `pwa_menu/src/components/menu/ProductGrid.tsx`, `SubcategorySection.tsx`, `CategorySection.tsx`, `EmptyState.tsx`, `MenuSkeleton.tsx`

### Task 9.5: Search Bar
**Files**: `pwa_menu/src/components/menu/SearchBar.tsx`
**Acceptance Criteria**:
- 300ms debounce, clear button, type="search", aria-label

### Task 9.6: Menu Page (Container)
**Files**: `pwa_menu/src/components/menu/MenuPage.tsx`

---

## Phase 10: Product Detail Modal

### Task 10.1: Product Detail Components
**Files**: `pwa_menu/src/components/product-detail/ProductImageGallery.tsx`, `ProductInfo.tsx`, `ProductBadges.tsx`, `AllergenEntry.tsx`, `CrossReactionList.tsx`, `AllergenList.tsx`, `IngredientList.tsx`, `DietaryProfileList.tsx`, `CookingMethodList.tsx`, `FlavorTextureSection.tsx`, `ProductDetailSkeleton.tsx`
**Acceptance Criteria**:
- Allergen traffic-light colors, collapsible cross-reactions, formatted ingredients

### Task 10.2: Product Detail Modal (Container)
**Files**: `pwa_menu/src/components/product-detail/ProductDetailModal.tsx`, `pwa_menu/src/hooks/useProductDetail.ts`
**Acceptance Criteria**:
- URL sync on open/close, browser back closes modal, skeleton while loading

---

## Phase 11: Filter System

### Task 11.1: Filter Drawer Components
**Files**: `pwa_menu/src/components/filters/AllergenModeSelector.tsx`, `FilterChip.tsx`, `AllergenFilterSection.tsx`, `DietaryFilterSection.tsx`, `CookingFilterSection.tsx`, `ClearFiltersButton.tsx`, `FilterDrawer.tsx`
**Acceptance Criteria**:
- Radio group for allergen mode, checkbox chips for filters
- Dietary/cooking deduplicated from menu data
- Clear button only when filters active

---

## Phase 12: Bottom Bar & PWA Components

### Task 12.1: Bottom Bar
**Files**: `pwa_menu/src/components/layout/BottomBar.tsx`, `BottomBarButton.tsx`
**Acceptance Criteria**:
- Fixed bottom, safe area inset, 3 FABs 56x56px, "Proximamente" toast on tap

### Task 12.2: PWA Components
**Files**: `pwa_menu/src/components/pwa/UpdateToast.tsx`, `pwa_menu/src/components/ui/InstallBanner.tsx`, `OfflineIndicator.tsx`

---

## Phase 13: Router & App Assembly

### Task 13.1: Router Configuration
**Files**: `pwa_menu/src/router/routes.ts`, `index.tsx`

### Task 13.2: App Entry Point
**Files**: `pwa_menu/src/main.tsx`, `App.tsx`

---

## Phase 14: Integration & Polish

### Task 14.1: Activity Tracker Integration
**Files**: Modify `pwa_menu/src/layouts/MenuLayout.tsx`

### Task 14.2: Allergen Catalog Prefetch
**Files**: Modify `pwa_menu/src/components/menu/MenuPage.tsx`

### Task 14.3: PWA Icons
**Files**: `pwa_menu/public/icon-*.png`, `favicon.svg`

### Task 14.4: Backend — Session Join Endpoint
**Files**: `rest_api/routers/public/session_router.py`, `rest_api/services/session_service.py`, `rest_api/models/customer_session.py`, `shared/schemas/session.py`
**Acceptance Criteria**:
- Validates branch/table, HMAC-SHA256 token, 3h expiry, rate limited 60/min
- Returns 404 if not found, 409 if table inactive

---

## Summary

| Phase | Tasks | Files |
|-------|-------|-------|
| 1. Scaffolding | 5 | ~10 |
| 2. Types | 3 | 6 |
| 3. i18n | 4 | 17 |
| 4. Services | 2 | 4 |
| 5. Stores | 6 | 6 |
| 6. Hooks | 6 | ~10 |
| 7. UI Atoms | 3 | ~12 |
| 8. Session Flow | 4 | ~10 |
| 9. Menu Navigation | 6 | ~10 |
| 10. Product Detail | 2 | ~13 |
| 11. Filters | 1 | 7 |
| 12. Bottom Bar + PWA | 2 | 5 |
| 13. Router + App | 2 | 4 |
| 14. Integration | 4 | ~8 |
| **TOTAL** | **50** | **~122 files** |

Estimated: **6-8 implementation sessions**

---

## Next Recommended
-> `sdd-apply` (Begin implementation in phases)
