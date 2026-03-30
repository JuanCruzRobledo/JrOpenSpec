---
sprint: 3
artifact: proposal
status: complete
---

# SDD Proposal: Sprint 3 — CRUD Base y Dashboard Shell

## Status: APPROVED

## Executive Summary

Sprint 3 delivers the admin dashboard foundation for "Buen Sabor" multi-tenant restaurant management. This includes: project scaffolding (React 19 + Vite 7.2 + TS 5.9 + Zustand 5 + TailwindCSS 4), JWT auth flow with proactive token refresh, hierarchical sidebar layout with branch selection, and basic CRUD operations for branches (sucursales), categories, subcategories, and products. The dashboard lives in `/dashboard/` as a standalone Vite app.

## Problem Statement

The admin dashboard is the primary interface for restaurant owners and managers. Without it, there is no way to manage restaurant configuration, branches, menus, or products. This sprint establishes the foundational shell that all future admin features will build upon — auth, layout, navigation, state management, and the CRUD pattern that will be reused across 15+ entity types.

## Proposed Solution

### 1. Project Setup
- Vite 7.2 with React 19.2 and TypeScript 5.9
- `babel-plugin-react-compiler` for automatic memoization (React 19 compiler)
- TailwindCSS 4 with custom theme (dark mode + orange accent #f97316)
- Zustand 5 with `persist` middleware for auth/UI state
- React Router for client-side routing with protected routes

### 2. Auth Flow
- Login screen -> POST /api/v1/auth/login -> JWT access (15min) + refresh (7day)
- Proactive token refresh at 14min (1min before expiry) via setTimeout
- BroadcastChannel API for cross-tab sync (logout propagation)
- Redirect to /login on 401 or expired token
- Auth state in Zustand store with persist (localStorage)

### 3. Layout Shell
- Sidebar: hierarchical navigation with collapsible groups, icons, active state highlighting
- Header: restaurant name, user avatar/menu, branch selector dropdown
- Branch selection is REQUIRED -- all CRUD operations are scoped to selected branch
- Dark theme (#0a0a0a background) with orange (#f97316) accent color
- Responsive: sidebar collapses on mobile

### 4. CRUD Pattern (reusable)
- Table view: paginated (10/page), sortable, filterable
- Create/Edit via modal dialogs
- Delete with destructive confirmation dialog
- Toast notifications for all operations (success/error/warning/info, max 5 stacked)
- Applied to: Sucursales, Categorias, Subcategorias, Productos

### 5. Entity-Specific Logic
- **Sucursales**: creating a branch auto-generates a "General" base category
- **Categorias**: auto-increment order field, emoji icon picker, cascading delete (subcategories + products)
- **Subcategorias**: parent category required, filterable by category
- **Productos**: category + optional subcategory, price in cents, featured/popular toggles

## Scope

### In Scope
- Dashboard Vite project scaffolding and config
- Auth flow (login, refresh, logout, tab sync)
- Dashboard layout (sidebar, header, branch selector)
- Restaurant configuration screen
- CRUD: Sucursales, Categorias, Subcategorias, Productos (basic)
- Toast notification system
- Destructive action confirmation dialogs
- Dark theme with orange accent

### Out of Scope
- Image upload (Sprint 4 -- S3/MinIO integration)
- Real-time updates via WebSocket (Sprint 5+)
- i18n (Sprint 6+)
- PWA capabilities / Workbox (Sprint 7+)
- Advanced product features (variants, combos, stock) -- future sprints
- Reports and analytics
- Role-based UI restrictions (RBAC UI -- Sprint 5)

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| React 19 infinite loops with Zustand destructuring | HIGH -- app crashes | Enforce individual selectors via ESLint rule + code review pattern |
| babel-plugin-react-compiler incompatibilities | MEDIUM -- perf degradation | Can disable per-component with `'use no memo'` directive |
| Token refresh race conditions | MEDIUM -- auth failures | Single refresh promise pattern (deduplicate concurrent refresh calls) |
| BroadcastChannel not supported in older browsers | LOW -- logout won't sync | Fallback to localStorage event listener |
| Cascading deletes data loss | HIGH -- irreversible | Confirmation dialog with entity count, soft-delete at DB level |

## Success Criteria

1. User can log in, see dashboard, and be redirected on token expiry
2. Token refreshes proactively at 14min without user noticing
3. Logging out in one tab logs out all tabs
4. User can select a branch and all CRUD operations scope to it
5. Full CRUD lifecycle works for sucursales, categorias, subcategorias, productos
6. Cascading deletes show confirmation with affected entity count
7. Toast notifications appear for all operations
8. Dark theme renders correctly with orange accent

## Dependencies

- Backend API endpoints for auth (POST /login, POST /refresh, POST /logout)
- Backend CRUD endpoints for sucursales, categorias, subcategorias, productos
- Backend must return tenant-scoped data based on JWT claims
- PostgreSQL database with schema from Sprint 1-2

## Next Recommended

`sdd-spec` -- Detailed specification with API contracts, component states, and Given/When/Then scenarios.
