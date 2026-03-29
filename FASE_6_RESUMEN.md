# Fase 6 — pwa-menu-base: Resumen de Implementación

**Fecha**: 2026-03-29
**Branch**: `mati`
**Estado**: `apply: done` — listo para `/sdd-verify`

---

## Descripción

PWA del menú orientada al cliente (`pwa_menu/`). Los clientes escanean un QR en su mesa, ingresan con nombre + color de avatar (sin cuenta, sin contraseña), y pueden navegar el menú con filtros de alérgenos, preferencias dietéticas y métodos de cocción. Soporta instalación como PWA, offline fallback, y 3 idiomas.

---

## Scope implementado

| Área | Detalle |
|------|---------|
| Scaffolding | Vite 7.2 + React 19.2 + TypeScript 5.9 strict + TailwindCSS 4 (`@theme`) + pnpm |
| React Compiler | `babel-plugin-react-compiler` activo en Vite |
| Estado | Zustand 5 — 6 stores con persist selectivo |
| i18n | es/en/pt — 5 namespaces, lazy loading, type-safe keys |
| PWA | vite-plugin-pwa + Workbox — CacheFirst images, NetworkFirst API, SPA fallback |
| Sesión | QR → HMAC token 3h + localStorage 8h sliding window |
| Menú | 3 niveles: categoría → subcategoría → producto |
| Navegación | Category tabs con IntersectionObserver sync |
| Filtros | Alérgenos (off/strict/very_strict + cross-reactions), dietético (AND), cocción (OR) |
| Búsqueda | Client-side, debounce 300ms, accent-insensitive |
| Detalle producto | Modal bottom-sheet con tráfico de luz alérgenos + ingredientes + cross-reactions |
| Accesibilidad | ARIA labels, touch targets 44px, focus trap, semántica HTML, prefers-reduced-motion |
| Bottom bar | 3 FABs placeholder (mozo, historial, cuenta) |
| Backend | `POST /api/sessions/join` — HMAC-SHA256, validación branch/table, 404/409 |

### Fuera de scope (fases futuras)
- Carrito / pedidos (Phase 8)
- Llamar al mozo funcional (Phase 9)
- Historial y cuenta (Phase 10-11)
- WebSocket real-time (Phase 7)
- Push notifications

---

## Arquitectura frontend

```
pwa_menu/src/
├── config/         constants.ts, pwa.ts
├── i18n/           index.ts, types.ts, locales/es|en|pt (5 namespaces c/u)
├── types/          menu.ts, product-detail.ts, session.ts, filters.ts, allergen-catalog.ts, api.ts
├── services/       api-client.ts, session.service.ts, menu.service.ts, allergen.service.ts
├── stores/         session, menu, filter, allergen-catalog, product-detail, ui
├── hooks/          useSessionGuard, useActivityTracker, useMenuData, useFilteredProducts,
│                   useCategoryScroll, useDebounce, useFocusTrap, usePWAInstall, useSWUpdate,
│                   useProductDetail
├── lib/            cn.ts, format.ts, text.ts, filter-engine.ts
├── router/         index.tsx, routes.ts, SessionGuard.tsx
├── layouts/        LandingLayout.tsx, MenuLayout.tsx
└── components/
    ├── ui/         Button, Input, Chip, Skeleton, Toast, ToastContainer, Badge, SealBadge,
    │               Modal, Drawer, InstallBanner, OfflineIndicator
    ├── session/    LandingPage, BranchHeader, NameInput, ColorPalette, JoinButton
    ├── layout/     MenuHeader, LanguageSelector, BottomBar, BottomBarButton
    ├── menu/       MenuPage, CategoryTabs, SearchBar, ProductCard, ProductGrid,
    │               SubcategorySection, CategorySection, EmptyState, MenuSkeleton
    ├── product-detail/ ProductDetailModal, ProductImageGallery, ProductInfo, ProductBadges,
    │               AllergenEntry, CrossReactionList, AllergenList, IngredientList,
    │               DietaryProfileList, CookingMethodList, FlavorTextureSection, ProductDetailSkeleton
    ├── filters/    FilterDrawer, AllergenModeSelector, FilterChip, AllergenFilterSection,
    │               DietaryFilterSection, CookingFilterSection, ClearFiltersButton
    └── pwa/        UpdateToast
```

**Total**: ~123 archivos

---

## Stores Zustand

