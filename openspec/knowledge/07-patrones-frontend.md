# Patrones Frontend
> Fuente de verdad para: pwa-waiter, pwa-menu, dashboard, cualquier fase con código React

---

## Patrón crítico de Zustand

### PROHIBIDO (causa infinite re-render loops)

```typescript
// NUNCA hacer esto
const { items } = useStore()
const { tables, fetchTables } = useTablesStore()
```

Zustand retorna el estado completo del store. Al destructurar, el componente se re-renderiza con CUALQUIER cambio en el store, aunque los campos usados no hayan cambiado. Esto causa cascadas infinitas de re-renders cuando el componente mismo dispara actualizaciones de estado.

### Correcto — siempre selectors

```typescript
// CORRECTO: selector exportado desde el archivo del store
export const selectItems = (state: State) => state.items

const items = useStore(selectItems)
const addItem = useStore((s) => s.addItem)

// CORRECTO: selector inline para acciones
const fetchTables = useTablesStore((s) => s.fetchTables)
const tables = useTablesStore(selectTables)
```

Los selectores hacen que el componente solo se re-renderice cuando el valor específico cambia (comparación por referencia).

### useShallow para arrays filtrados/computed

Cuando el selector devuelve un array nuevo en cada llamada (por `.filter()`, `.map()`, etc.), la comparación por referencia siempre falla y el componente se re-renderiza infinitamente. Usar `useShallow` para comparación shallow:

```typescript
import { useShallow } from 'zustand/react/shallow'

// CORRECTO: useShallow evita re-renders por nueva referencia de array
const staff = useStaffStore(
  useShallow((state) =>
    selectedBranchId ? state.staff.filter((s) => s.branch_id === selectedBranchId) : []
  )
)

// INCORRECTO: crea nueva referencia de array en cada render -> infinite loop
const staff = useStaffStore((state) =>
  selectedBranchId ? state.staff.filter((s) => s.branch_id === selectedBranchId) : []
)
```

Para derivaciones de estado ya extraído con un selector, usar `useMemo`:

```typescript
const items = useStore(selectItems)  // selector simple primero

// Derivacion posterior con useMemo (NO inline en el selector)
const filteredItems = useMemo(() =>
  items.filter(i => i.active),
  [items]
)
```

Regla general: operaciones que devuelven una nueva referencia (filter, map, reduce) van en `useShallow` o en `useMemo` posterior — NUNCA directamente en el selector sin `useShallow`.

### EMPTY_ARRAY stable reference

Para selectores con fallback de array vacío, usar una constante estable en lugar de `[]` inline. `[]` crea una nueva referencia en cada evaluación y rompe la comparación del selector:

```typescript
// CORRECTO: referencia estable declarada a nivel de módulo
const EMPTY_ARRAY: number[] = []
export const selectBranchIds = (s: State) => s.user?.branch_ids ?? EMPTY_ARRAY

// En pwaMenu (tableStore/selectors.ts):
const EMPTY_CART_ITEMS: CartItem[] = []
const EMPTY_DINERS: Diner[] = []
```

---

## Patrón de formularios — React 19 useActionState

El estándar en los tres sub-proyectos es `useActionState`, no `useState` + handlers manuales. Provee estado del formulario, la action, e `isPending` de forma declarativa.

```typescript
import { useActionState, useCallback } from 'react'
import type { FormState } from '../types/form'

const submitAction = useCallback(
  async (_prevState: FormState<T>, formData: FormData): Promise<FormState<T>> => {
    // 1. Extraer campos del FormData
    const data: T = {
      field1: formData.get('field1') as string,
      quantity: parseInt(formData.get('quantity') as string, 10) || 0,
      is_active: formData.get('is_active') === 'on',
    }

    // 2. Validar antes de enviar
    const validation = validateData(data)
    if (!validation.isValid) {
      return { errors: validation.errors, isSuccess: false }
    }

    // 3. Ejecutar
    try {
      if (modal.selectedItem) {
        updateItem(modal.selectedItem.id, data)
        toast.success('Actualizado correctamente')
      } else {
        addItem(data)
        toast.success('Creado correctamente')
      }
      return { isSuccess: true, message: 'Guardado correctamente' }
    } catch (error) {
      const message = handleError(error, 'Component.submitAction')
      toast.error(`Error: ${message}`)
      return { isSuccess: false, message: `Error: ${message}` }
    }
  },
  [modal.selectedItem, updateItem, addItem]
)

const [state, formAction, isPending] = useActionState<FormState<T>, FormData>(
  submitAction,
  { isSuccess: false }
)

// Cerrar modal automáticamente en éxito
if (state.isSuccess && modal.isOpen) {
  modal.close()
}
```

