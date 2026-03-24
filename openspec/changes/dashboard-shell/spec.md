---
sprint: 3
artifact: spec
status: complete
---

# SDD Spec: Sprint 3 — CRUD Base y Dashboard Shell

## Status: APPROVED

---

## 1. Requirements (RFC 2119)

### 1.1 Project Setup
- The dashboard MUST be scaffolded with Vite 7.2, React 19.2, TypeScript 5.9
- The project MUST include `babel-plugin-react-compiler` in the Vite config
- TailwindCSS 4 MUST be configured with dark theme and orange accent (#f97316)
- Zustand 5 MUST be used for state management with `persist` middleware for auth and UI stores
- All Zustand selectors MUST be individual (e.g., `useAuthStore(s => s.token)`) — destructuring (`const { token, user } = useAuthStore()`) is FORBIDDEN due to React 19 infinite render loops
- React Router MUST be used for client-side routing

### 1.2 Authentication
- The app MUST display a login screen at `/login` for unauthenticated users
- The login form MUST accept email and password
- On successful login, the app MUST store the access token (15min TTL) and refresh token (7day TTL) in Zustand persisted store
- The app MUST proactively refresh the access token at 14 minutes (60 seconds before expiry) using a setTimeout timer
- The refresh timer MUST be reset on each successful refresh
- If refresh fails, the app MUST clear auth state and redirect to `/login`
- The app MUST use BroadcastChannel API to sync logout across all open tabs
- As a fallback, the app SHOULD listen to `storage` events for browsers without BroadcastChannel support
- All API requests MUST include the access token in the `Authorization: Bearer {token}` header
- On receiving a 401 response, the app MUST attempt one token refresh; if that fails, redirect to `/login`

### 1.3 Layout
- The layout MUST include a fixed sidebar (left, 280px wide, collapsible to 64px)
- The sidebar MUST display hierarchical navigation groups that are expandable/collapsible
- Navigation groups: "Inicio" (Dashboard), "Mi Restaurante" (Configuracion), "Sucursales" (Lista), "Menu" (Categorias, Subcategorias, Productos)
- The layout MUST include a header bar with: restaurant name (left), branch selector (center), user menu (right)
- The branch selector MUST be a dropdown showing all branches for the current tenant
- Selecting a branch MUST be REQUIRED before accessing any CRUD screen — if no branch is selected, show a prompt
- The branch selector MUST persist the selection in Zustand (persisted)
- The layout MUST use dark theme: background #0a0a0a, surface #171717, border #262626, text #fafafa
- The accent color MUST be orange-500 (#f97316) for primary actions, active states, and highlights

### 1.4 Restaurant Configuration
- The configuration screen MUST allow editing: nombre, slug (auto-generated from nombre, editable), descripcion (textarea), logo URL, banner URL, contacto (telefono, email, direccion)
- The slug MUST auto-generate from nombre using lowercase + hyphens, but MUST remain editable
- All fields MUST validate on blur and on submit
- Save MUST call PUT /api/v1/restaurants/{id}

### 1.5 CRUD: Sucursales (Branches)
- The list view MUST show a paginated table (10 items/page) with columns: nombre, direccion, telefono, email, estado (badge), acciones
- The "Crear" button MUST open a modal with fields: nombre (required, 2-100 chars), direccion, telefono, email, imagen URL, horarios (default 09:00-23:00), estado (activo/inactivo toggle), orden (integer)
- On successful creation, the API MUST auto-generate a "General" base category for the new branch
- The "Editar" button MUST open the same modal pre-filled with existing data
- The "Eliminar" button MUST show a destructive confirmation dialog warning about cascading effects (categories, subcategories, products that will be deleted)
- Pagination MUST use offset-based pagination with page/limit query params

### 1.6 CRUD: Categorias (Categories)
- The list view MUST show a table with columns: icono (emoji), nombre, imagen (thumbnail), orden, estado (badge), acciones
- The list MUST filter out the "Home" virtual category (it is system-managed)
- The "Crear" button MUST open a modal with fields: nombre (required, 2-100 chars), icono (emoji picker or text input), imagen URL, orden (auto-increment, editable), estado (activo/inactivo)
- The orden field MUST default to max(existing_order) + 1
- The "Eliminar" button MUST show a destructive confirmation warning about cascading deletion of subcategories AND their products
- Categories MUST be scoped to the currently selected branch

### 1.7 CRUD: Subcategorias (Subcategories)
- The list view MUST show a table with columns: imagen (thumbnail), nombre, categoria padre, orden, estado (badge), qty productos, acciones
- The list MUST be filterable by parent category via a dropdown filter above the table
- The "Crear" button MUST open a modal with fields: nombre (required, 2-100 chars), categoria padre (required dropdown), imagen URL, orden (auto-increment within parent), estado (activo/inactivo)
- Subcategories MUST be scoped to the currently selected branch

### 1.8 CRUD: Productos (Products)
- The list view MUST show a table with columns: imagen (thumbnail), nombre, categoria/subcategoria (combined), precio (formatted as currency), destacado (star icon), popular (fire icon), estado (badge), acciones
- The "Crear" button MUST open a modal with fields: nombre (required, 2-100 chars), descripcion (textarea, max 500 chars with counter), categoria (required dropdown), subcategoria (optional dropdown, filtered by selected category), precio base (number input, stored as cents), imagen URL, destacado (toggle), popular (toggle), estado (activo/inactivo)
- When a category is selected, the subcategory dropdown MUST filter to show only subcategories of that category
- Products MUST be scoped to the currently selected branch

### 1.9 Toast Notifications
- The system MUST support 4 toast types: success (green), error (red), warning (yellow), info (blue)
- A maximum of 5 toasts MUST be visible simultaneously; oldest dismissed first
- Toasts MUST auto-dismiss after 5 seconds (configurable per toast)
- Toasts MUST appear in the top-right corner, stacked vertically
- Each toast MUST have a manual close button

### 1.10 Destructive Confirmation Dialog
- All delete operations MUST show a confirmation dialog before proceeding
- The dialog MUST display: title ("Eliminar {entity}?"), description of what will be deleted (including cascade counts), a cancel button, and a red "Eliminar" button
- For cascading deletes, the description MUST list affected child entities with counts (e.g., "Se eliminaran 3 subcategorias y 12 productos")

---

## 2. UI Specifications

### 2.1 Color System (TailwindCSS 4 Theme)
```
--color-bg-primary: #0a0a0a       (page background)
--color-bg-surface: #171717       (cards, sidebar, modals)
--color-bg-elevated: #262626      (hover states, dropdowns)
--color-border: #262626           (default borders)
--color-border-focus: #f97316     (focused inputs)
--color-text-primary: #fafafa     (main text)
--color-text-secondary: #a3a3a3   (muted text)
--color-text-tertiary: #737373    (disabled text)
--color-accent: #f97316           (primary actions, links)
--color-accent-hover: #ea580c     (primary hover)
--color-success: #22c55e
--color-error: #ef4444
--color-warning: #eab308
--color-info: #3b82f6
```

### 2.2 Layout Dimensions
- Sidebar: 280px expanded, 64px collapsed, full viewport height
- Header: 64px height, full width minus sidebar
- Content area: fills remaining space, 24px padding, max-width 1400px centered
- Modals: 480px width for forms, centered with backdrop overlay (#000 @ 50% opacity)

### 2.3 Table Specifications
- Row height: 56px
- Header: sticky, bg-surface, uppercase text-xs text-secondary, font-semibold
- Rows: border-b border, hover:bg-elevated transition
- Pagination: bottom-right, showing "Pagina X de Y" with prev/next buttons
- Empty state: centered icon + text "No hay {entities}" with create CTA

### 2.4 Form Specifications
- Input fields: h-10, bg-surface, border, rounded-lg, focus:border-accent focus:ring-1 ring-accent
- Labels: text-sm text-secondary, mb-1.5
- Error messages: text-sm text-error, mt-1
- Required field indicator: red asterisk after label
- Submit button: bg-accent text-white rounded-lg h-10 px-6, hover:bg-accent-hover
- Cancel button: bg-transparent border text-secondary, hover:bg-elevated

### 2.5 Component States
Each interactive component MUST handle these states:
- **Loading**: Skeleton placeholders for tables, spinner for buttons
- **Empty**: Illustration + message + CTA
- **Error**: Error message + retry button
- **Success**: Brief success state then return to default

---

## 3. API Contracts

All endpoints are prefixed with `/api/v1`. All require `Authorization: Bearer {token}` header. All responses follow the envelope: `{ data: T, meta?: { page, limit, total } }`. Errors: `{ detail: string, code: string }`.

### 3.1 Auth Endpoints

#### POST /api/v1/auth/login
```
Request:  { email: string, password: string }
Response: { data: { access_token: string, refresh_token: string, expires_in: 900, user: { id: int, email: string, nombre: string, rol: string, tenant_id: int } } }
Errors:   401 { detail: "Credenciales invalidas", code: "INVALID_CREDENTIALS" }
```

#### POST /api/v1/auth/refresh
```
Request:  { refresh_token: string }
Response: { data: { access_token: string, refresh_token: string, expires_in: 900 } }
Errors:   401 { detail: "Token expirado", code: "REFRESH_TOKEN_EXPIRED" }
```

#### POST /api/v1/auth/logout
```
Request:  { refresh_token: string }
Response: { data: { message: "Sesion cerrada" } }
```

### 3.2 Restaurant Endpoints

#### GET /api/v1/restaurants/me
```
Response: { data: { id: int, nombre: string, slug: string, descripcion: string, logo_url: string | null, banner_url: string | null, telefono: string | null, email: string | null, direccion: string | null } }
```

#### PUT /api/v1/restaurants/{id}
```
Request:  { nombre: string, slug: string, descripcion?: string, logo_url?: string, banner_url?: string, telefono?: string, email?: string, direccion?: string }
Response: { data: Restaurant }
Errors:   409 { detail: "Slug ya existe", code: "SLUG_CONFLICT" }
```

### 3.3 Branch Endpoints

#### GET /api/v1/branches?page=1&limit=10
```
Response: { data: Branch[], meta: { page: int, limit: int, total: int } }
Branch:   { id: int, nombre: string, direccion: string | null, telefono: string | null, email: string | null, imagen_url: string | null, horario_apertura: string, horario_cierre: string, estado: "activo" | "inactivo", orden: int, created_at: string, updated_at: string }
```

#### POST /api/v1/branches
```
Request:  { nombre: string, direccion?: string, telefono?: string, email?: string, imagen_url?: string, horario_apertura?: string (default "09:00"), horario_cierre?: string (default "23:00"), estado?: "activo" | "inactivo" (default "activo"), orden?: int }
Response: { data: Branch }  (also auto-creates "General" category for this branch)
Errors:   422 { detail: "Nombre es requerido", code: "VALIDATION_ERROR" }
```

#### PUT /api/v1/branches/{id}
```
Request:  Partial<BranchCreate>
Response: { data: Branch }
```

#### DELETE /api/v1/branches/{id}
```
Response: { data: { message: "Sucursal eliminada", cascade: { categorias: int, subcategorias: int, productos: int } } }
```

### 3.4 Category Endpoints

#### GET /api/v1/branches/{branch_id}/categories?page=1&limit=10
```
Response: { data: Category[], meta: { page, limit, total } }
Category: { id: int, nombre: string, icono: string | null, imagen_url: string | null, orden: int, estado: "activo" | "inactivo", es_home: boolean, created_at: string, updated_at: string }
Note: Frontend MUST filter out categories where es_home=true
```

#### POST /api/v1/branches/{branch_id}/categories
```
Request:  { nombre: string, icono?: string, imagen_url?: string, orden?: int, estado?: "activo" | "inactivo" }
Response: { data: Category }
```

#### PUT /api/v1/branches/{branch_id}/categories/{id}
```
Request:  Partial<CategoryCreate>
Response: { data: Category }
```

#### DELETE /api/v1/branches/{branch_id}/categories/{id}
```
Response: { data: { message: "Categoria eliminada", cascade: { subcategorias: int, productos: int } } }
Errors:   400 { detail: "No se puede eliminar la categoria Home", code: "HOME_CATEGORY_PROTECTED" }
```

### 3.5 Subcategory Endpoints

#### GET /api/v1/branches/{branch_id}/subcategories?page=1&limit=10&category_id={optional}
```
Response: { data: Subcategory[], meta: { page, limit, total } }
Subcategory: { id: int, nombre: string, imagen_url: string | null, categoria_id: int, categoria_nombre: string, orden: int, estado: "activo" | "inactivo", productos_count: int, created_at: string, updated_at: string }
```

#### POST /api/v1/branches/{branch_id}/subcategories
```
Request:  { nombre: string, categoria_id: int, imagen_url?: string, orden?: int, estado?: "activo" | "inactivo" }
Response: { data: Subcategory }
```

#### PUT /api/v1/branches/{branch_id}/subcategories/{id}
```
Request:  Partial<SubcategoryCreate>
Response: { data: Subcategory }
```

#### DELETE /api/v1/branches/{branch_id}/subcategories/{id}
```
Response: { data: { message: "Subcategoria eliminada", cascade: { productos: int } } }
```

### 3.6 Product Endpoints

#### GET /api/v1/branches/{branch_id}/products?page=1&limit=10
```
Response: { data: Product[], meta: { page, limit, total } }
Product: { id: int, nombre: string, descripcion: string | null, categoria_id: int, categoria_nombre: string, subcategoria_id: int | null, subcategoria_nombre: string | null, precio: int (cents), imagen_url: string | null, destacado: boolean, popular: boolean, estado: "activo" | "inactivo", created_at: string, updated_at: string }
```

#### POST /api/v1/branches/{branch_id}/products
```
Request:  { nombre: string, descripcion?: string (max 500), categoria_id: int, subcategoria_id?: int, precio: int (cents), imagen_url?: string, destacado?: boolean, popular?: boolean, estado?: "activo" | "inactivo" }
Response: { data: Product }
Errors:   422 { detail: "Subcategoria no pertenece a la categoria seleccionada", code: "SUBCATEGORY_MISMATCH" }
```

#### PUT /api/v1/branches/{branch_id}/products/{id}
```
Request:  Partial<ProductCreate>
Response: { data: Product }
```

#### DELETE /api/v1/branches/{branch_id}/products/{id}
```
Response: { data: { message: "Producto eliminado" } }
```

---

## 4. Zustand Store Structure

### 4.1 Auth Store (persisted to localStorage)
```typescript
interface AuthState {
  token: string | null;
  refreshToken: string | null;
  expiresAt: number | null;       // timestamp ms
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
  _scheduleRefresh: () => void;    // internal: setTimeout at expiresAt - 60s
  _broadcastLogout: () => void;    // internal: BroadcastChannel send
}
```
Persist config: `{ name: 'buen-sabor-auth', partialize: (s) => ({ token: s.token, refreshToken: s.refreshToken, expiresAt: s.expiresAt, user: s.user }) }`

### 4.2 Branch Store (persisted to localStorage)
```typescript
interface BranchState {
  selectedBranchId: number | null;
  branches: Branch[];
  isLoading: boolean;
  selectBranch: (id: number) => void;
  fetchBranches: () => Promise<void>;
}
```
Persist config: `{ name: 'buen-sabor-branch', partialize: (s) => ({ selectedBranchId: s.selectedBranchId }) }`

### 4.3 UI Store (persisted to localStorage)
```typescript
interface UIState {
  sidebarCollapsed: boolean;
  toasts: Toast[];
  confirmDialog: ConfirmDialogState | null;
  toggleSidebar: () => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  showConfirm: (config: ConfirmDialogConfig) => Promise<boolean>;
  hideConfirm: () => void;
}
```
Persist config: `{ name: 'buen-sabor-ui', partialize: (s) => ({ sidebarCollapsed: s.sidebarCollapsed }) }`

---

## 5. Scenarios (Given/When/Then)

### 5.1 Auth Flow

**S1: Successful Login**
- GIVEN the user is on /login
- WHEN they enter valid email and password and click "Ingresar"
- THEN the app stores tokens, redirects to /dashboard, and schedules a refresh timer at 14min

**S2: Failed Login**
- GIVEN the user is on /login
- WHEN they enter invalid credentials and click "Ingresar"
- THEN a toast error appears "Credenciales invalidas" and the form is NOT cleared

**S3: Proactive Token Refresh**
- GIVEN the user is authenticated with a token expiring at T
- WHEN the clock reaches T - 60 seconds
- THEN the app calls POST /auth/refresh, stores the new tokens, and reschedules the timer

**S4: Refresh Failure**
- GIVEN the refresh token has expired
- WHEN a proactive or reactive refresh is attempted
- THEN the app clears auth state, shows toast "Sesion expirada", and redirects to /login

**S5: Cross-Tab Logout**
- GIVEN the user has 2 tabs open
- WHEN they click "Cerrar sesion" in tab 1
- THEN tab 2 receives the BroadcastChannel message, clears auth state, and redirects to /login

**S6: 401 Interceptor**
- GIVEN the user makes an API call that returns 401
- WHEN the interceptor catches it
- THEN it attempts one refresh; if successful, retries the original request; if not, redirects to /login

### 5.2 Branch Selection

**S7: Required Branch Selection**
- GIVEN the user navigates to /categorias without a selected branch
- WHEN the page loads
- THEN a modal/prompt appears: "Selecciona una sucursal para continuar"

**S8: Branch Scoping**
- GIVEN the user has selected branch "Centro" (id: 5)
- WHEN they navigate to /categorias
- THEN the app calls GET /api/v1/branches/5/categories and shows only Centro's categories

**S9: Branch Switch**
- GIVEN the user is on /categorias with branch "Centro" selected
- WHEN they switch to branch "Norte" in the header dropdown
- THEN the category table reloads with Norte's categories

### 5.3 CRUD: Sucursales

**S10: Create Branch**
- GIVEN the user is on /sucursales
- WHEN they click "Crear sucursal", fill nombre="Norte", direccion="Av. Norte 123", and submit
- THEN the API creates the branch (with auto-generated "General" category), a success toast appears, and the table refreshes

**S11: Edit Branch**
- GIVEN the user is on /sucursales
- WHEN they click "Editar" on branch "Norte" and change direccion to "Av. Norte 456" and submit
- THEN the API updates the branch, a success toast appears, and the table refreshes

**S12: Delete Branch with Cascade**
- GIVEN branch "Norte" has 2 categories, 3 subcategories, and 8 products
- WHEN the user clicks "Eliminar" on "Norte"
- THEN a confirmation dialog shows: "Eliminar sucursal Norte? Se eliminaran 2 categorias, 3 subcategorias y 8 productos"
- AND when confirmed, the API deletes with cascade and a success toast appears

### 5.4 CRUD: Categorias

**S13: Create Category**
- GIVEN the user is on /categorias with branch "Centro" selected
- WHEN they click "Crear", fill nombre="Pizzas", icono="🍕", and submit
- THEN the API creates the category with orden=max+1, success toast appears, table refreshes

**S14: Filter Home Category**
- GIVEN the branch has categories: Home (es_home=true), Pizzas, Empanadas
- WHEN the category list loads
- THEN only Pizzas and Empanadas are shown (Home is filtered out)

**S15: Delete Category Cascade**
- GIVEN category "Pizzas" has 2 subcategories and 5 products
- WHEN the user clicks "Eliminar" on "Pizzas"
- THEN confirmation shows cascade count; on confirm, deletes all

### 5.5 CRUD: Subcategorias

**S16: Filter by Parent Category**
- GIVEN subcategories exist for Pizzas and Empanadas
- WHEN the user selects "Pizzas" in the category filter dropdown
- THEN only Pizzas' subcategories are shown

**S17: Create Subcategory**
- GIVEN the user is on /subcategorias
- WHEN they click "Crear", select categoria="Pizzas", fill nombre="A la piedra", and submit
- THEN the API creates it with orden auto-incremented within Pizzas

### 5.6 CRUD: Productos

**S18: Create Product**
- GIVEN the user is on /productos
- WHEN they click "Crear", fill nombre="Muzza", categoria="Pizzas", subcategoria="A la piedra", precio=2500 (renders as $2.500), destacado=true, and submit
- THEN the API receives precio=250000 (cents), creates the product, success toast appears

**S19: Category-Subcategory Filter**
- GIVEN the user is creating a product and selects categoria="Pizzas"
- WHEN the subcategory dropdown opens
- THEN it shows only subcategories of Pizzas (e.g., "A la piedra", "A la parrilla")

**S20: Description Length Validation**
- GIVEN the user is creating a product
- WHEN they type more than 500 characters in descripcion
- THEN the character counter turns red and the submit button is disabled

### 5.7 Toasts

**S21: Toast Stacking**
- GIVEN 5 toasts are already visible
- WHEN a 6th toast is triggered
- THEN the oldest toast is dismissed and the new one appears

**S22: Toast Auto-Dismiss**
- GIVEN a success toast is shown
- WHEN 5 seconds pass
- THEN the toast auto-dismisses with a fade-out animation

### 5.8 Destructive Confirmation

**S23: Cancel Delete**
- GIVEN the delete confirmation dialog is showing for a branch
- WHEN the user clicks "Cancelar"
- THEN the dialog closes and NO delete request is made

---

## Next Recommended
`sdd-design` — Component architecture, folder structure, and key technical decisions.
