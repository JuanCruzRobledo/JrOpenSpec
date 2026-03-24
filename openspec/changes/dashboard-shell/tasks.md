---
sprint: 3
artifact: tasks
status: complete
---

# SDD Tasks: Sprint 3 — CRUD Base y Dashboard Shell

## Status: APPROVED

---

## Phase 1: Project Scaffolding & Configuration

### Task 1.1: Initialize Vite Project
**Files to create:**
- `dashboard/package.json`
- `dashboard/tsconfig.json`
- `dashboard/tsconfig.app.json`
- `dashboard/tsconfig.node.json`
- `dashboard/vite.config.ts`
- `dashboard/index.html`
- `dashboard/src/main.tsx`
- `dashboard/src/App.tsx`
- `dashboard/src/vite-env.d.ts`
- `dashboard/.env.example`
- `dashboard/.gitignore`

**Acceptance Criteria:**
- [ ] Vite 7.2 scaffolded with React 19.2 and TypeScript 5.9
- [ ] `babel-plugin-react-compiler` configured in vite.config.ts as a Babel plugin
- [ ] `npm run dev` starts the dev server on port 5173 (or configurable)
- [ ] `npm run build` produces a production build without errors
- [ ] TypeScript strict mode enabled
- [ ] Path aliases configured: `@/` -> `src/`

**Dependencies to install:**
```
react@19.2 react-dom@19.2 react-router@7 zustand@5 axios
@tailwindcss/vite tailwindcss@4 clsx tailwind-merge
babel-plugin-react-compiler (devDep)
@types/react @types/react-dom typescript@5.9 vite@7.2 @vitejs/plugin-react (devDeps)
```

### Task 1.2: TailwindCSS 4 Theme Setup
**Files to create/edit:**
- `dashboard/src/index.css`
- `dashboard/postcss.config.js` (if needed by TW4)

**Acceptance Criteria:**
- [ ] TailwindCSS 4 configured with `@tailwindcss/vite` plugin in vite.config.ts
- [ ] `@theme` block in index.css defines all custom colors
- [ ] Font family set to Inter (with system-ui fallback)
- [ ] Dark theme is the DEFAULT and ONLY theme (no toggle needed)
- [ ] Body element has `bg-bg-primary text-text-primary` applied

### Task 1.3: Constants and Type Definitions
**Files to create:**
- `dashboard/src/config/constants.ts`
- `dashboard/src/types/auth.ts`
- `dashboard/src/types/restaurant.ts`
- `dashboard/src/types/branch.ts`
- `dashboard/src/types/category.ts`
- `dashboard/src/types/subcategory.ts`
- `dashboard/src/types/product.ts`
- `dashboard/src/types/api.ts`
- `dashboard/src/types/ui.ts`

**Acceptance Criteria:**
- [ ] `constants.ts` exports: `API_URL` (from env), `TOKEN_REFRESH_MARGIN_MS` (60000), `TOAST_DURATION_MS` (5000), `PAGE_SIZE` (10), `MAX_TOASTS` (5)
- [ ] All entity types match the API contracts defined in the Spec (Section 3)
- [ ] `ApiResponse<T>` generic: `{ data: T }`
- [ ] `PaginatedResponse<T>` generic: `{ data: T[], meta: { page: number, limit: number, total: number } }`
- [ ] `ApiError`: `{ detail: string, code: string }`
- [ ] `Toast`: `{ id: string, type: 'success' | 'error' | 'warning' | 'info', message: string, duration?: number }`
- [ ] `ConfirmDialogConfig`: `{ title: string, description: string, confirmLabel?: string, cancelLabel?: string }`
- [ ] Prices are `number` (cents, integer)
- [ ] Estado is typed as `'activo' | 'inactivo'` union

### Task 1.4: Utility Functions
**Files to create:**
- `dashboard/src/lib/cn.ts`
- `dashboard/src/lib/format.ts`
- `dashboard/src/lib/slug.ts`
- `dashboard/src/lib/validators.ts`

**Acceptance Criteria:**
- [ ] `cn(...inputs)` merges Tailwind classes using clsx + twMerge
- [ ] `formatCurrency(cents: number)` returns formatted string with Argentine locale: `"$2.500,00"`
- [ ] `formatDate(isoString: string)` returns `"DD/MM/YYYY HH:mm"` format
- [ ] `generateSlug(text: string)` returns lowercase, hyphenated, accent-stripped slug
- [ ] Validators: `required(value)`, `minLength(min)(value)`, `maxLength(max)(value)`, `isEmail(value)` — each returns `string | null`

---

## Phase 2: State Management (Zustand Stores)

### Task 2.1: Auth Store
**Files:** `dashboard/src/stores/auth.store.ts`

**Acceptance Criteria:**
- [ ] Zustand store with persist middleware, key `'buen-sabor-auth'`
- [ ] State: `token`, `refreshToken`, `expiresAt`, `user`, `isAuthenticated`, `isLoading`
- [ ] Actions: `login(email, password)`, `logout()`, `refreshAuth()`
- [ ] BroadcastChannel + storage event fallback for cross-tab sync
- [ ] `onRehydrate` callback for token validation on app load
- [ ] ALL selectors in consuming components MUST be individual (no destructuring)

### Task 2.2: Branch Store
**Files:** `dashboard/src/stores/branch.store.ts`

