---
sprint: 3
artifact: design
status: complete
---

# SDD Design: Sprint 3 — CRUD Base y Dashboard Shell

## Status: APPROVED

---

## 1. Folder Structure

```
dashboard/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── .env
├── .env.example
├── public/
│   └── favicon.svg
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── vite-env.d.ts
    ├── config/
    │   └── constants.ts
    ├── types/
    │   ├── auth.ts
    │   ├── restaurant.ts
    │   ├── branch.ts
    │   ├── category.ts
    │   ├── subcategory.ts
    │   ├── product.ts
    │   ├── api.ts
    │   └── ui.ts
    ├── services/
    │   ├── api-client.ts
    │   ├── auth.service.ts
    │   ├── restaurant.service.ts
    │   ├── branch.service.ts
    │   ├── category.service.ts
    │   ├── subcategory.service.ts
    │   └── product.service.ts
    ├── stores/
    │   ├── auth.store.ts
    │   ├── branch.store.ts
    │   └── ui.store.ts
    ├── hooks/
    │   ├── useAuth.ts
    │   ├── useBranch.ts
    │   ├── usePagination.ts
    │   ├── useCrud.ts
    │   └── useConfirm.ts
    ├── router/
    │   ├── index.tsx
    │   ├── routes.ts
    │   ├── ProtectedRoute.tsx
    │   └── BranchGuard.tsx
    ├── layouts/
    │   ├── AuthLayout.tsx
    │   └── DashboardLayout.tsx
    ├── components/
    │   ├── ui/
    │   │   ├── Button.tsx
    │   │   ├── Input.tsx
    │   │   ├── Textarea.tsx
    │   │   ├── Select.tsx
    │   │   ├── Toggle.tsx
    │   │   ├── Badge.tsx
    │   │   ├── Modal.tsx
    │   │   ├── Table.tsx
    │   │   ├── Pagination.tsx
    │   │   ├── Skeleton.tsx
    │   │   ├── Spinner.tsx
    │   │   ├── Toast.tsx
    │   │   ├── ToastContainer.tsx
    │   │   ├── ConfirmDialog.tsx
    │   │   └── EmptyState.tsx
    │   ├── layout/
    │   │   ├── Sidebar.tsx
    │   │   ├── SidebarGroup.tsx
    │   │   ├── SidebarItem.tsx
    │   │   ├── Header.tsx
    │   │   ├── BranchSelector.tsx
    │   │   └── UserMenu.tsx
    │   └── forms/
    │       ├── BranchForm.tsx
    │       ├── CategoryForm.tsx
    │       ├── SubcategoryForm.tsx
    │       ├── ProductForm.tsx
    │       └── RestaurantForm.tsx
    ├── pages/
    │   ├── LoginPage.tsx
    │   ├── DashboardPage.tsx
    │   ├── RestaurantPage.tsx
    │   ├── BranchesPage.tsx
    │   ├── CategoriesPage.tsx
    │   ├── SubcategoriesPage.tsx
    │   └── ProductsPage.tsx
    └── lib/
        ├── cn.ts
        ├── format.ts
        ├── slug.ts
        └── validators.ts
```

---

## 2. Component Tree

```
<App>
  <RouterProvider>
    ├── /login -> <AuthLayout> -> <LoginPage>
    │
    └── /* (protected) -> <ProtectedRoute>
        └── <DashboardLayout>
            ├── <Sidebar>
            │   ├── <SidebarGroup label="Inicio">
            │   │   └── <SidebarItem to="/dashboard" icon="Home" label="Dashboard" />
            │   ├── <SidebarGroup label="Mi Restaurante">
            │   │   └── <SidebarItem to="/configuracion" icon="Settings" label="Configuracion" />
            │   ├── <SidebarGroup label="Sucursales">
            │   │   └── <SidebarItem to="/sucursales" icon="Building" label="Lista" />
            │   └── <SidebarGroup label="Menu">
            │       ├── <SidebarItem to="/categorias" icon="Grid" label="Categorias" />
            │       ├── <SidebarItem to="/subcategorias" icon="Layers" label="Subcategorias" />
            │       └── <SidebarItem to="/productos" icon="Package" label="Productos" />
            │
            ├── <Header>
            │   ├── <span>{restaurantName}</span>
            │   ├── <BranchSelector />
            │   └── <UserMenu />
            │
            └── <main>
                ├── <BranchGuard> (wraps menu routes)
                └── <Outlet /> -> Page components
            │
            └── <ToastContainer />   (portal, fixed top-right)
            └── <ConfirmDialog />    (portal, centered modal)
```

---

## 3. Routing Structure

