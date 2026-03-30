---
sprint: 6
artifact: spec
status: complete
---

# SDD Spec — Sprint 6: pwaMenu Base — Ingreso y Navegacion

## Status: APPROVED

---

## 1. Requirements (RFC 2119)

### 1.1 Project Setup

- The pwaMenu MUST be scaffolded with Vite 7.2, React 19.2, TypeScript 5.9
- The project MUST include `babel-plugin-react-compiler` in the Vite config
- TailwindCSS 4 MUST be configured with CSS-first `@theme` directive (NO tailwind.config.ts)
- Zustand 5 MUST be used for state management with `persist` middleware where specified
- All Zustand selectors MUST be individual (NO destructuring, NO object-returning selectors) to prevent React 19 infinite render loops
- i18next with react-i18next MUST be configured with namespace-based lazy loading
- `vite-plugin-pwa` MUST be installed and configured with Workbox strategies
- The project MUST reside in `pwa_menu/` directory within the monorepo
- The project MUST use `pnpm` as package manager (consistent with dashboard)

### 1.2 i18n

- The app MUST support 3 languages: `es` (Spanish, complete), `en` (English), `pt` (Portuguese)
- i18n detection order MUST be: localStorage key `i18nextLng` -> `navigator.language` -> fallback `es`
- The user MUST be able to manually switch language via a flag selector showing: AR (es), US (en), BR (pt)
- Language selection MUST persist in localStorage
- Translation namespaces MUST be: `common`, `menu`, `session`, `filters`, `allergens`
- Namespaces MUST be lazy-loaded (loaded on demand per route/feature)
- Missing translation keys MUST fall back in order: requested language -> `es` -> raw key name
- All user-facing strings MUST use i18n keys (no hardcoded strings in components)

### 1.3 Session Flow (QR -> Token -> Store)

- QR codes MUST encode URLs in format: `https://{domain}/{tenant_slug}/{branch_slug}/mesa/{table_identifier}`
- The landing page MUST display the branch name, table identifier, and restaurant logo
- The user MAY enter a display name (max 50 characters, trimmed, optional -- defaults to "Anonimo"/"Anonymous"/"Anonimo" based on locale)
- The user MUST select an avatar color from a palette of exactly 16 predefined colors
- The 16 colors MUST be: `#EF4444` (red), `#F97316` (orange), `#F59E0B` (amber), `#EAB308` (yellow), `#84CC16` (lime), `#22C55E` (green), `#10B981` (emerald), `#14B8A6` (teal), `#06B6D4` (cyan), `#3B82F6` (blue), `#6366F1` (indigo), `#8B5CF6` (violet), `#A855F7` (purple), `#EC4899` (pink), `#F43F5E` (rose), `#78716C` (stone)
- Default avatar color MUST be randomly selected on page load
- On "Entrar" button press, the app MUST call `POST /api/sessions/join`
- The response token MUST be stored in localStorage under key `buen-sabor-session-token`
- Session metadata (displayName, avatarColor, branchSlug, tableId, joinedAt) MUST be stored in Zustand with `persist` middleware under key `buen-sabor-session`
- The localStorage session MUST expire after 8 hours of inactivity (sliding window)
- "Inactivity" means no user interaction events (touch, scroll, click) for 8 hours
- On any user interaction, the `lastActivity` timestamp MUST be updated in localStorage
- On app load, if `Date.now() - lastActivity > 8 * 60 * 60 * 1000`, the session MUST be cleared and user redirected to landing
- The HMAC token itself expires server-side in 3 hours; the client SHOULD NOT decode or validate the token locally

### 1.4 Session Join API Contract

**`POST /api/sessions/join`**

Request:
```json
{
  "branchSlug": "buen-sabor-centro",
  "tableIdentifier": "mesa-12",
  "displayName": "Juani",
  "avatarColor": "#F97316",
  "locale": "es"
}
```

