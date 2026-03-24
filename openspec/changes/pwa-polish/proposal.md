---
sprint: 15
artifact: proposal
status: complete
---

# Proposal: PWA Polish, Accesibilidad e i18n

## Intent

Elevate all three PWAs (pwaMenu, pwaWaiter, Dashboard) to production-quality standards with refined caching strategies, full WCAG 2.1 AA accessibility, complete i18n coverage for pwaMenu, import/export functionality, contextual help, polished toast notifications, and smooth animations.

## Scope

### In Scope
- Workbox caching strategies per PWA: pwaMenu (CacheFirst 30d images, NetworkFirst 5s APIs, 1y fonts), pwaWaiter (7d images, 1h tables, 1y fonts), Dashboard (NetworkFirst all)
- Advanced offline for pwaMenu: local menu, offline cart, OfflineQueue replay, offline payment success page, hourly update checks + banner
- WCAG 2.1 AA compliance in all 3 PWAs: ARIA semantics, focus traps on modals, keyboard tab navigation, ESC close, 44x44px touch targets, verified contrast ratios, scalable typography, skip-to-content links
- Complete i18n in pwaMenu: all user-facing strings via `t()` function
- Dashboard import/export JSON: export restaurant + categories + products + timestamp, import with validation (max 5MB), cache cleanup, state reset
- Contextual help: (?) button per Dashboard screen
- Toast refinements: max 5 visible, urgent persist, 5s auto-close
- Animations: modals 200ms fade/scale, buttons 200ms feedback, loading spinner, order success celebration

### Out of Scope
- Multi-language for pwaWaiter and Dashboard (future)
- WCAG AAA compliance
- RTL language support
- Dark mode
- A/B testing framework

## Modules

| Module | Description |
|--------|-------------|
| `workbox-config` | Per-PWA Workbox caching strategies |
| `offline-menu` | Advanced pwaMenu offline capabilities |
| `accessibility` | WCAG 2.1 AA compliance across all PWAs |
| `i18n` | pwaMenu internationalization framework |
| `import-export` | Dashboard data import/export JSON |
| `help-system` | Contextual help per screen |
| `toasts` | Refined notification system |
| `animations` | Production-quality UI animations |

## Approach

1. **Workbox configuration** per PWA with differentiated caching strategies
2. **pwaMenu offline** enhancements: cached menu, offline cart, queue replay, update checks
3. **Accessibility audit** and remediation across all 3 PWAs
4. **i18n setup** with extraction of all pwaMenu strings into translation files
5. **Import/export** for Dashboard with JSON schema validation
6. **Help system** with per-screen contextual content
7. **Toast refinements** across all PWAs
8. **Animation polish** for production feel

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Stale cache causing incorrect menu/prices | High — wrong orders | NetworkFirst for APIs with 5s timeout; hourly update check; manual refresh available |
| i18n missing translations causing blank strings | Medium — broken UI | Fallback to Spanish (default); automated string extraction; CI check for missing keys |
| Accessibility fixes breaking existing UI layout | Medium — visual regression | Visual regression testing with screenshots; incremental fixes with review |
| Import validation too strict/lenient | Medium — data corruption or rejection | Strict JSON schema validation; preview before import; backup before overwrite |
| Animation jank on low-end devices | Low — poor UX | Use CSS animations + will-change hints; respect prefers-reduced-motion |

## Rollback

- Workbox config changes: revert to previous service worker version; force update via `skipWaiting()`
- Accessibility: CSS/ARIA additions are non-breaking; removal restores original behavior
- i18n: fallback to Spanish hardcoded strings always works
- Import/export: new feature; removal just removes Dashboard page
- Animations: controlled via CSS; removal restores default browser behavior