**Acceptance Criteria:**
- [ ] Persist middleware, key `'buen-sabor-branch'`
- [ ] State: `selectedBranchId`, `branches`, `isLoading`
- [ ] Actions: `selectBranch(id)`, `fetchBranches()`
- [ ] `partialize` persists only: `selectedBranchId`

### Task 2.3: UI Store
**Files:** `dashboard/src/stores/ui.store.ts`

**Acceptance Criteria:**
- [ ] State: `sidebarCollapsed`, `toasts`, `confirmDialog`
- [ ] `addToast` caps at MAX_TOASTS (5), auto-dismiss setTimeout
- [ ] `showConfirm` returns `Promise<boolean>`

---

## Phase 3: API Service Layer

### Task 3.1: API Client with Interceptors
**Files:** `dashboard/src/services/api-client.ts`

### Task 3.2: Auth Service
**Files:** `dashboard/src/services/auth.service.ts`
- Uses SEPARATE axios instance (no interceptors) to avoid circular dependency

### Task 3.3: Entity Services
**Files:** `dashboard/src/services/restaurant.service.ts`, `branch.service.ts`, `category.service.ts`, `subcategory.service.ts`, `product.service.ts`

---

## Phase 4: Routing & Layout

### Task 4.1: Router Configuration
**Files:** `dashboard/src/router/index.tsx`, `routes.ts`, `ProtectedRoute.tsx`, `BranchGuard.tsx`

### Task 4.2: Auth Layout
**Files:** `dashboard/src/layouts/AuthLayout.tsx`

### Task 4.3: Dashboard Layout
**Files:** `dashboard/src/layouts/DashboardLayout.tsx`

### Task 4.4: Sidebar Component
**Files:** `dashboard/src/components/layout/Sidebar.tsx`, `SidebarGroup.tsx`, `SidebarItem.tsx`

### Task 4.5: Header Component
**Files:** `dashboard/src/components/layout/Header.tsx`, `BranchSelector.tsx`, `UserMenu.tsx`

---

## Phase 5: UI Components (Atoms)

### Task 5.1: Base UI Components
**Files:** Button, Input, Textarea, Select, Toggle, Badge, Spinner, Skeleton, EmptyState

### Task 5.2: Modal Component
**Files:** `dashboard/src/components/ui/Modal.tsx`

### Task 5.3: Table and Pagination
**Files:** `dashboard/src/components/ui/Table.tsx`, `Pagination.tsx`

### Task 5.4: Toast System
**Files:** `dashboard/src/components/ui/Toast.tsx`, `ToastContainer.tsx`

### Task 5.5: Confirm Dialog
**Files:** `dashboard/src/components/ui/ConfirmDialog.tsx`

---

## Phase 6: Custom Hooks

### Task 6.1: Convenience Hooks
**Files:** `useAuth.ts`, `useBranch.ts`, `usePagination.ts`, `useConfirm.ts`, `useCrud.ts`

---

## Phase 7: Pages — Auth & Dashboard

### Task 7.1: Login Page
**Files:** `dashboard/src/pages/LoginPage.tsx`

### Task 7.2: Dashboard Page (Placeholder)
**Files:** `dashboard/src/pages/DashboardPage.tsx`

---

## Phase 8: Pages — Restaurant Configuration

### Task 8.1: Restaurant Configuration Page
**Files:** `dashboard/src/pages/RestaurantPage.tsx`, `dashboard/src/components/forms/RestaurantForm.tsx`

---

## Phase 9: Pages — CRUD Entities

### Task 9.1: Branches Page
**Files:** `dashboard/src/pages/BranchesPage.tsx`, `dashboard/src/components/forms/BranchForm.tsx`

### Task 9.2: Categories Page
**Files:** `dashboard/src/pages/CategoriesPage.tsx`, `dashboard/src/components/forms/CategoryForm.tsx`

### Task 9.3: Subcategories Page
**Files:** `dashboard/src/pages/SubcategoriesPage.tsx`, `dashboard/src/components/forms/SubcategoryForm.tsx`

### Task 9.4: Products Page
**Files:** `dashboard/src/pages/ProductsPage.tsx`, `dashboard/src/components/forms/ProductForm.tsx`

---

## Phase 10: Integration & Polish

### Task 10.1: Wire Everything Together
### Task 10.2: Verify Zustand Selector Safety

---

## Task Dependency Graph

```
Phase 1 (Scaffolding)
  ├── 1.1 Vite Project
  ├── 1.2 TailwindCSS Theme (depends on 1.1)
  ├── 1.3 Types & Constants (depends on 1.1)
  └── 1.4 Utilities (depends on 1.1)

Phase 2 (Stores) — depends on Phase 1
Phase 3 (Services) — depends on Phase 1, Phase 2.1
Phase 4 (Routing & Layout) — depends on Phase 2, Phase 3
Phase 5 (UI Components) — depends on Phase 1
Phase 6 (Hooks) — depends on Phase 2, Phase 3, Phase 5
Phase 7-9 (Pages) — depends on Phase 4, Phase 5, Phase 6
Phase 10 (Integration) — depends on ALL
```

---

## Estimated File Count: ~55 files
## Estimated Lines of Code: ~4,000-5,000 LOC (TypeScript + CSS)

---

## Next Recommended
`sdd-apply` — Begin implementation in phase order.
