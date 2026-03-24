---
sprint: 15
artifact: design
status: complete
---

# Design: PWA Polish, Accesibilidad e i18n

## Architecture Decisions

### AD-1: Workbox with vite-plugin-pwa
- **Decision**: Use `vite-plugin-pwa` (wraps Workbox) for service worker generation in all 3 PWAs.
- **Rationale**: Integrates with Vite build pipeline, auto-generates precache manifest, supports runtime caching strategies via config.
- **Tradeoff**: Less control than raw Workbox — mitigated by custom service worker injection for advanced offline logic.

### AD-2: i18next for i18n
- **Decision**: Use `i18next` + `react-i18next` for pwaMenu internationalization.
- **Rationale**: Industry standard, supports pluralization, interpolation, lazy loading of locale files, TypeScript support. ~12KB gzipped.
- **Tradeoff**: Additional dependency — justified by the complexity of proper i18n handling.

### AD-3: CSS-only Animations with prefers-reduced-motion
- **Decision**: All animations via CSS (no JS animation libraries). `@media (prefers-reduced-motion: reduce)` overrides all animations to `none`.
- **Rationale**: CSS animations are GPU-accelerated, performant, and the reduced-motion media query is the standard accessibility approach.
- **Tradeoff**: Cannot do complex physics-based animations — acceptable for a business app.

### AD-4: Import as Atomic Transaction with Pre-backup
- **Decision**: Import creates a backup snapshot first, then clears + imports in a single DB transaction.
- **Rationale**: Atomic import ensures no partial state. Backup enables recovery if the imported data is incorrect.
- **Tradeoff**: Double write (backup + import) — acceptable since imports are infrequent.

### AD-5: Help Content as Static JSON
- **Decision**: Store help content in `help/{screenId}.json` files, loaded on demand.
- **Rationale**: Separates content from code. Non-developers can edit help text. Lazy-loaded to avoid bloating the bundle.
- **Tradeoff**: Extra network request for help — mitigated by CacheFirst strategy.

## File Structure

### Workbox Configuration
```
pwaMenu/vite.config.ts                # VitePWA plugin config
pwaMenu/src/sw-custom.ts              # Custom SW logic (menu cache, update check)

pwaWaiter/vite.config.ts              # VitePWA plugin config
pwaWaiter/src/sw-custom.ts            # Custom SW logic (table cache)

dashboard/vite.config.ts              # VitePWA plugin config (minimal)
```

### pwaMenu Offline Enhancements
```
pwaMenu/src/
├── offline/
│   ├── MenuCache.ts                  # IndexedDB menu cache manager
│   ├── OfflineCart.ts                # Cart operations without network
│   ├── UpdateChecker.ts             # Hourly HEAD request + banner logic
│   └── components/
│       ├── UpdateBanner.tsx          # "Nueva versin disponible"
│       └── OfflineIndicator.tsx     # Offline mode indicator
```

### Accessibility Additions (all PWAs)
```
shared/
├── accessibility/
│   ├── FocusTrap.tsx                 # Reusable focus trap wrapper
│   ├── SkipToContent.tsx             # Skip link component
│   ├── AriaLive.tsx                  # Live region wrapper
│   ├── hooks/
│   │   ├── useFocusTrap.ts           # Focus trap hook
│   │   ├── useKeyboardNavigation.ts  # Tab/Shift-Tab/ESC handling
│   │   └── useAnnounce.ts           # Screen reader announcements
│   └── utils/
│       └── contrastChecker.ts        # Runtime contrast validation (dev only)
```

### i18n Setup (pwaMenu)
```
pwaMenu/src/
├── i18n/
│   ├── index.ts                      # i18next initialization
│   ├── locales/
│   │   ├── es-AR.json                # Spanish (Argentina) — default
│   │   └── en.json                   # English (future)
│   ├── hooks/
│   │   └── useTranslation.ts         # Wrapper hook
│   └── utils/
│       ├── formatCurrency.ts         # Locale-aware currency
│       └── formatDate.ts             # Locale-aware dates
```

### Import/Export (Dashboard)
```
dashboard/src/
├── import-export/
│   ├── pages/
│   │   └── ImportExportPage.tsx
│   ├── components/
│   │   ├── ExportButton.tsx          # Trigger export download
│   │   ├── ImportUpload.tsx          # File upload + validation
│   │   ├── ImportPreview.tsx         # Summary before apply
│   │   └── ImportConfirm.tsx        # Confirmation dialog
│   ├── services/
│   │   └── importExportService.ts
│   └── schemas/
│       └── exportSchema.ts          # JSON schema validation (Zod)
```

### Help System (Dashboard)
```
dashboard/src/
├── help/
│   ├── components/
│   │   ├── HelpButton.tsx           # (?) button
│   │   └── HelpPanel.tsx            # Slide-out panel
│   ├── content/                     # Static JSON files
│   │   ├── products.json
│   │   ├── categories.json
│   │   ├── statistics.json
│   │   ├── orders.json
│   │   ├── promotions.json
│   │   ├── recipes.json
│   │   ├── ingredients.json
│   │   └── audit.json
│   └── hooks/
│       └── useHelp.ts               # Load + display help
```

### Toast System (shared)
```
shared/
├── toasts/
│   ├── ToastContainer.tsx           # Max 5, stacking, positioning
│   ├── Toast.tsx                    # Individual toast with icon + action
│   ├── toastStore.ts               # Queue management
│   └── types.ts                    # ToastConfig type
```

### Animation System
```
shared/
├── animations/
│   ├── animations.css               # All @keyframes + utility classes
│   ├── modal-transition.css         # Modal open/close
│   ├── button-feedback.css          # Button press
│   ├── celebration.css              # Order success
│   └── reduced-motion.css           # @media prefers-reduced-motion overrides
```

