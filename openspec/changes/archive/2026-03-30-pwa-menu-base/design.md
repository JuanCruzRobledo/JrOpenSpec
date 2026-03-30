---
sprint: 6
artifact: design
status: complete
---

# SDD Design — Sprint 6: pwaMenu Base — Ingreso y Navegacion

## Status: APPROVED

---

## 1. Folder Structure

```
pwa_menu/
+-- index.html
+-- package.json
+-- pnpm-lock.yaml
+-- tsconfig.json
+-- tsconfig.app.json
+-- tsconfig.node.json
+-- vite.config.ts                    # React compiler + vite-plugin-pwa
+-- .env                              # VITE_API_URL=http://localhost:8000
+-- .env.example
+-- public/
|   +-- favicon.svg
|   +-- icon-192x192.png
|   +-- icon-512x512.png
|   +-- icon-192x192-maskable.png
|   +-- icon-512x512-maskable.png
|   +-- manifest.json
+-- src/
    +-- main.tsx
    +-- App.tsx
    +-- index.css                     # TailwindCSS 4 + @theme dark+orange
    +-- vite-env.d.ts
    +-- config/
    |   +-- constants.ts
    |   +-- pwa.ts
    +-- i18n/
    |   +-- index.ts
    |   +-- locales/
    |   |   +-- es/ (common, session, menu, filters, allergens .json)
    |   |   +-- en/ (same)
    |   |   +-- pt/ (same)
    |   +-- types.ts
    +-- types/
    |   +-- menu.ts
    |   +-- product-detail.ts
    |   +-- allergen-catalog.ts
    |   +-- session.ts
    |   +-- filters.ts
    |   +-- api.ts
    +-- services/
    |   +-- api-client.ts
    |   +-- session.service.ts
    |   +-- menu.service.ts
    |   +-- allergen.service.ts
    +-- stores/
    |   +-- session.store.ts
    |   +-- menu.store.ts
    |   +-- filter.store.ts
    |   +-- allergen-catalog.store.ts
    |   +-- product-detail.store.ts
    |   +-- ui.store.ts
    +-- hooks/
    |   +-- useSessionGuard.ts
    |   +-- useActivityTracker.ts
    |   +-- useMenuData.ts
    |   +-- useFilteredProducts.ts
    |   +-- useCategoryScroll.ts
    |   +-- useDebounce.ts
    |   +-- useProductDetail.ts
    |   +-- usePWAInstall.ts
    |   +-- useSWUpdate.ts
    |   +-- useFocusTrap.ts
    +-- router/
    |   +-- index.tsx
    |   +-- routes.ts
    |   +-- SessionGuard.tsx
    +-- layouts/
    |   +-- LandingLayout.tsx
    |   +-- MenuLayout.tsx
    +-- components/
    |   +-- ui/ (Button, Input, Chip, Modal, Drawer, Skeleton, Toast, ToastContainer, Badge, SealBadge, OfflineIndicator, InstallBanner)
    |   +-- session/ (LandingPage, BranchHeader, NameInput, ColorPalette, JoinButton)
    |   +-- menu/ (MenuPage, CategoryTabs, SearchBar, ProductGrid, ProductCard, SubcategorySection, CategorySection, EmptyState, MenuSkeleton)
    |   +-- product-detail/ (ProductDetailModal, ProductImageGallery, ProductInfo, ProductBadges, AllergenList, AllergenEntry, CrossReactionList, IngredientList, DietaryProfileList, CookingMethodList, FlavorTextureSection, ProductDetailSkeleton)
    |   +-- filters/ (FilterDrawer, AllergenFilterSection, AllergenModeSelector, DietaryFilterSection, CookingFilterSection, FilterChip, ClearFiltersButton)
    |   +-- layout/ (MenuHeader, LanguageSelector, BottomBar, BottomBarButton)
    |   +-- pwa/ (UpdateToast, OfflineFallback)
    +-- lib/
        +-- cn.ts
        +-- format.ts
        +-- text.ts
        +-- filter-engine.ts
```