```typescript
// router/routes.ts
export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  RESTAURANT_CONFIG: '/configuracion',
  BRANCHES: '/sucursales',
  CATEGORIES: '/categorias',
  SUBCATEGORIES: '/subcategorias',
  PRODUCTS: '/productos',
} as const;

// router/index.tsx
const router = createBrowserRouter([
  {
    path: '/login',
    element: <AuthLayout />,
    children: [{ index: true, element: <LoginPage /> }],
  },
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      {
        element: <DashboardLayout />,
        children: [
          { index: true, element: <Navigate to="/dashboard" /> },
          { path: 'dashboard', element: <DashboardPage /> },
          { path: 'configuracion', element: <RestaurantPage /> },
          { path: 'sucursales', element: <BranchesPage /> },
          {
            element: <BranchGuard />,
            children: [
              { path: 'categorias', element: <CategoriesPage /> },
              { path: 'subcategorias', element: <SubcategoriesPage /> },
              { path: 'productos', element: <ProductsPage /> },
            ],
          },
        ],
      },
    ],
  },
]);
```

---

## 4. Zustand Store Architecture

### 4.1 Auth Store — Critical Design Decisions

```typescript
// stores/auth.store.ts
const CHANNEL_NAME = 'buen-sabor-auth';
let refreshTimeoutId: ReturnType<typeof setTimeout> | null = null;
let broadcastChannel: BroadcastChannel | null = null;

try {
  broadcastChannel = new BroadcastChannel(CHANNEL_NAME);
} catch {
  // Fallback: listen to storage events
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      expiresAt: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const res = await authService.login(email, password);
          const expiresAt = Date.now() + res.expires_in * 1000;
          set({
            token: res.access_token,
            refreshToken: res.refresh_token,
            expiresAt,
            user: res.user,
            isAuthenticated: true,
            isLoading: false,
          });
          get()._scheduleRefresh();
        } catch (err) {
          set({ isLoading: false });
          throw err;
        }
      },

      logout: () => {
        if (refreshTimeoutId) clearTimeout(refreshTimeoutId);
        const rt = get().refreshToken;
        if (rt) authService.logout(rt).catch(() => {});
        set({ token: null, refreshToken: null, expiresAt: null, user: null, isAuthenticated: false });
        get()._broadcastLogout();
      },

      refreshAuth: async () => {
        const rt = get().refreshToken;
        if (!rt) { get().logout(); return; }
        try {
          const res = await authService.refresh(rt);
          const expiresAt = Date.now() + res.expires_in * 1000;
          set({ token: res.access_token, refreshToken: res.refresh_token, expiresAt });
          get()._scheduleRefresh();
        } catch {
          get().logout();
        }
      },

      _scheduleRefresh: () => {
        if (refreshTimeoutId) clearTimeout(refreshTimeoutId);
        const expiresAt = get().expiresAt;
        if (!expiresAt) return;
        const refreshIn = expiresAt - Date.now() - 60_000;
        if (refreshIn <= 0) { get().refreshAuth(); return; }
        refreshTimeoutId = setTimeout(() => get().refreshAuth(), refreshIn);
      },

      _broadcastLogout: () => {
        broadcastChannel?.postMessage({ type: 'LOGOUT' });
      },
    }),
    {
      name: 'buen-sabor-auth',
      partialize: (s) => ({
        token: s.token,
        refreshToken: s.refreshToken,
        expiresAt: s.expiresAt,
        user: s.user,
      }),
      onRehydrate: (_state, _error) => {
        return (state) => {
          if (state?.token && state?.expiresAt) {
            if (Date.now() < state.expiresAt) {
              state.isAuthenticated = true;
              state._scheduleRefresh();
            } else {
              state.refreshAuth();
            }
          }
        };
      },
    }
  )
);

broadcastChannel?.addEventListener('message', (event) => {
  if (event.data?.type === 'LOGOUT') {
    useAuthStore.getState().logout();
  }
});

if (!broadcastChannel) {
  window.addEventListener('storage', (event) => {
    if (event.key === 'buen-sabor-auth' && event.newValue) {
      const parsed = JSON.parse(event.newValue);
      if (!parsed.state?.token) {
        useAuthStore.getState().logout();
      }
    }
  });
}
```

### 4.2 CRITICAL: Zustand Selector Pattern

```typescript
// CORRECT — individual selectors (React 19 safe)
const token = useAuthStore((s) => s.token);
const user = useAuthStore((s) => s.user);
const login = useAuthStore((s) => s.login);

// FORBIDDEN — destructuring causes infinite re-renders in React 19
// const { token, user, login } = useAuthStore();
```

**WHY**: React 19's compiler aggressively memoizes. Zustand's unselectored `useStore()` returns a new object reference every time the store updates ANY field. Individual selectors return primitives or stable references, breaking the cycle.

### 4.3 Branch Store

```typescript
export const useBranchStore = create<BranchState>()(
  persist(
    (set) => ({
      selectedBranchId: null,
      branches: [],
      isLoading: false,
      selectBranch: (id) => set({ selectedBranchId: id }),
      fetchBranches: async () => {
        set({ isLoading: true });
        const res = await branchService.getBranches({ page: 1, limit: 100 });
        set({ branches: res.data, isLoading: false });
      },
    }),
    {
      name: 'buen-sabor-branch',
      partialize: (s) => ({ selectedBranchId: s.selectedBranchId }),
    }
  )
);
```

### 4.4 UI Store