## Workbox Configuration Details

### pwaMenu — vite.config.ts
```typescript
VitePWA({
  strategies: 'injectManifest',
  srcDir: 'src',
  filename: 'sw-custom.ts',
  registerType: 'prompt',               // prompt user for updates
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
    runtimeCaching: [
      {
        urlPattern: /\/api\//,
        handler: 'NetworkFirst',
        options: { networkTimeoutSeconds: 5, cacheName: 'api-cache', expiration: { maxEntries: 100 } }
      },
      {
        urlPattern: /\.(png|jpg|jpeg|webp|gif)$/,
        handler: 'CacheFirst',
        options: { cacheName: 'images', expiration: { maxEntries: 200, maxAgeSeconds: 30 * 24 * 60 * 60 } }
      },
      {
        urlPattern: /\.(woff2?|ttf|otf)$/,
        handler: 'CacheFirst',
        options: { cacheName: 'fonts', expiration: { maxAgeSeconds: 365 * 24 * 60 * 60 } }
      }
    ]
  }
})
```

### pwaWaiter — vite.config.ts
```typescript
VitePWA({
  strategies: 'injectManifest',
  registerType: 'autoUpdate',            // auto-update for waiter (critical)
  workbox: {
    runtimeCaching: [
      {
        urlPattern: /\/api\/branches\/.*\/tables/,
        handler: 'NetworkFirst',
        options: { networkTimeoutSeconds: 3, cacheName: 'tables-cache', expiration: { maxAgeSeconds: 3600 } }
      },
      {
        urlPattern: /\.(png|jpg|jpeg|webp)$/,
        handler: 'CacheFirst',
        options: { cacheName: 'images', expiration: { maxEntries: 100, maxAgeSeconds: 7 * 24 * 60 * 60 } }
      },
      {
        urlPattern: /\.(woff2?|ttf|otf)$/,
        handler: 'CacheFirst',
        options: { cacheName: 'fonts', expiration: { maxAgeSeconds: 365 * 24 * 60 * 60 } }
      }
    ]
  }
})
```

## Component Trees

### Toast System
```
<ToastContainer position="bottom-right">
  ├── <Toast type="success" message="Pedido enviado" autoClose={5000} />
  ├── <Toast type="error" message="Error de conexin" persistent />
  ├── <Toast type="info" message="Mesa actualizada" autoClose={5000} />
  └── ... (max 5)
</ToastContainer>

<!-- aria-live region (invisible) -->
<AriaLive>
  <div role="status" aria-live="polite">{normalAnnouncements}</div>
  <div role="alert" aria-live="assertive">{urgentAnnouncements}</div>
</AriaLive>
```

### Import/Export Page
```
<ImportExportPage>
  ├── <ExportSection>
  │   ├── <ExportDescription text="Descargar datos del restaurante..." />
  │   └── <ExportButton onClick={downloadExport} />
  └── <ImportSection>
      ├── <ImportUpload onFile={handleFile} maxSize={5MB} />
      ├── [after upload] <ImportPreview summary={} warnings={} />
      └── [on confirm] <ImportConfirm onConfirm={applyImport} onCancel={cancel} />
```

## Sequence Diagrams

### Menu Update Check
```
pwaMenu         UpdateChecker      ServiceWorker    Server
  |                |                  |                |
  |  [every 1h]--->|                  |                |
  |                |--HEAD /api/menu->|                |
  |                |                  |--HEAD--------->|
  |                |                  |<--200 ETag-----|
  |                |--compare ETags-->|                |
  |                |  [different]     |                |
  |                |--show banner---->|                |
  |<--"Nueva versin disponible"      |                |
  |                |                  |                |
  |--tap "Actualizar"                 |                |
  |                |--full fetch----->|                |
  |                |                  |--GET /menu---->|
  |                |                  |<--200 [data]---|
  |                |--update IDB----->|                |
  |                |--hide banner---->|                |
  |<--menu refreshed                  |                |
```

### Import Flow
```
Admin           Dashboard         API              DB
  |                |                |                |
  |--select file-->|                |                |
  |                |--POST /import?preview=true----->|
  |                |                |--validate JSON |
  |                |                |--count entities|
  |                |<--200 {preview}|                |
  |                |--show preview->|                |
  |<--"12 cats, 85 prods"           |                |
  |                |                |                |
  |--confirm------>|                |                |
  |                |--POST /import?preview=false---->|
  |                |                |--BEGIN TX----->|
  |                |                |--backup snapshot
  |                |                |--clear branch data
  |                |                |--insert categories
  |                |                |--insert products
  |                |                |--COMMIT------->|
  |                |                |--clean caches  |
  |                |<--200 {imported}|               |
  |<--success toast|                |                |
```

## Accessibility Checklist

| Check | pwaMenu | pwaWaiter | Dashboard |
|-------|---------|-----------|-----------|
| Skip to content link | Required | Required | Required |
| ARIA roles on landmarks | Required | Required | Required |
| Focus trap on modals | Required | Required | Required |
| ESC closes modal | Required | Required | Required |
| Tab navigation complete | Required | Required | Required |
| 44x44px touch targets | Required | Required | N/A (desktop) |
| Contrast ratio 4.5:1 | Required | Required | Required |
| rem-based typography | Required | Required | Required |
| alt text on images | Required | Required | Required |
| Form label association | Required | Required | Required |
| aria-live for toasts | Required | Required | Required |
| aria-describedby errors | Required | Required | Required |
| 200% zoom no h-scroll | Required | Required | Required |