---

## 2. Component Tree

```
<App>
  <I18nextProvider>
    <RouterProvider>
      |
      +-- /:tenant/:branch/mesa/:table -> <LandingLayout>
      |   +-- <LandingPage>
      |       +-- <BranchHeader branchName tableName />
      |       +-- <NameInput value onChange maxLength={50} />
      |       +-- <ColorPalette colors={AVATAR_COLORS} selected onChange />
      |       +-- <JoinButton onClick isLoading />
      |       +-- <LanguageSelector />
      |
      +-- /:tenant/:branch -> <SessionGuard> -> <MenuLayout>
          +-- <MenuHeader>
          |   +-- branchName, tableName, avatar, LanguageSelector, filter button with badge
          |
          +-- <main>
          |   +-- <CategoryTabs categories activeId onSelect />
          |   +-- <SearchBar value onChange onClear />
          |   +-- {filteredCategories.map -> CategorySection -> SubcategorySection -> ProductGrid -> ProductCard}
          |   +-- <EmptyState /> or <MenuSkeleton />
          |
          +-- <BottomBar>
          |   +-- 3x BottomBarButton (callWaiter, history, myBill) -> placeholder toast
          |
          +-- <FilterDrawer isOpen onClose>
          |   +-- AllergenFilterSection (mode selector + allergen chips)
          |   +-- DietaryFilterSection (dietary chips)
          |   +-- CookingFilterSection (cooking chips)
          |   +-- ClearFiltersButton
          |
          +-- <ProductDetailModal> (triggered by URL /product/:id)
              +-- ProductImageGallery, ProductInfo, ProductBadges
              +-- AllergenList -> AllergenEntry -> CrossReactionList
              +-- DietaryProfileList, CookingMethodList
              +-- FlavorTextureSection, IngredientList

      Portals: ToastContainer, OfflineIndicator, InstallBanner, UpdateToast
```

---

## 3. Zustand Stores

### 3.1 Session Store
- Persisted in localStorage as `buen-sabor-session`
- Fields: token, sessionId, displayName, avatarColor, branchSlug, branchName, tableIdentifier, tableName, joinedAt, lastActivity
- Actions: join(), clear(), updateActivity(), isExpired()
- 8-hour inactivity sliding window

### 3.2 Menu Store
- Persisted in localStorage as `buen-sabor-menu-cache`
- Fields: data (MenuResponse), fetchedAt, isLoading, isBackgroundRefreshing, error
- Actions: fetchMenu(slug), backgroundRefresh(slug), isStale(), clearMenu()
- 5-minute cache TTL, stale-while-revalidate pattern

### 3.3 Filter Store
- NOT persisted (resets on page reload)
- Fields: searchQuery, allergenMode (off/strict/very_strict), selectedAllergens[], selectedDietary[], selectedCooking[]
- Actions: setSearchQuery, setAllergenMode, toggleAllergen, toggleDietary, toggleCooking, clearAll, activeFilterCount()
- Auto-sets mode to "strict" when allergens selected without mode

### 3.4 Allergen Catalog Store
- NOT persisted (re-fetched on load)
- Fields: catalog[], crossReactionMap (Map<string, string[]>), fetchedAt, isLoading
- Actions: fetchCatalog(tenantSlug), isStale()
- Builds bidirectional cross-reaction map on fetch

### 3.5 Product Detail Store
- NOT persisted
- Fields: product (ProductDetail), isLoading, error, isOpen
- Actions: fetchProduct(slug, id), close()

### 3.6 UI Store
- NOT persisted
- Fields: filterDrawerOpen, installBannerVisible, toasts[]
- Actions: openFilterDrawer, closeFilterDrawer, showInstallBanner, hideInstallBanner, addToast, removeToast
- Toast auto-removes after 4 seconds, max 5 visible

---

## 4. Routing

```typescript
const ROUTES = {
  LANDING: '/:tenant/:branch/mesa/:table',
  MENU: '/:tenant/:branch',
  PRODUCT_DETAIL: '/:tenant/:branch/product/:productId',
};
```