Response 200:
```json
{
  "token": "hmac_sha256_base64_encoded_token_string",
  "sessionId": "uuid-v4",
  "expiresAt": "2026-03-19T18:30:00Z",
  "branch": {
    "id": 1,
    "name": "Buen Sabor Centro",
    "slug": "buen-sabor-centro"
  },
  "table": {
    "identifier": "mesa-12",
    "displayName": "Mesa 12"
  }
}
```

Response 404: `{"detail": "Branch or table not found"}`
Response 409: `{"detail": "Table is not active"}`

**HMAC Token Payload** (server-side, not decoded by client):
```
{branch_id}:{table_id}:{session_id}:{created_at_unix}
```
Signed with: `HMAC-SHA256(payload, SERVER_SECRET)`
Token format: `base64(payload).base64(signature)`

### 1.5 Menu Navigation

- The menu MUST display 3 hierarchical levels: Category -> Subcategory -> Product
- Categories MUST be displayed as horizontally scrollable chips/tabs at the top of the menu
- The first category MUST be auto-selected on menu load
- Clicking a category MUST scroll to that category's section AND highlight the active chip
- Scrolling through the page MUST update the active category chip (intersection observer)
- Subcategories within a category MUST be shown as section headers
- Products MUST be displayed in a responsive grid: 2 columns on mobile (<640px), 3 columns on tablet (640-1024px), 4 columns on desktop (>1024px)
- Each product card MUST show: product image (lazy loaded, with placeholder), product name, formatted price (`$1.500`), badges (max 3 visible, "+N" if more), availability indicator
- Product images MUST use `loading="lazy"` and have a skeleton placeholder while loading
- If a product has `isAvailable: false`, the card MUST show a "No disponible" overlay with reduced opacity
- Empty categories (no products after filtering) MUST be hidden
- The menu data MUST be fetched from `GET /api/public/menu/{slug}`
- Menu data MUST be cached in Zustand store for 5 minutes (300,000ms)
- After cache expires, the next render MUST trigger a background fetch (stale-while-revalidate)
- During background refresh, the UI MUST continue showing stale data (no loading spinner)
- If the background refresh fails, the stale data MUST remain visible and a subtle toast SHOULD appear

### 1.6 Product Detail Modal

