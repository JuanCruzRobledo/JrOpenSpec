---
sprint: 15
artifact: spec
status: complete
---

# Spec: PWA Polish, Accesibilidad e i18n

## Requirements (RFC 2119)

### Workbox Caching Strategies

#### pwaMenu
- Images MUST use CacheFirst strategy with max-age 30 days, max 200 entries
- API responses MUST use NetworkFirst strategy with 5-second network timeout
- Fonts MUST use CacheFirst strategy with max-age 1 year
- Navigation routes MUST use NetworkFirst with offline fallback page
- The service worker MUST precache the app shell (HTML, CSS, JS bundles)

#### pwaWaiter
- Images MUST use CacheFirst strategy with max-age 7 days, max 100 entries
- Table data (GET /api/branches/{id}/tables) MUST use NetworkFirst with 1-hour cache fallback
- Fonts MUST use CacheFirst strategy with max-age 1 year
- API mutations (POST, PUT, PATCH, DELETE) MUST NOT be cached

#### Dashboard
- All requests MUST use NetworkFirst strategy (always prefer fresh data)
- Static assets MUST use CacheFirst for performance
- The Dashboard SHOULD NOT serve stale data for any API endpoint

### Advanced Offline — pwaMenu
- The app MUST cache the full menu (categories + products) in IndexedDB on first load
- When offline, the menu MUST be served from IndexedDB
- The cart MUST function fully offline (add, remove, update quantities)
- Order submissions while offline MUST be queued in OfflineQueue and replayed on reconnection
- After successful payment while offline connectivity returns, the app MUST show the success page from cache
- The app MUST check for menu updates every hour via a lightweight HEAD request
- If updates are available, a banner MUST appear: "Hay una nueva versin del men disponible" with a refresh button
- The update check MUST NOT interrupt the user's current flow (non-blocking)

### WCAG 2.1 AA — All 3 PWAs
- All interactive elements MUST have appropriate ARIA roles and labels
- All modals MUST implement focus traps: focus stays within modal when open, restores to trigger on close
- The entire app MUST be navigable via Tab key (forward) and Shift+Tab (backward)
- ESC key MUST close the topmost modal/overlay
- All touch/click targets MUST be at least 44x44 pixels
- Color contrast MUST meet WCAG AA ratios: 4.5:1 for normal text, 3:1 for large text
- Typography MUST be scalable: base font 16px, all sizes in rem units, zoom to 200% without horizontal scroll
- Each PWA MUST include a "Skip to main content" link as the first focusable element
- Form inputs MUST have visible labels (not just placeholders)
- Error messages MUST be associated with inputs via `aria-describedby`
- Status changes (toasts, alerts) MUST use `aria-live` regions
- Images MUST have descriptive `alt` text; decorative images MUST have `alt=""`

### i18n — pwaMenu
- ALL user-facing strings in pwaMenu MUST use the `t()` translation function
- Default language MUST be Spanish (es-AR)
- Translation files MUST be JSON format: `locales/{lang}.json`
- The system MUST support future languages without code changes (add JSON file only)
- String keys MUST follow dot notation: `menu.categories.title`, `cart.empty`, `order.success`
- Pluralization MUST be supported: `t('cart.items', { count: 3 })` → "3 tems"
- Number/currency formatting MUST respect locale: `formatCurrency(15400)` → "$15.400,00" for es-AR
- Date formatting MUST respect locale: `formatDate(date)` → "19 de marzo de 2026"

### Import/Export — Dashboard
- The Dashboard MUST provide an "Exportar" button that downloads a JSON file containing:
  - Restaurant configuration
  - All categories with hierarchy
  - All products with full details
  - Export timestamp and version
- The JSON MUST follow a documented schema with a version field
- The Dashboard MUST provide an "Importar" button that:
  - Accepts a JSON file upload (max 5MB)
  - Validates the JSON against the expected schema
  - Shows a preview of what will be imported (counts: X categories, Y products)
  - Requires confirmation before applying
  - On apply: clears existing data for the branch, imports new data, cleans caches
- The import MUST be atomic (all-or-nothing transaction)
- The system MUST create a backup snapshot before import (for recovery)

### Contextual Help — Dashboard
- Each Dashboard screen MUST have a (?) help button in the top-right area
- Clicking (?) MUST open a help panel/modal with:
  - Screen title and description
  - Key actions explained
  - Tips and best practices
- Help content MUST be stored as static JSON/markdown, not hardcoded in components
- The help panel MUST be dismissible via X, ESC, or backdrop click

### Toast Refinements
- Maximum 5 toasts visible simultaneously (oldest auto-dismissed when 6th arrives)
- Urgent toasts (errors, payment confirmations) MUST persist until manually dismissed
- Normal toasts MUST auto-close after 5 seconds
- Toasts MUST stack vertically from bottom-right (desktop) or bottom-center (mobile)
- Each toast MUST include: icon (success/error/warning/info), message, optional action button, close button
- Toasts MUST use `aria-live="polite"` for normal, `aria-live="assertive"` for urgent

### Animations
- Modal open/close: 200ms fade + scale (0.95 → 1.0) transition
- Button press: 200ms scale (0.97) + opacity (0.8) feedback
- Loading states: CSS spinner animation (no JS)
- Order success: celebration animation (confetti or checkmark expand)
- All animations MUST respect `prefers-reduced-motion` media query (reduce to instant transitions)
- Animations MUST use CSS transforms and opacity only (GPU-accelerated, no layout triggers)