Product detail is the same MenuPage with a modal overlay triggered by URL. This preserves scroll position and filter state.

---

## 5. i18n Setup

- i18next with react-i18next, LanguageDetector, HTTP backend
- Fallback: es, supported: es/en/pt
- Namespaces: common (eager), session/menu/filters/allergens (lazy via Suspense)
- Detection order: localStorage -> navigator.language -> fallback "es"
- Load path: `/locales/{{lng}}/{{ns}}.json`

---

## 6. PWA Configuration

- vite-plugin-pwa with registerType: 'prompt'
- Runtime manifest link replacement generates tenant/branch-scoped `start_url` and `scope` from the active route before install; static `/manifest.json` remains a fallback shell manifest for first paint
- Precache: app shell (HTML, JS, CSS, fonts)
- Runtime CacheFirst 30d: images (local + CDN patterns)
- Runtime NetworkFirst 5s: /api/public/*
- StaleWhileRevalidate 365d: fonts
- Navigate fallback: /index.html (SPA offline shell)
- Custom install banner after 30s, dismissible for 7 days
- Update toast with "Actualizar" button

---

## 7. API Client

- Axios with baseURL from VITE_API_URL
- Request interceptor: adds X-Table-Token header
- Response interceptor: on 401/403 -> clear session (redirect handled by SessionGuard)
- No JWT refresh flow (simple HMAC tokens)

---

## 8. Theme Configuration (CSS @theme)

```css
@theme {
  --color-bg-primary: #0a0a0a;
  --color-bg-surface: #171717;
  --color-bg-elevated: #262626;
  --color-accent: #f97316;
  --color-accent-hover: #ea580c;
  --color-text-primary: #fafafa;
  --color-text-secondary: #a3a3a3;
  --color-text-tertiary: #737373;
  --color-border-default: #262626;
  --color-border-focus: #f97316;
  --color-success: #22c55e;
  --color-error: #ef4444;
  --color-warning: #eab308;
  --color-info: #3b82f6;
  /* Allergen traffic-light */
  --color-allergen-contains-bg: rgba(239, 68, 68, 0.2);
  --color-allergen-contains-border: #ef4444;
  --color-allergen-contains-text: #fca5a5;
  --color-allergen-may-contain-bg: rgba(249, 115, 22, 0.2);
  --color-allergen-may-contain-border: #f59e0b;
  --color-allergen-may-contain-text: #fcd34d;
  --color-allergen-free-bg: rgba(34, 197, 94, 0.2);
  --color-allergen-free-border: #22c55e;
  --color-allergen-free-text: #86efac;
  --font-family-sans: 'Inter', system-ui, -apple-system, sans-serif;
}
```

---

## 9. Accessibility Patterns

- Focus trap in modals/drawers via useFocusTrap hook
- Category tabs: role="tablist" with arrow key navigation
- Filter chips: role="checkbox" with aria-checked
- Product cards: role="article" with aria-label
- Modals: role="dialog", aria-modal="true"
- Semantic HTML: header, main, nav, section, article
- Min 44x44px touch targets
- prefers-reduced-motion support

---

## 10. Key Technical Decisions

- **D1**: Product detail as modal overlay (not separate route) to preserve scroll and filter state
- **D2**: Client-side filtering on cached menu (<100KB) for instant results
- **D3**: Separate allergen catalog store for cross-reaction map (not in menu response)
- **D4**: No JWT/auth store -- simple HMAC session tokens for anonymous customers
- **D5**: vite-plugin-pwa with registerType: 'prompt' for controlled update UX
- **D6**: Bottom-sheet modal for mobile-native feel
- **D7**: IntersectionObserver for category scroll sync (not scroll events)
- **D8**: No TanStack Query -- Zustand with manual stale-while-revalidate for 3-4 API calls

---

## Next Recommended
-> `sdd-tasks` (Hierarchical task breakdown with acceptance criteria and file paths)