```typescript
let toastIdCounter = 0;
const MAX_TOASTS = 5;

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      sidebarCollapsed: false,
      toasts: [],
      confirmDialog: null,

      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

      addToast: (toast) => {
        const id = String(++toastIdCounter);
        const newToast = { ...toast, id };
        set((s) => ({
          toasts: [...s.toasts.slice(-(MAX_TOASTS - 1)), newToast],
        }));
        setTimeout(() => get().removeToast(id), toast.duration ?? 5000);
      },

      removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),

      showConfirm: (config) =>
        new Promise<boolean>((resolve) => {
          set({
            confirmDialog: {
              ...config,
              onConfirm: () => { set({ confirmDialog: null }); resolve(true); },
              onCancel: () => { set({ confirmDialog: null }); resolve(false); },
            },
          });
        }),

      hideConfirm: () => set({ confirmDialog: null }),
    }),
    {
      name: 'buen-sabor-ui',
      partialize: (s) => ({ sidebarCollapsed: s.sidebarCollapsed }),
    }
  )
);
```

---

## 5. API Service Layer

### 5.1 API Client (Axios)

```typescript
// services/api-client.ts
export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: attach token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: handle 401 with single refresh promise pattern
let isRefreshing = false;
let failedQueue: Array<{ resolve: Function; reject: Function }> = [];

const processQueue = (error: any, token: string | null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token)));
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await useAuthStore.getState().refreshAuth();
        const newToken = useAuthStore.getState().token;
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);
```

**KEY DECISION**: Single refresh promise pattern prevents token refresh storms.

### 5.2 Service Pattern

```typescript
// services/branch.service.ts
export const branchService = {
  getBranches: (params: { page: number; limit: number }) =>
    apiClient.get<PaginatedResponse<Branch>>('/branches', { params }).then((r) => r.data),
  createBranch: (data: BranchCreate) =>
    apiClient.post<ApiResponse<Branch>>('/branches', data).then((r) => r.data),
  updateBranch: (id: number, data: BranchUpdate) =>
    apiClient.put<ApiResponse<Branch>>(`/branches/${id}`, data).then((r) => r.data),
  deleteBranch: (id: number) =>
    apiClient.delete<ApiResponse<{ message: string; cascade: { categorias: number; subcategorias: number; productos: number } }>>(`/branches/${id}`).then((r) => r.data),
};
```

---

## 6. Generic CRUD Hook

```typescript
interface UseCrudOptions<T, TCreate, TUpdate> {
  fetchFn: (params: { page: number; limit: number }) => Promise<PaginatedResponse<T>>;
  createFn: (data: TCreate) => Promise<ApiResponse<T>>;
  updateFn: (id: number, data: TUpdate) => Promise<ApiResponse<T>>;
  deleteFn: (id: number) => Promise<ApiResponse<any>>;
  entityName: string;
}

function useCrud<T, TCreate, TUpdate>(options: UseCrudOptions<T, TCreate, TUpdate>) {
  // Returns: { items, isLoading, page, totalPages, setPage, create, update, remove, refresh }
}
```

---

## 7. TailwindCSS 4 Theme Configuration

```css
/* src/index.css */
@import "tailwindcss";

@theme {
  --color-bg-primary: #0a0a0a;
  --color-bg-surface: #171717;
  --color-bg-elevated: #262626;
  --color-border-default: #262626;
  --color-border-focus: #f97316;
  --color-text-primary: #fafafa;
  --color-text-secondary: #a3a3a3;
  --color-text-tertiary: #737373;
  --color-accent: #f97316;
  --color-accent-hover: #ea580c;
  --color-success: #22c55e;
  --color-error: #ef4444;
  --color-warning: #eab308;
  --color-info: #3b82f6;
  --font-family-sans: 'Inter', system-ui, -apple-system, sans-serif;
}
```

---

## 8. Key Technical Decisions

### D1: Why Zustand Individual Selectors (not destructuring)
React 19 infinite loop prevention. Individual primitive selectors are stable by value equality.

### D2: Why BroadcastChannel for Tab Sync
Modern, purpose-built API for same-origin tab communication. 97%+ browser support. Storage events as fallback.

### D3: Why Proactive Refresh (not on-401-only)
Refreshing only on 401 means every first request after expiry fails. Proactive refresh at T-60s ensures seamless UX.

### D4: Why Single Refresh Promise Pattern
Prevents token refresh storms when multiple API calls fail with 401 simultaneously.

### D5: Why Axios over fetch
Interceptors (critical for auth flow), automatic JSON parsing, easier error handling.

### D6: Why Generic CRUD Hook
4 entities share the same pattern. Generic `useCrud` hook eliminates ~70% of duplication.

### D7: Why Prices in Cents
Floating-point math is unreliable for currency. Integer cents avoids this.

### D8: Why Portal for Toasts and Confirm Dialog
Avoids z-index conflicts with sidebar and page content.

---

## Next Recommended
`sdd-tasks` — Hierarchical task breakdown with acceptance criteria and file paths.