| Store | Persist | Key localStorage | TTL / Notas |
|-------|---------|-----------------|-------------|
| `session.store` | ✅ | `buen-sabor-session` | 8h inactividad sliding window |
| `menu.store` | ✅ | `buen-sabor-menu-cache` | 5min TTL, stale-while-revalidate |
| `filter.store` | ❌ | — | Auto-sets 'strict' al seleccionar alérgenos sin modo |
| `allergen-catalog.store` | ❌ | — | 5min TTL, mapa bidireccional cross-reactions |
| `product-detail.store` | ❌ | — | Modal state |
| `ui.store` | ❌ | — | Toasts auto-remove 4s, max 5 |

---

## Routing

```
/:tenant/:branch/mesa/:table      → LandingLayout > LandingPage
/:tenant/:branch                  → SessionGuard > MenuLayout > MenuPage
/:tenant/:branch/product/:id      → SessionGuard > MenuLayout > MenuPage (modal overlay)
```

---

## Workbox — Caching Strategies

| Estrategia | Recursos | TTL | Cache Name |
|------------|----------|-----|-----------|
| CacheFirst | Imágenes (png, jpg, webp, CDN) | 30 días, max 200 | `images-cache` |
| NetworkFirst | `/api/public/*` (timeout 5s) | 1 día, max 50 | `api-cache` |
| StaleWhileRevalidate | Fuentes (woff2, ttf) | 365 días, max 20 | `fonts-cache` |
| Precache | App shell (HTML, JS, CSS) | Build hash | vite-plugin-pwa |

---

## Backend — Endpoint nuevo

```
POST /api/sessions/join
```

| Archivo | Descripción |
|---------|-------------|
| `rest_api/app/routers/public/session_router.py` | Router thin — solo validación + service call |
| `rest_api/app/services/domain/session_service.py` | Lógica: valida branch/table, genera HMAC token |
| `rest_api/app/schemas/session.py` | Pydantic schemas request/response |

**Token**: `HMAC-SHA256(branch_id:table_id:session_id:created_at_unix, SERVER_SECRET)` — expira en 3h.
**Errores**: 404 si branch/table no existe, 409 si table inactiva.

---

## Algoritmo de filtrado

```typescript
// Ubicación: pwa_menu/src/lib/filter-engine.ts
filterProducts(products, search, allergenFilter, dietaryFilter, cookingFilter, crossReactionMap)

// 1. Search: accent-insensitive + case-insensitive en name + shortDescription
// 2. Allergen strict: oculta si contains algún allergen seleccionado
// 3. Allergen very_strict: expande con cross-reactions, oculta contains + may_contain
// 4. Dietary: AND — el producto debe tener TODOS los perfiles seleccionados
// 5. Cooking: OR — el producto debe tener AL MENOS UNO de los métodos seleccionados
```

---

## Convenciones aplicadas

- **Zustand**: siempre `const value = useStore(selectValue)` — nunca `const { value } = useStore()`
- **Precios**: `backendCents / 100` para display, `Math.round(price * 100)` para backend
- **IDs**: BigInteger backend / string frontend
- **i18n**: cero strings hardcodeadas — todo via `t()`
- **Imágenes**: `loading="lazy"` + Skeleton placeholder
- **TailwindCSS 4**: `@theme` en CSS, sin `tailwind.config.ts`

---

## Issues conocidos / Pendientes antes de deploy

| Issue | Severidad | Acción |
|-------|-----------|--------|
| PNG icons son 0-byte placeholders | Media | Generar con ImageMagick o PWA icon generator (192×192 + 512×512, fondo `#f97316`) |
| `sessionId` usa `table.id` temporalmente | Baja | Se reemplaza con entidad `TableSession` real en Phase 9 (`table-staff-domain`) |
| `pnpm install` no ejecutado aún | Alta | Correr `cd pwa_menu && pnpm install` antes de levantar |

---

## Dependencias de fases

```
✅ Phase 4 (menu-domain)
  └─→ ✅ Phase 6 (pwa-menu-base)  ← esta fase
        └─→ ⬜ Phase 7 (realtime-infra)  ← próxima
```

---

## Próximos pasos

```bash
# 1. Verificar implementación
/sdd-verify "pwa-menu-base"

# 2. Instalar dependencias frontend
cd pwa_menu && pnpm install

# 3. Levantar para prueba local
docker-compose up -d
cd pwa_menu && pnpm dev   # → http://localhost:5176

# 4. Una vez verificado, arrancar Phase 7
/sdd-new "realtime-infra"
```