- Tapping a product card MUST open a bottom-sheet modal (slides up from bottom on mobile)
- The modal MUST display: full product image (gallery if multiple), product name, full description, formatted price, badges (full list), seals (full list), dietary profiles with icons, allergen information (detailed), cooking methods with icons, flavor profiles as tags, texture profiles as tags, ingredient list (sorted by sort_order)
- **Allergen Display**: Each allergen MUST show an icon, name, and a traffic-light color indicator:
  - `contains` -> RED background (#EF4444 at 20% opacity, red border, red text)
  - `may_contain` -> YELLOW/AMBER background (#F59E0B at 20% opacity, amber border, amber text)
  - `free_of` -> GREEN background (#22C55E at 20% opacity, green border, green text)
- Each allergen entry MUST show: icon, name, presence type label (Contiene/Puede contener/Libre de), risk level, notes (if any)
- Cross-reactions MUST be shown as a collapsible section under each "contains" or "may_contain" allergen
- Cross-reaction items MUST show: related allergen name, description, severity badge
- Ingredients MUST be shown as an ordered list with: name, quantity + unit formatted (e.g., "250g", "1 cda"), optional badge if `isOptional: true`
- The modal MUST be dismissible by: swiping down, tapping outside/backdrop, tapping X button, pressing Escape
- Product detail data MUST be fetched from `GET /api/public/menu/{slug}/product/{id}`
- The fetch MUST show a skeleton loader inside the modal while loading
- URL MUST update to `/{tenant}/{branch}/product/{id}` when modal is open (for shareability) and revert when closed

### 1.7 Search

- A search bar MUST be present at the top of the menu page, below the category tabs
- Search input MUST have a 300ms debounce before filtering
- Search MUST filter products by: name (case-insensitive, accent-insensitive), short description (case-insensitive)
- Search MUST be performed client-side on cached menu data
- When search is active, category grouping MUST still be visible (don't flatten results)
- Empty search results MUST show a localized "No se encontraron productos" message with a clear-search button
- The search bar MUST have a clear (X) button visible when text is present
- Search term MUST be preserved when navigating to product detail and back

### 1.8 Allergen Filtering

- A filter panel MUST be accessible via a filter icon button on the menu page
- The filter panel MUST slide in from the right (or bottom on mobile) as a drawer
- **Allergen filter section**:
  - Displays all allergens from `GET /api/public/allergens?tenant={slug}` (cached 5min)
  - Each allergen shown as a toggleable chip with icon and name
  - Above the allergen chips, a **strictness mode selector** with 3 options:
    1. **Sin filtro** (Off): No allergen filtering applied. Default.
    2. **Estricto** (Strict): Hide products where `presenceType = "contains"` for ANY selected allergen
    3. **Muy estricto** (Very Strict): Hide products where `presenceType = "contains" OR "may_contain"` for ANY selected allergen. ALSO hide products containing allergens that have cross-reactions with selected allergens.
  - Selecting a strictness mode without any allergens selected MUST have no effect
  - Selecting allergens without a strictness mode MUST default to "Estricto"
- **Cross-reaction logic (Very Strict mode)**:
  - When user selects allergen A, and allergen A has cross-reactions with allergens B and C
  - Products containing B or C (per the "may_contain" or "contains" presence) MUST also be hidden
  - Cross-reaction data comes from the allergen catalog response (`crossReactions` array on each allergen)
  - Cross-reaction expansion MUST be cached client-side for 5 minutes
  - The UI MUST indicate when products are hidden due to cross-reactions (e.g., "Oculto por reaccion cruzada con [allergen name]")
- Filter results MUST update in real-time as the user toggles allergens (no "Apply" button for allergen filter)
- Active allergen filter count MUST be shown as a badge on the filter icon
- A "Limpiar filtros" (Clear filters) button MUST be present in the filter drawer

### 1.9 Dietary Preference Filtering

- In the same filter drawer, below allergen filters, a **dietary preferences** section
- Displays all dietary profiles from the menu data (`dietaryProfiles` on products, deduplicated)
- Each dietary profile shown as a toggleable chip with icon and name
- Logic: show only products that match ALL selected dietary profiles (AND logic)
- If no dietary profiles selected, no dietary filtering applied
- Filter MUST work in combination with allergen filter and search (all filters are ANDed)

### 1.10 Cooking Method Filtering

- In the same filter drawer, below dietary preferences, a **cooking method** section
- Displays all cooking methods from the menu data (deduplicated from products)
- Each cooking method shown as a toggleable chip with icon and name
- Logic: show products that match ANY selected cooking method (OR logic)
- If no cooking methods selected, no cooking method filtering applied
- Combines with other filters via AND

### 1.11 PWA Configuration

- The app MUST ship a fallback static `manifest.json` for first paint and for browsers that resolve the manifest before route context is known.
- Before the install flow is presented on a tenant/branch route, the app MUST replace the manifest link at runtime with a generated manifest scoped to the active route.
- The runtime-scoped manifest MUST include:
  - `name`: "{Restaurant Name} - Menu"
  - `short_name`: "Menu"
  - `start_url`: "/{tenant_slug}/{branch_slug}"
  - `scope`: "/{tenant_slug}/{branch_slug}"
  - `display`: "standalone"
  - `orientation`: "portrait"
  - `theme_color`: "#f97316"
  - `background_color`: "#0a0a0a"
  - `icons`: 192x192 and 512x512 PNG (maskable + any)
  - `categories`: ["food"]
  - `lang`: "es"
- The fallback static `manifest.json` SHOULD keep shell-safe defaults (`start_url: "/"`, `scope: "/"`) while preserving equivalent icon and theme metadata.
- Service Worker (Workbox via vite-plugin-pwa):
  - **Precache**: App shell (index.html, JS bundles, CSS)
  - **Runtime CacheFirst** (30 days): Image URLs matching `*.cdn.*`, `*.cloudinary.*`, `*.amazonaws.com/*`, common image extensions
  - **Runtime NetworkFirst** (5s timeout): API calls matching `/api/public/*`
  - **SPA Fallback**: Navigate requests -> serve cached `index.html` (offline shell)
  - **Offline fallback**: If network fails AND no cache exists for API, show offline message component
- The app MUST show a custom install banner (not the browser default) after 30 seconds on the page
- The install banner MUST be dismissible and not shown again for 7 days (localStorage flag with timestamp)
- Service worker updates MUST show a "Nueva version disponible" toast with a "Actualizar" button that calls `registration.waiting.postMessage({ type: 'SKIP_WAITING' })` then reloads

### 1.12 Workbox Cache Strategies (Detailed)

```
Strategy: CacheFirst
  Match: /\.(png|jpg|jpeg|webp|avif|gif|svg|ico)$/i AND external CDN patterns
  Cache Name: "images-cache"
  Max Entries: 200
  Max Age: 30 days
  Purge on quota error: true

Strategy: NetworkFirst
  Match: /\/api\/public\/.*/
  Cache Name: "api-cache"
  Network Timeout: 5 seconds
  Max Entries: 50
  Max Age: 1 day

Strategy: StaleWhileRevalidate
  Match: /\.(woff2?|ttf|otf)$/i
  Cache Name: "fonts-cache"
  Max Entries: 20
  Max Age: 365 days

Precache: Generated by vite-plugin-pwa (app shell, JS chunks, CSS)
```

### 1.13 Theme (Dark + Orange)

- Background primary: `#0a0a0a` (near black)
- Background surface: `#171717` (card backgrounds)
- Background elevated: `#262626` (modals, drawers)
- Accent color: `#f97316` (orange-500)
- Accent hover: `#ea580c` (orange-600)
- Text primary: `#fafafa`
- Text secondary: `#a3a3a3`
- Text tertiary: `#737373`
- Border default: `#262626`
- Border focus: `#f97316`
- Success: `#22c55e`, Error: `#ef4444`, Warning: `#eab308`, Info: `#3b82f6`
- Font: `'Inter', system-ui, -apple-system, sans-serif`
- All interactive elements MUST have `transition-colors duration-150`

### 1.14 Bottom Bar

- A fixed bottom bar MUST be present on the menu page
- The bar MUST have 3 floating action buttons (FABs):
  1. **Llamar mozo** (Call waiter): bell icon -- placeholder, shows "Proximamente" toast on tap
  2. **Historial** (History): clock icon -- placeholder, shows "Proximamente" toast on tap
  3. **Mi cuenta** (My bill): receipt icon -- placeholder, shows "Proximamente" toast on tap
- The bar MUST be `position: fixed; bottom: 0` with safe area inset padding (`pb-safe`)
- The bar MUST NOT overlap the last product card (add bottom padding to main content equal to bar height + 16px)
- FABs MUST be 56x56px with the accent orange color and white icons

### 1.15 Accessibility

- All interactive elements MUST have `aria-label` attributes
- All images MUST have `alt` text (product name for product images)
- Touch targets MUST be minimum 44x44px (WCAG 2.5.8)
- The app MUST use semantic HTML: `<header>`, `<main>`, `<nav>`, `<section>`, `<article>` for product cards
- Focus MUST be visible on all interactive elements (orange ring: `focus-visible:ring-2 focus-visible:ring-accent`)
- The filter drawer MUST trap focus when open
- The product detail modal MUST trap focus when open and return focus to the triggering card on close
- Color MUST NOT be the only means of conveying allergen information (icons + text always accompany color)
- The app MUST support `prefers-reduced-motion` (disable animations when enabled)

### 1.16 Menu Data Model (Frontend TypeScript Types)

```typescript
interface MenuResponse {
  branch: BranchInfo;
  categories: MenuCategory[];
  allergenLegend: AllergenLegendItem[];
  generatedAt: string;
}

interface BranchInfo {
  id: number;
  name: string;
  slug: string;
  address: string;
  phone: string;
  openNow: boolean;
  schedule: Record<string, { open: string; close: string } | null>;
}

interface MenuCategory {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  sortOrder: number;
  subcategories: MenuSubcategory[];
}

interface MenuSubcategory {
  id: number;
  name: string;
  slug: string;
  sortOrder: number;
  products: MenuProduct[];
}

interface MenuProduct {
  id: number;
  name: string;
  shortDescription: string;
  priceCents: number;
  imageUrl: string | null;
  badges: Badge[];
  seals: Seal[];
  dietaryProfiles: string[];
  allergenSummary: {
    contains: string[];
    mayContain: string[];
    freeOf: string[];
  };
  cookingMethods: string[];
  flavorProfiles: string[];
  isAvailable: boolean;
}

interface ProductDetail {
  id: number;
  name: string;
  description: string;
  shortDescription: string;
  priceCents: number;
  imageUrl: string | null;
  imageGallery: string[];
  badges: Badge[];
  seals: Seal[];
  dietaryProfiles: DietaryProfileInfo[];
  allergens: ProductAllergenDetail[];
  cookingMethods: CookingMethodInfo[];
  flavorProfiles: string[];
  textureProfiles: string[];
  ingredients: Ingredient[];
  branch: { id: number; name: string; slug: string };
  category: { id: number; name: string; slug: string };
  generatedAt: string;
}

interface ProductAllergenDetail {
  code: string;
  name: string;
  icon: string;
  presenceType: 'contains' | 'may_contain' | 'free_of';
  riskLevel: 'low' | 'moderate' | 'severe' | 'life_threatening';
  notes: string | null;
  crossReactions: CrossReaction[];
}

interface SessionJoinRequest {
  branchSlug: string;
  tableIdentifier: string;
  displayName: string;
  avatarColor: string;
  locale: string;
}

interface SessionJoinResponse {
  token: string;
  sessionId: string;
  expiresAt: string;
  branch: { id: number; name: string; slug: string };
  table: { identifier: string; displayName: string };
}

interface SessionState {
  token: string | null;
  sessionId: string | null;
  displayName: string;
  avatarColor: string;
  branchSlug: string | null;
  tableIdentifier: string | null;
  tableName: string | null;
  branchName: string | null;
  joinedAt: string | null;
  lastActivity: number;
}
```

### 1.17 Filter Algorithm (Detailed)

```typescript
function filterProducts(
  products: MenuProduct[],
  search: string,
  allergenFilter: { codes: string[]; mode: 'off' | 'strict' | 'very_strict' },
  dietaryFilter: string[],
  cookingFilter: string[],
  crossReactionMap: Map<string, string[]>
): MenuProduct[] {
  return products.filter(product => {
    // 1. Search filter
    if (search.length > 0) {
      const normalized = removeAccents(search.toLowerCase());
      const nameMatch = removeAccents(product.name.toLowerCase()).includes(normalized);
      const descMatch = removeAccents(product.shortDescription.toLowerCase()).includes(normalized);
      if (!nameMatch && !descMatch) return false;
    }
    // 2. Allergen filter
    if (allergenFilter.mode !== 'off' && allergenFilter.codes.length > 0) {
      const selectedAllergens = new Set(allergenFilter.codes);
      if (allergenFilter.mode === 'strict') {
        const hasContains = product.allergenSummary.contains.some(code => selectedAllergens.has(code));
        if (hasContains) return false;
      }
      if (allergenFilter.mode === 'very_strict') {
        const expandedAllergens = new Set(selectedAllergens);
        for (const code of selectedAllergens) {
          const related = crossReactionMap.get(code) || [];
          related.forEach(r => expandedAllergens.add(r));
        }
        const hasContains = product.allergenSummary.contains.some(code => expandedAllergens.has(code));
        const hasMayContain = product.allergenSummary.mayContain.some(code => expandedAllergens.has(code));
        if (hasContains || hasMayContain) return false;
      }
    }
    // 3. Dietary filter (AND)
    if (dietaryFilter.length > 0) {
      const productDietary = new Set(product.dietaryProfiles);
      const matchesAll = dietaryFilter.every(code => productDietary.has(code));
      if (!matchesAll) return false;
    }
    // 4. Cooking method filter (OR)
    if (cookingFilter.length > 0) {
      const productCooking = new Set(product.cookingMethods);
      const matchesAny = cookingFilter.some(code => productCooking.has(code));
      if (!matchesAny) return false;
    }
    return true;
  });
}
```

### 1.18 i18n Key Structure

Namespaces: `common`, `session`, `menu`, `filters`, `allergens` for each locale (es, en, pt).

Key examples:
- `session.landing.title`: "Bienvenido a {{branchName}}"
- `menu.search.placeholder`: "Buscar productos..."
- `filters.allergens.modeStrict`: "Estricto"
- `allergens.presence.contains`: "Contiene"
- `allergens.names.gluten`: "Gluten"

---

## 2. Scenarios (Given/When/Then)

### S1: QR Scan and Landing
- **Given** a customer scans QR code linking to `/buen-sabor/buen-sabor-centro/mesa/mesa-12`
- **When** the page loads
- **Then** the landing page shows "Bienvenido a Buen Sabor Centro", "Mesa 12", name input, color palette with 16 colors, and "Entrar al menu" button
- **And** one color is randomly pre-selected

### S2: Session Join -- Happy Path
- **Given** a customer on the landing page enters name "Juani" and selects color #F97316
- **When** they tap "Entrar al menu"
- **Then** `POST /api/sessions/join` is called with the appropriate payload
- **And** the returned token is stored in localStorage key `buen-sabor-session-token`
- **And** the app navigates to the menu page

### S3: Session Join -- No Name
- **Given** a customer leaves the name field empty
- **When** they tap "Entrar al menu"
- **Then** displayName is sent as "Anonimo" (based on locale)
- **And** session is created successfully

### S4: Session Expiry by Inactivity
- **Given** a customer joined 9 hours ago and lastActivity was 8.5 hours ago
- **When** they reopen the app
- **Then** `Date.now() - lastActivity > 28800000` is true
- **And** localStorage session is cleared
- **And** user is redirected to the landing page

### S5: Menu Load and Category Navigation
- **Given** a customer has an active session for branch "buen-sabor-centro"
- **When** the menu page loads
- **Then** `GET /api/public/menu/buen-sabor-centro` is called
- **And** categories are displayed as horizontal scrollable chips
- **And** the first category is highlighted
- **And** products are shown in a grid grouped by category -> subcategory

### S6: Category Scroll Sync
- **Given** the menu is loaded with categories: Pizzas, Pastas, Ensaladas
- **When** the user scrolls down to the Pastas section
- **Then** the "Pastas" category chip becomes active (highlighted)
- **And** the category chip bar scrolls to keep "Pastas" visible

### S7: Product Detail Modal
- **Given** the menu shows "Pizza Margherita" in the grid
- **When** the user taps the product card
- **Then** a bottom-sheet modal slides up
- **And** `GET /api/public/menu/buen-sabor-centro/product/10` is called
- **And** while loading, a skeleton is shown inside the modal
- **And** URL changes to `/buen-sabor/buen-sabor-centro/product/10`

### S8: Allergen Traffic-Light Display
- **Given** "Pizza Margherita" has allergens: gluten (contains, severe), dairy (contains, moderate), eggs (may_contain, low)
- **When** the product detail modal is open
- **Then** gluten shows with red background, "Contiene", "Severo"
- **And** dairy shows with red background, "Contiene", "Moderado"
- **And** eggs shows with yellow/amber background, "Puede contener", "Bajo"

### S9: Cross-Reaction Display
- **Given** "Pizza Margherita" contains gluten, and gluten has cross-reaction with celery (severity: low)
- **When** the product detail modal is open and user expands cross-reactions under gluten
- **Then** celery is listed with "Sensibilidad cruzada por profilinas", severity "Bajo"

### S10: Search with Debounce
- **Given** the menu is loaded with products: "Pizza Margherita", "Pizza Napolitana", "Steak"
- **When** the user types "piz" in the search bar
- **Then** after 300ms debounce, only "Pizza Margherita" and "Pizza Napolitana" are visible

### S11: Allergen Filter -- Strict Mode
- **Given** menu has: Pizza (contains gluten, may_contain eggs), Steak (free_of gluten), Salad (contains eggs)
- **When** user opens filter drawer, selects "Estricto" mode, and toggles "gluten"
- **Then** Pizza is hidden (contains gluten)
- **And** Steak and Salad are visible

### S12: Allergen Filter -- Very Strict Mode with Cross-Reactions
- **Given** menu has: Pizza (contains gluten), Soup (contains celery), Steak (free_of all)
- **And** gluten has cross-reaction with celery
- **When** user selects "Muy estricto" mode and toggles "gluten"
- **Then** Pizza is hidden (contains gluten), Soup is hidden (cross-reaction), Steak is visible

### S13: Dietary Filter (AND logic)
- **Given** menu has: Salad (vegan, gluten_free), Pasta (vegetarian), Steak (none)
- **When** user selects dietary filters: "vegan" AND "gluten_free"
- **Then** only Salad is visible

### S14: Cooking Method Filter (OR logic)
- **Given** menu has: Pizza (oven), Steak (grill), Sushi (raw), Pasta (boil, oven)
- **When** user selects cooking methods: "oven" and "grill"
- **Then** Pizza, Steak, and Pasta are visible; Sushi is hidden

### S15: Combined Filters
- **Given** menu has: Grilled Veggie Salad (vegetarian, grill, free_of gluten), Grilled Steak (grill, contains gluten), Veggie Pizza (vegetarian, oven, contains gluten)
- **When** user sets: allergen filter strict for "gluten", dietary "vegetarian", cooking "grill"
- **Then** only "Grilled Veggie Salad" is visible

### S16: i18n Auto-Detection
- **Given** the user's browser language is `pt-BR`
- **And** no language is stored in localStorage
- **When** the app loads
- **Then** the UI is displayed in Portuguese

### S17: i18n Manual Switch
- **Given** the app is in Spanish
- **When** the user taps the language selector and chooses US flag
- **Then** all UI text switches to English

### S18: PWA Install Prompt
- **Given** the user has been on the menu page for 30+ seconds
- **And** the app is not already installed
- **When** the 30s timer fires
- **Then** a custom install banner appears

### S19: PWA Offline Fallback
- **Given** the user has previously loaded the menu (cached)
- **And** the device goes offline
- **When** the user navigates within the app
- **Then** the app shell loads from precache and menu data from api-cache

### S20: Menu Cache Stale-While-Revalidate
- **Given** the user loaded the menu 6 minutes ago (cache expired)
- **When** they navigate back to the menu page
- **Then** stale data is shown immediately while background fetch runs

### S21: Bottom Bar Placeholder
- **Given** the user is on the menu page
- **When** they tap a bottom bar button
- **Then** a toast appears: "Proximamente"

### S22: Accessibility -- Focus Trap in Modal
- **Given** the product detail modal is open
- **When** the user presses Tab repeatedly
- **Then** focus cycles within the modal

### S23: Accessibility -- Touch Targets
- **Given** any interactive element
- **When** rendered on any screen size
- **Then** its tap target is at least 44x44px

### S24: Service Worker Update
- **Given** a new version is deployed
- **When** the service worker detects the update
- **Then** a toast with "Actualizar" button appears

### S25: Session Activity Sliding Window
- **Given** a user joined 7 hours ago, last activity 30 minutes ago
- **When** they reopen the app
- **Then** session remains active and lastActivity is updated

---

## Next Recommended
-> `sdd-design` (Folder structure, component tree, stores, routing, PWA config, i18n setup)