En JSX, el formulario usa `action={formAction}` y el botón usa `isPending` para estado de carga:

```tsx
<form id="item-form" action={formAction}>
  {/* campos del formulario */}
</form>
<Button type="submit" form="item-form" isLoading={isPending}>
  {modal.selectedItem ? 'Guardar' : 'Crear'}
</Button>
```

`isPending` es `true` mientras la action async está en curso. Usarlo para deshabilitar inputs y mostrar spinners; nunca manejar ese estado con un `useState` separado.

pwaMenu también usa `useActionState` en: `ProductDetailModal`, `CallWaiterModal`, `JoinTable`, `AIChat`.

---

## Patrón WebSocket — ref para evitar acumulación de listeners

Sin el patrón ref, cada re-render del componente que contiene el handler registra un nuevo listener sobre el mismo evento — los handlers se acumulan y se ejecutan múltiples veces.

```typescript
// Handler actualizado en cada render, pero la suscripción no se re-ejecuta
const handleEventRef = useRef(handleEvent)

// Mantener ref actualizada sin disparar re-suscripción (sin deps en este useEffect)
useEffect(() => {
  handleEventRef.current = handleEvent
})

// Suscribir UNA sola vez al montar; el cleanup cancela la suscripción
useEffect(() => {
  const unsubscribe = ws.on('*', (e) => handleEventRef.current(e))
  return unsubscribe
}, [])  // deps vacío — suscribir una vez
```

Por qué funciona: la ref siempre apunta al handler más reciente, pero la suscripción al WebSocket solo se establece al montar y se limpia al desmontar.

Este mismo patrón aplica para event listeners del DOM en modales (`Escape`, `keydown`):

```typescript
const onCloseRef = useRef(onClose)

useEffect(() => {
  onCloseRef.current = onClose
}, [onClose])

useEffect(() => {
  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onCloseRef.current()
  }
  if (isOpen) document.addEventListener('keydown', handleEscape)
  return () => document.removeEventListener('keydown', handleEscape)
}, [isOpen])  // solo depende de isOpen, no de onClose
```

---

## Mount guard para async hooks

Previene `setState` sobre un componente ya desmontado (memory leak y warning en consola):

```typescript
useEffect(() => {
  let isMounted = true

  fetchData().then(data => {
    if (!isMounted) return   // Si ya se desmontó, ignorar
    setData(data)
  })

  return () => { isMounted = false }
}, [])
```

pwaMenu expone el hook `useIsMounted` en `src/hooks/useIsMounted.ts`:

```typescript
const isMounted = useIsMounted()
fetchData().then(data => {
  if (!isMounted.current) return
  setData(data)
})
```

---

## Logout — prevención de infinite loop

**El problema:** cuando el token expira el API client recibe un 401, llama a `onTokenExpired`, que llama a `logout()`, que hace un request a `/api/auth/logout` con el token inválido, que recibe otro 401, que vuelve a llamar a `onTokenExpired`... loop infinito.

**La solución:** en `api.ts`, la llamada a `authAPI.logout()` DEBE pasar `false` como tercer argumento a `fetchAPI` para deshabilitar el retry en 401:

```typescript
// CORRECTO: deshabilitar retry en el logout
logout: () => fetchAPI('/auth/logout', { method: 'POST' }, false)

// INCORRECTO: sin el false, el logout puede disparar otro intento de refresh
logout: () => fetchAPI('/auth/logout', { method: 'POST' })
```