## Data Models

### ExportPayload
```typescript
interface ExportPayload {
  version: string;                    // "1.0"
  exportedAt: string;                 // ISO 8601
  branchId: string;
  branchName: string;
  restaurant: {
    name: string;
    logo: string;
    // ...restaurant config
  };
  categories: ExportCategory[];
  products: ExportProduct[];
}

interface ExportCategory {
  id: string;
  name: string;
  parentId: string | null;
  displayOrder: number;
  imageUrl: string | null;
}

interface ExportProduct {
  id: string;
  name: string;
  description: string;
  categoryId: string;
  price: number;
  imageUrl: string | null;
  state: string;
  // ...all product fields
}
```

### i18n Translation Structure
```json
{
  "menu": {
    "title": "Men",
    "categories": { "title": "Categoras", "all": "Todas" },
    "search": { "placeholder": "Buscar productos...", "noResults": "No se encontraron resultados" }
  },
  "cart": {
    "title": "Tu Pedido",
    "empty": "Tu carrito est vaco",
    "items": "{{count}} tem",
    "items_plural": "{{count}} tems",
    "total": "Total",
    "submit": "Enviar Pedido"
  },
  "order": {
    "success": "Pedido enviado exitosamente!",
    "error": "Error al enviar el pedido",
    "round": "Ronda {{number}}"
  },
  "common": {
    "loading": "Cargando...",
    "retry": "Reintentar",
    "cancel": "Cancelar",
    "confirm": "Confirmar",
    "close": "Cerrar",
    "back": "Volver"
  }
}
```

### HelpContent
```typescript
interface HelpContent {
  screenId: string;                   // e.g., "products", "statistics"
  title: string;
  description: string;
  actions: { name: string; description: string }[];
  tips: string[];
}
```

## API Contracts

### POST /api/branches/{branchId}/export
**Auth**: Bearer JWT (role: ADMIN)
**Response 200**: `Content-Type: application/json`, `Content-Disposition: attachment; filename="export-{branch}-{date}.json"`
```json
{
  "version": "1.0",
  "exportedAt": "ISO8601",
  "branchId": "uuid",
  "branchName": "Sucursal Centro",
  "restaurant": { ... },
  "categories": [ ... ],
  "products": [ ... ]
}
```

### POST /api/branches/{branchId}/import
**Auth**: Bearer JWT (role: ADMIN)
**Request**: `Content-Type: multipart/form-data`, field "file" with JSON
**Response 200** (preview mode — `?preview=true`):
```json
{
  "valid": true,
  "summary": {
    "categories": 12,
    "products": 85,
    "version": "1.0"
  },
  "warnings": ["2 products reference non-existent categories"]
}
```
**Response 200** (apply mode — `?preview=false`):
```json
{
  "imported": true,
  "categoriesImported": 12,
  "productsImported": 85,
  "backupId": "uuid"
}
```
**Response 400**: Invalid JSON or schema validation failure
**Response 413**: File exceeds 5MB

## Scenarios

### Scenario: Offline menu browsing
```
Given the diner has loaded pwaMenu at least once (menu cached in IndexedDB)
When the diner's device loses network connectivity
Then the menu continues to display from IndexedDB cache
And the diner can browse categories and view products
And the diner can add items to cart
When the diner submits the order
Then the order is queued in OfflineQueue
And a toast shows "Pedido en cola - Se enviar al recuperar conexin"
```

### Scenario: Menu update check
```
Given the diner has been browsing the menu for 1 hour
When the hourly update check fires
And the HEAD request indicates the menu has changed
Then a banner appears at the top: "Hay una nueva versin del men"
And a "Actualizar" button is shown
When the diner taps "Actualizar"
Then the menu refreshes from the network
And the IndexedDB cache is updated
And the banner disappears
```

### Scenario: Keyboard navigation through modal
```
Given a modal is open (e.g., product detail)
When the user presses Tab
Then focus moves to the next focusable element WITHIN the modal
When focus reaches the last element and Tab is pressed again
Then focus wraps to the first focusable element in the modal
When the user presses Shift+Tab on the first element
Then focus wraps to the last element
When the user presses ESC
Then the modal closes
And focus returns to the element that triggered the modal
```

### Scenario: Dashboard data import
```
Given the admin opens the Import/Export page
When the admin clicks "Importar" and selects a 3MB JSON file
Then the file is uploaded with preview=true
And the preview shows: "12 categoras, 85 productos - Versin 1.0"
And a warning shows: "Esta accin reemplazar los datos existentes"
When the admin clicks "Confirmar Importacin"
Then a backup snapshot is created
And existing branch data is cleared
And new categories and products are imported atomically
And caches are cleaned
And a success toast shows "Importacin exitosa: 12 categoras, 85 productos"
```

### Scenario: Toast queue management
```
Given 5 toasts are currently visible
When a 6th toast is triggered
Then the oldest (bottom) toast is auto-dismissed
And the 6th toast appears at the top of the stack
When an urgent toast (error) is triggered
Then it appears with a red accent and no auto-close timer
And it remains visible until the user clicks the close button
```

### Scenario: Reduced motion preference
```
Given the user has enabled "Reduce motion" in OS settings
When a modal opens
Then it appears instantly (no fade/scale animation)
When a button is pressed
Then there is no scale animation, just color change
When an order succeeds
Then the success indicator appears without celebration animation
```