---

## Dashboard — patrones específicos

### HelpButton obligatorio en todas las páginas

Cada página incluye un `HelpButton` (botón rojo centrado) que abre un modal con descripción de la funcionalidad. Es obligatorio en todas las páginas del Dashboard:

```typescript
import { helpContent } from '../utils/helpContent'

<PageContainer
  title="Productos"
  description="Gestión de platos y bebidas"
  helpContent={helpContent.products}
>
```

El contenido está centralizado en `src/utils/helpContent.tsx` con entradas para: dashboard, restaurant, branches, categories, subcategories, products, prices, allergens, promotionTypes, promotions, settings.

Los modales de creación/edición también incluyen un `HelpButton` de tamaño `sm` en la cabecera del formulario.

### Estructura estándar de páginas CRUD

```
PageContainer
  Table (datos paginados)
    columnas con acciones (editar, eliminar)
  Pagination
  Modal (crear/editar) con useFormModal
  ConfirmDialog (eliminar) con useConfirmDialog
```

### Hooks de UI reutilizables

```typescript
// useFormModal: reemplaza 3 useState para estado modal + datos formulario
import { useFormModal } from '../hooks'

const modal = useFormModal<FormData>({ name: '', description: '', is_active: true })

modal.openCreate({ ...initialFormData })        // modo creación
modal.openEdit(item, { ...itemFormData })        // modo edición
modal.close()
modal.setFormData(prev => ({ ...prev, name: 'Nuevo' }))
modal.isOpen        // boolean
modal.selectedItem  // item en edición o null
modal.formData      // datos actuales del formulario

// useConfirmDialog: reemplaza 2 useState para confirmación de eliminación
import { useConfirmDialog } from '../hooks'

const deleteDialog = useConfirmDialog<Item>()

deleteDialog.open(item)
deleteDialog.close()
deleteDialog.isOpen
deleteDialog.item

// usePagination: 10 items por página, auto-reset al filtrar
const {
  paginatedItems,
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  setCurrentPage,
} = usePagination(sortedItems)
```

Estado de migración: 9/11 páginas CRUD simples usan `useFormModal`/`useConfirmDialog`. Pendientes: Products y Promotions (páginas complejas).

### Datos con scope de sucursal

Categorías, subcategorías y productos están filtrados por `selectedBranchId`. Nunca usar `''` como fallback; pasar `null` directamente:

```typescript
const selectedBranchId = useBranchStore(selectSelectedBranchId)  // string | null

// Filtrar en useMemo (no en el selector)
const branchCategories = useMemo(() => {
  if (!selectedBranchId) return []
  return categories.filter(
    (c) => c.branch_id === selectedBranchId && c.name !== HOME_CATEGORY_NAME
  )
}, [categories, selectedBranchId])
```

`selectBranchById` acepta `string | null` — pasar `selectedBranchId` directamente, sin fallback a cadena vacía.

### Reglas del React Compiler (eslint-plugin-react-hooks 7.x)

El proyecto usa `babel-plugin-react-compiler` en los tres frontends. Reglas críticas:

**1. Hooks siempre incondicionales:**
```typescript
// INCORRECTO
if (type === 'submit') { const formStatus = useFormStatus() }

// CORRECTO
const formStatus = useFormStatus()
const isPending = type === 'submit' && formStatus.pending
```

**2. Estado derivado con useMemo, no setState en useEffect:**
```typescript
// INCORRECTO — setState en effect causa renders en cascada
useEffect(() => {
  if (!branches.includes(selectedId)) setSelectedId(branches[0].id)
}, [branches, selectedId])

// CORRECTO — estado derivado
const effectiveId = useMemo(() => {
  if (branches.some(b => b.id === selectedId)) return selectedId
  return branches[0]?.id ?? ''
}, [branches, selectedId])
```

**3. Objeto completo en deps de useMemo, no propiedades:**
```typescript
// INCORRECTO
useMemo(() => [...], [openEditModal, deleteDialog.open])

// CORRECTO
useMemo(() => [...], [openEditModal, deleteDialog])
```

**4. Lazy component caching para dynamic imports:**
```typescript
// LazyModal.tsx — cache a nivel de módulo y eslint-disable porque
// lazy() en render es inevitable para loaders dinámicos
/* eslint-disable react-hooks/static-components */
const lazyComponentCache = new Map<LazyLoader, ReturnType<typeof lazy>>()
```

**5. unknown en lugar de any en genéricos:**
```typescript
// INCORRECTO
export interface Options<T, TData = any> { ... }

// CORRECTO
export interface Options<T, TData = unknown> { ... }
```

### Code splitting obligatorio

Todas las páginas usan `React.lazy()`:

```typescript
const DashboardPage = lazy(() => import('./pages/Dashboard'))
// Envuelto en <Suspense fallback={<PageLoader />}>
```

### Cascade delete centralizado

Todas las eliminaciones en cascada van por `src/services/cascadeService.ts`. No implementar lógica de cascada inline en páginas:

```typescript
import { deleteBranchWithCascade, deleteCategoryWithCascade } from '../services/cascadeService'

const result = deleteBranchWithCascade(selectedBranch.id)
if (!result.success) {
  toast.error(result.error || 'Error al eliminar')
  return
}
```

Retorna `CascadeDeleteResult` con `success`, `deletedCounts`, y `error?`.

### Migraciones de stores Zustand

Al cambiar la estructura de datos de un store: incrementar `version` en `STORE_VERSIONS` y agregar función `migrate`. Usar `unknown` (nunca `any`) para `persistedState`, con type guards antes de castear:

```typescript
migrate: (persistedState: unknown, version: number) => {
  if (!persistedState || typeof persistedState !== 'object') {
    return { products: initialProducts }
  }
  const state = persistedState as { products?: unknown }
  if (!Array.isArray(state.products)) {
    return { products: initialProducts }
  }
  // transformaciones incrementales por version...
  return { products } as State
}
```

---

## pwaMenu — patrones específicos

### i18n: cero strings hardcodeadas

TODA cadena visible al usuario debe pasar por `t()` de `useTranslation`. Sin excepciones — incluye mensajes de error, placeholders, labels, tooltips, aria-labels:

```typescript
import { useTranslation } from 'react-i18next'
const { t } = useTranslation()

// CORRECTO
<button>{t('cart.submit')}</button>
<p>{t('errors.timeout')}</p>

// INCORRECTO
<button>Enviar pedido</button>
```

Los mensajes de error también usan i18n keys. Se almacena la key, se muestra con `t(errorKey)`:

```typescript
setError('errors.authGoogleInvalid')   // guardar la clave
<p>{t(errorKey)}</p>                   // mostrar traducido
```

Idiomas soportados: **es** (completo), **en** (fallback a es), **pt** (fallback a es).
Archivos: `src/i18n/es.json`, `en.json`, `pt.json`. Agregar keys en los tres archivos al mismo tiempo.

El hook `useProductTranslation` maneja i18n de nombres y descripciones de productos del catálogo.

### Autenticación por Table Token (HMAC)

pwaMenu NO usa JWT. La autenticación es por `X-Table-Token` (HMAC, 3 horas de vida):

```typescript
import { setTableToken, dinerAPI } from './api'

// Al unirse a la mesa
setTableToken(response.table_token)  // se persiste en localStorage

// Todas las llamadas de diner agregan X-Table-Token automáticamente
dinerAPI.submitRound({ items })
```

### Carrito colaborativo vía WebSocket

El carrito es local por dispositivo. La sincronización entre pestañas del mismo dispositivo usa `storage event`. El WebSocket (`/ws/diner?table_token=...`) actualiza el estado de rounds. El `tableStore` detecta si hay sesión backend:

```typescript
// joinTable es async
await joinTable(tableId, tableName, dinerName)
// Si tableId es numérico -> llama al backend /api/tables/{id}/session

// submitOrder verifica sesión backend
if (session.backend_session_id) {
  // Llama /api/diner/rounds/submit con X-Table-Token
}
```

### Confirmación grupal de pedido (Round Confirmation)

Antes de enviar el pedido a cocina, todos los comensales deben confirmar (evita envíos accidentales):

```typescript
const { proposeRound, confirmReady, cancelReady, cancelRoundProposal } = useRoundConfirmationActions()
const { confirmationCount, allReady, hasCurrentDinerConfirmed, isProposer } = useRoundConfirmationData()

// Flujo: proponer -> cada diner confirma -> cuando allReady -> auto-submit tras 1.5s
// Expira a los 5 minutos o si el proponente cancela
```

### Actualizaciones optimistas

`useOptimisticCart` usa `useOptimistic` de React 19 para feedback instantáneo con rollback automático en caso de error del servidor.

### Capacidades offline (PWA)

Service Worker con tres estrategias en `vite.config.ts`:
- `CacheFirst`: imágenes (30d), fuentes (1 año)
- `NetworkFirst`: APIs con timeout fallback al cache
- SPA fallback: navega a `index.html` sin conexión

Fallback a `mockData.ts` cuando el backend no está disponible.

### Mobile viewport

Todos los contenedores de página/vista deben incluir estas clases para evitar scroll horizontal en mobile:

```tsx
<div className="min-h-screen bg-dark-bg overflow-x-hidden w-full max-w-full">
```

Prevención global adicional en `index.css` sobre `html`, `body`, y `#root`.

---

## pwaWaiter — patrones específicos

### Flujo pre-login: sucursal antes de login

El mozo DEBE seleccionar sucursal ANTES de ingresar credenciales:

```
PreLoginBranchSelect -> Login -> AssignmentVerification -> MainPage
```

1. `GET /api/public/branches` (sin auth) — seleccionar sucursal
2. Login con credenciales — JWT
3. `GET /api/waiter/verify-branch-assignment?branch_id={id}` — verificar asignación del DÍA actual
4. Si no asignado hoy — pantalla "Acceso Denegado" con botón "Elegir otra sucursal"
5. Si asignado — `assignmentVerified: true` en authStore — `MainPage`

El store `authStore` guarda `preLoginBranchId` y `preLoginBranchName` antes del login. El botón "Cambiar" en Login borra el branch y vuelve al paso 1.

### Token refresh proactivo cada 14 minutos

`authStore` refresca el JWT proactivamente antes de que expire (access token dura 15 min). Igual en Dashboard. Refresh tokens en HttpOnly cookies (`credentials: 'include'` en fetch):

```typescript
// authStore.ts — refresh cada 14 minutos, nunca llegar al límite de 15
scheduleTokenRefresh(14 * 60 * 1000)
```

### Offline-first con retry queue

Las operaciones fallidas se encolan en `retryQueueStore` y se reintentan automáticamente al recuperar conectividad. Orden FIFO.

### Comanda rápida (Autogestión)

Para clientes sin teléfono, el mozo toma pedidos directamente desde la app:

- Endpoint compacto sin imágenes: `GET /api/waiter/branches/{id}/menu`
- Modal split-view: panel izquierdo = búsqueda/categorías, panel derecho = carrito
- Para mesas libres: activar primero con `waiterTableAPI.activateTable(tableId, { diner_count })`
- Submit: `waiterTableAPI.submitRound(sessionId, { items })`
- Componente: `AutogestionModal.tsx`

### Filtrado de eventos por sector

Los eventos WebSocket con `sector_id` solo llegan a los mozos asignados a ese sector. ADMIN/MANAGER reciben todos los eventos de la sucursal. El `tablesStore` procesa el filtrado al manejar eventos entrantes.

### Agrupación de mesas por sector

Las mesas se muestran agrupadas por sector (ej: "Interior", "Terraza"). Cada sector muestra nombre, badge con cantidad de mesas, e indicador urgente (pulso rojo) si hay mesas con alertas.

### Animaciones según prioridad

| Prioridad | Condición | Animación | Duración |
|-----------|-----------|-----------|----------|
| 1 | `hasServiceCall` | Rojo blink | 3s |
| 2 | `orderStatus === 'ready_with_kitchen'` | Naranja blink | 5s |
| 3 | `statusChanged` | Azul blink | 1.5s |
| 4 | `hasNewOrder` | Amarillo pulse | 2s |
| 5 | `check_status === 'REQUESTED'` | Violeta pulse | — |

### Estilo visual

pwaWaiter usa **tema claro** con acento naranja (`#f97316`) y elementos **rectangulares** (sin bordes redondeados). Es la única diferencia visual respecto a Dashboard (tema oscuro) y pwaMenu (tema oscuro mobile).

---

## Convenciones de código (todos los frontends)

| Convención | Valor |
|------------|-------|
| Idioma de la UI | Español |
| Comentarios en código | Inglés |
| Color de acento | Naranja `#f97316` |
| Logging | `utils/logger.ts` — NUNCA `console.log/warn/error` directo |
| Generación de IDs | `crypto.randomUUID()` vía helper `generateId()` |
| Nomenclatura frontend | camelCase |
| Nomenclatura backend | snake_case |
| TypeScript | Strict mode — `unknown` sobre `any` |
| Precios almacenados | Centavos enteros (`12550` = $125.50) |
| Formato de precio para display | `formatPrice(price)` de `utils/constants.ts` |

### Logging

```typescript
import { handleError, logWarning, logInfo } from '../utils/logger'

// En catch blocks — devuelve mensaje amigable para el usuario
catch (error) {
  const message = handleError(error, 'ComponentName.functionName')
  toast.error(message)
}

// Advertencias no críticas (siempre se loggean, incluso en producción)
logWarning('Invalid array structure', 'componentName', dataObject)

// Info de desarrollo (solo en modo DEV)
logInfo('Processing items', 'componentName', { count: items.length })
```

pwaMenu usa loggers por módulo:
```typescript
const myLogger = logger.module('ModuleName')
// Pre-configurados: tableStoreLogger, apiLogger, i18nLogger, errorBoundaryLogger, joinTableLogger
```

---

## Conversiones de tipos frontend-backend

```typescript
// IDs: backend = number, frontend = string
const frontendId = String(backendId)           // 42 -> "42"
const backendId = parseInt(frontendId, 10)     // "42" -> 42

// Precios: backend = centavos (int), frontend = pesos (float)
const displayPrice = backendCents / 100        // 12550 -> 125.50
const backendCents = Math.round(price * 100)   // 125.50 -> 12550 (Math.round OBLIGATORIO)

// Estado de sesión: backend UPPERCASE -> frontend lowercase
// OPEN -> 'active'  |  PAYING -> 'paying'  |  CLOSED -> 'closed'
```

Helpers de conversión en `pwaMenu/src/pages/Home.tsx`:

```typescript
function convertBackendProduct(prod: ProductFrontend): Product
function convertBackendCategory(cat: CategoryFrontend): Category
function convertBackendSubcategory(sub, categoryId): Subcategory
```

---

## Container/Presentational pattern

- **Container (smart):** conoce el store, despacha acciones, maneja efectos secundarios. No tiene lógica de UI ni estilos propios.
- **Presentational (dumb):** recibe todo por props, no sabe del store ni del backend. Fácil de testear en aislamiento.

```typescript
// Container — sabe del store
function TableListContainer() {
  const tables = useTablesStore(selectTables)
  const fetchTables = useTablesStore((s) => s.fetchTables)
  useEffect(() => { fetchTables() }, [fetchTables])
  return <TableListView tables={tables} />
}

// Presentational — solo renderiza
function TableListView({ tables }: { tables: Table[] }) {
  return <ul>{tables.map(t => <TableCard key={t.id} table={t} />)}</ul>
}
```

Aplicar especialmente en componentes que consumen múltiples stores o realizan fetch de datos.

---

## Atomic Design — jerarquía de componentes

| Nivel | Directorio | Descripción |
|-------|------------|-------------|
| Atoms | `components/ui/` | Button, Input, Badge, Spinner, Modal |
| Molecules | `components/` | FormField, SearchBar, TableCard, CartItemCard |
| Organisms | `components/` | TableGrid, SharedCart, AutogestionModal, Header |
| Templates | `pages/` + Layout | PageContainer, Layout (con sidebar/nav) |
| Pages | `pages/` | Dashboard, MainPage, Home, CloseTable |

Componentes complejos usan estructura de carpeta con `index.tsx` y subcomponentes (ej: `JoinTable/`, `AIChat/`, `tableStore/`).

---

## Gotchas y edge cases

- **Destructuring Zustand CAUSA infinite re-renders** — es el error más común y difícil de debuggear. Siempre usar selectores individuales, sin excepción.

- **useShallow es OBLIGATORIO** para selectores que devuelven arrays filtrados o mapeados. Sin useShallow, cada render produce una nueva referencia aunque los datos sean idénticos.

- **EMPTY_ARRAY a nivel de módulo** — nunca `?? []` inline como valor de retorno en un selector. Declarar la constante fuera del componente y del selector.

- **pwaMenu: cero strings hardcodeadas** — toda cadena visible al usuario usa `t()`. No hay excepciones. Incluye placeholders, aria-labels, mensajes de error.

- **Async hooks necesitan mount guard** — cualquier `.then()` o `await` seguido de `setState` debe verificar que el componente siga montado. Usar `useIsMounted` en pwaMenu o el patrón `let isMounted = true` en Dashboard/pwaWaiter.

- **WS subscription: suscribir una vez con deps vacías**, usar ref para mantener el handler actualizado. Si se re-suscribe en cada render, los listeners se acumulan.

- **authAPI.logout() debe pasar `false`** como tercer argumento para deshabilitar retry en 401 y evitar el bucle infinito.

- **Precios: siempre `Math.round()` al convertir a centavos** — `125.50 * 100` puede ser `12549.999...` por aritmética de punto flotante.

- **Table codes NO son únicos entre sucursales** — siempre requieren `branch_slug`. "INT-01" puede existir en múltiples sucursales.

- **Token de tabla dura 3 horas** — pwaMenu debe manejar expiración durante sesiones largas de mesa.

- **`selectBranchById` acepta `string | null`** — pasar `selectedBranchId` directamente sin fallback a cadena vacía.

- **React Compiler: hooks siempre incondicionales** — `if (condition) { const x = useHook() }` es un error de linting. Llamar siempre el hook, condicionar el uso del valor.

- **React Compiler: evitar setState en useEffect** — preferir estado derivado con `useMemo`. setState en effect causa renders en cascada que el compilador detecta.

- **Modales anidados en Dashboard** — `Modal` trackea el conteo en `document.body.dataset.modalCount`. El overflow del body solo se restaura al cerrar el ÚLTIMO modal. No interferir al construir modales propios.

- **Zustand persist migrations** — al cambiar la estructura del store: incrementar `version` en `STORE_VERSIONS` y agregar función `migrate`. Usar `unknown` (no `any`) para `persistedState` y validar estructura antes de castear.

- **pwaWaiter: verificar asignación diaria** — el mozo debe estar asignado HOY a la sucursal. El token JWT no garantiza acceso si no hay asignación del día. La verificación es en cada login, no solo en el primer acceso.

- **pwaWaiter eventos con sector_id** — solo llegan al mozo asignado a ese sector. ADMIN/MANAGER reciben todos. No asumir que todos los eventos llegan a todos los usuarios del mismo rol.

- **usePagination resetea automáticamente a página 1** — usa `useLayoutEffect` con un ref flag para prevenir su propio bucle al filtrar. No reimplementar paginación manual.

- **Functional state updates en store async actions** — usar `set((state) => ...)` en lugar de leer state fuera del setter para evitar state stale después de un `await`.

- **React 19 `useOptimistic` en pwaMenu** — el hook `useOptimisticCart` hace rollback automático si la llamada al servidor falla. El estado optimista es temporal y se descarta con error.
