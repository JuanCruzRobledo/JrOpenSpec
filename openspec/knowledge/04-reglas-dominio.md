# Reglas de Dominio y Lógica de Negocio

> Fuente de verdad para: order-domain, billing-domain, table-session-domain, pwa-waiter, pwa-menu, dashboard
>
> Fuentes utilizadas: `SDD/Specs/03_ReglasDeNegocio.md`, `CLAUDE.md`, `Dashboard/CLAUDE.md`, `pwaWaiter/CLAUDE.md`

---

## Multi-Tenancy y Aislamiento

| ID | Regla | Consecuencia de violación |
|----|-------|--------------------------|
| RN-001 | Toda entidad principal DEBE contener `tenant_id` como campo obligatorio | Fuga de datos entre restaurantes |
| RN-002 | Toda query DEBE filtrar por `tenant_id` del usuario autenticado, sin excepción | Acceso cruzado entre tenants |
| RN-003 | Los catálogos de dominio (CookingMethod, FlavorProfile, TextureProfile, CuisineType) son tenant-scoped | Contaminación de catálogos |
| RN-004 | Un usuario solo puede pertenecer a un tenant | Integridad del modelo |

---

## Ciclo de Vida del Round (Pedido)

### Estados

```
PENDING → CONFIRMED → SUBMITTED → IN_KITCHEN → READY → SERVED
   │            │
   └─→ CANCELED └─→ CANCELED
```

- `CANCELED` es un estado terminal; no hay recuperación posible.
- No se pueden saltar estados — la transición debe ser estrictamente secuencial.

### Restricciones por rol

| Transición | Rol autorizado |
|-----------|---------------|
| Crear (→ PENDING) | DINER (desde carrito compartido) o WAITER (Autogestión) |
| PENDING → CONFIRMED | WAITER |
| CONFIRMED → SUBMITTED | ADMIN / MANAGER |
| SUBMITTED → IN_KITCHEN | KITCHEN |
| IN_KITCHEN → READY | KITCHEN |
| READY → SERVED | WAITER / cualquier staff |
| PENDING o CONFIRMED → CANCELED | WAITER / ADMIN |

**Regla critica:** Cocina (KITCHEN) NO ve rondas en estado PENDING ni CONFIRMED. Solo puede ver y operar sobre rondas a partir de SUBMITTED.

### Tabla completa de transiciones

| Estado actual | Nuevo estado | Quién puede hacerlo | Condiciones |
|--------------|-------------|---------------------|-------------|
| (nuevo) | PENDING | DINER / WAITER | Carrito no vacío |
| PENDING | CONFIRMED | WAITER | Verificación física en mesa |
| PENDING | CANCELED | WAITER / ADMIN | Solo en estos dos estados |
| CONFIRMED | SUBMITTED | ADMIN / MANAGER | — |
| CONFIRMED | CANCELED | WAITER / ADMIN | Solo en estos dos estados |
| SUBMITTED | IN_KITCHEN | KITCHEN | — |
| IN_KITCHEN | READY | KITCHEN | — |
| READY | SERVED | WAITER / staff | — |

### Eventos WebSocket asociados

| Transición | Evento WS emitido | Patrón de entrega |
|-----------|-------------------|-------------------|
| → PENDING | `ROUND_PENDING` | Direct Redis |
| PENDING → CONFIRMED | `ROUND_CONFIRMED` | Direct Redis |
| CONFIRMED → SUBMITTED | `ROUND_SUBMITTED` | Outbox (garantizado) |
| SUBMITTED → IN_KITCHEN | `ROUND_IN_KITCHEN` | Direct Redis |
| IN_KITCHEN → READY | `ROUND_READY` | Outbox (garantizado) |
| READY → SERVED | `ROUND_SERVED` | Direct Redis |
| → CANCELED | `ROUND_CANCELED` | Direct Redis |

### Routing de eventos de round

| Evento | Admin/Manager | Kitchen | Waiters | Diners |
|--------|--------------|---------|---------|--------|
| `ROUND_PENDING` | si | no | si (toda la sucursal) | no |
| `ROUND_CONFIRMED` | si | no | si | no |
| `ROUND_SUBMITTED` | si | si | si | no |
| `ROUND_IN_KITCHEN` y posteriores | si | si | si | si |

Eventos con `sector_id` se envían SOLO a los mozos asignados a ese sector. ADMIN/MANAGER siempre reciben todos los eventos de su sucursal.

### Reglas adicionales de rondas

| ID | Regla |
|----|-------|
| RN-063 | Cada RoundItem DEBE tener `qty > 0` y `unit_price_cents >= 0` |
| RN-064 | Una ronda usa `idempotency_key` para prevenir envíos duplicados |
| RN-065 | Si al eliminar un ítem la ronda queda vacía, la ronda se elimina automáticamente |
| RN-066 | Los ítems de una ronda se combinan de todos los comensales de la mesa |

---

## Ciclo de Vida de la Sesión de Mesa

### Estados

```
            ┌──────────────────┐
            │  OUT_OF_SERVICE  │
            └──────────────────┘
                    ↑↓
┌──────┐     ┌──────────┐     ┌─────────┐
│ FREE │ ──→ │  ACTIVE  │ ──→ │ PAYING  │ ──→ FREE
└──────┘     └──────────┘     └─────────┘
 (QR scan /    (pedidos en      (CHECK_REQUESTED,
  waiter        curso)           aún puede pedir)
  activate)
```

### Reglas

| ID | Regla |
|----|-------|
| RN-050 | Una mesa SOLO puede tener una sesión OPEN (ACTIVE) a la vez |
| RN-051 | Los estados de mesa son: FREE → ACTIVE → PAYING → FREE (ciclo) + OUT_OF_SERVICE (lateral) |
| RN-052 | Los comensales PUEDEN seguir haciendo pedidos mientras la mesa está en estado PAYING |
| RN-053 | El table token contiene: table_id, session_id, diner_id, branch_id — y es intransferible |
| RN-054 | El campo `cart_version` en TableSession permite optimistic locking en operaciones de carrito |
| RN-021 | El código de mesa es alfanumérico (ej: "INT-01") y único dentro de la sucursal, NO globalmente — se requiere `branch_slug` |
| RN-020 | El slug de sucursal DEBE ser único dentro del tenant |
| RN-086 | La mesa no puede cerrarse si el Check no está PAID |

---

## Reglas de Billing

### Estados del Check

```
OPEN ──→ REQUESTED ──→ IN_PAYMENT ──→ PAID
                                   └──→ FAILED
```

### Invariantes

| ID | Regla |
|----|-------|
| RN-080 | Un Check (tabla `app_check`) corresponde a una sesión de mesa |
| RN-081 | `total_cents >= 0`, `paid_cents <= total_cents` y `paid_cents >= 0` — invariantes CHECK en DB |
| RN-082 | Solo se cobran ítems de rondas NO canceladas |
| RN-083 | Los pagos usan Allocation FIFO para vincular Payment → Charge |
| RN-084 | `amount_cents > 0` en Payment y en Charge — no se aceptan montos cero o negativos |
| RN-085 | Si `paid_cents == total_cents` → Check pasa a PAID automáticamente |
| RN-087 | Los eventos de billing (CHECK_*, PAYMENT_*) DEBEN usar Outbox pattern para garantizar entrega |
| RN-088 | Rate limiting en endpoints de billing: 5–20 req/min según endpoint |

### Métodos de pago

| Método | Proveedor | Registrado por |
|--------|-----------|----------------|
| Digital | Mercado Pago | SYSTEM (webhook) o DINER |
| Efectivo | — | WAITER (manual) |
| Tarjeta | — | WAITER (manual) |
| Transferencia | — | WAITER (manual) |

---

## Kitchen Tickets

| ID | Regla |
|----|-------|
| RN-090 | Se genera KitchenTicket al transicionar la ronda a SUBMITTED |
| RN-091 | Los tickets se agrupan por estación (station): BAR, HOT_KITCHEN, COLD_KITCHEN |
| RN-092 | Estados del ticket: PENDING → IN_PROGRESS → READY → DELIVERED |
| RN-093 | No se puede saltar estados en tickets |

---

## Reglas de ServiceCall

| ID | Regla |
|----|-------|
| RN-100 | Tipos: WAITER_CALL, PAYMENT_HELP, OTHER |
| RN-101 | Estados: OPEN → ACKED → CLOSED |
| RN-102 | SERVICE_CALL_CREATED usa Outbox pattern (entrega garantizada) |
| RN-103 | Solo el mozo asignado al sector (o ADMIN/MANAGER) puede resolver llamados |

El evento `SERVICE_CALL_CREATED` dispara alerta sonora + animación roja en pwaWaiter. La resolución se realiza via `POST /waiter/service-calls/{id}/resolve`.

---

## Reglas de Asignación de Mozos

| ID | Regla |
|----|-------|
| RN-023 | Un mozo SOLO puede acceder a la sucursal si tiene WaiterSectorAssignment para la fecha actual |
| RN-024 | Las asignaciones de mozo son por día y turno — no persisten entre jornadas |

**Flujo pre-login del mozo:**
1. `GET /api/public/branches` — seleccionar sucursal (sin autenticación)
2. Login con JWT
3. `GET /api/waiter/verify-branch-assignment?branch_id={id}` — debe estar asignado HOY
4. Si no está asignado → pantalla "Acceso Denegado"
5. Si está asignado → acceso a MainPage

Un mozo puede estar asignado a múltiples sectores. Solo ve las mesas de sus sectores asignados; ADMIN/MANAGER ven todas las mesas de la sucursal.

---

## Reglas del Carrito Compartido (pwaMenu)

| ID | Regla |
|----|-------|
| RN-070 | El carrito es por sesión de mesa, visible para todos los comensales |
| RN-071 | Solo el comensal que agregó un ítem puede modificarlo o eliminarlo |
| RN-072 | La cantidad por ítem está acotada entre 1 y 99 (`CHECK qty > 0 AND qty <= 99`) |
| RN-073 | `UNIQUE(session_id, diner_id, product_id)` — un comensal no puede tener duplicados del mismo producto (se hace UPSERT) |
| RN-074 | Al enviar la ronda, el carrito se limpia (evento CART_CLEARED) |
| RN-075 | Conflictos de concurrencia se resuelven por orden de llegada al servidor |

Los items del carrito muestran qué comensal los agregó (nombre/color del diner). Al hacer submit, todos los items de todos los diners se combinan en una sola ronda.

---

## Comanda Rápida (pwaWaiter — Autogestión)

El mozo puede tomar pedidos para clientes sin teléfono mediante la pestaña "Autogestión":

- Endpoint compacto sin imágenes: `GET /api/waiter/branches/{id}/menu`
- Para mesas FREE: el mozo activa la mesa ingresando cantidad de comensales → `POST /api/waiter/tables/{id}/activate`
- Para mesas ACTIVE: usa la sesión existente
- El round resultante pasa a estado PENDING y sigue el flujo normal de confirmación

---

## Reglas de Customer / Diner y Fidelización

| ID | Regla |
|----|-------|
| RN-130 | Fase 1 (Device Tracking): fingerprint de dispositivo sin consentimiento (anonymous) |
| RN-131 | Fase 2 (Preferencias Implícitas): se registran filtros de alérgenos y cocción usados por el dispositivo |
| RN-132 | Fase 4 (Opt-In): requiere consentimiento GDPR explícito y revocable (`consent_remember`, `consent_marketing`, `consent_date`) |
| RN-133 | El campo `ai_personalization_enabled` requiere opt-in adicional |
| RN-134 | Customer tiene únicos condicionales: `(tenant_id, phone)` y `(tenant_id, email)` cuando no son NULL |

---

## Reglas del Catálogo de Menú

| ID | Regla |
|----|-------|
| RN-030 | La jerarquía del menú es estrictamente: Categoría → Subcategoría → Producto |
| RN-031 | Los nombres de categoría DEBEN ser únicos dentro de la sucursal (`UNIQUE(branch_id, name)`) |
| RN-032 | Los nombres de subcategoría DEBEN ser únicos dentro de la categoría (`UNIQUE(category_id, name)`) |
| RN-033 | Un producto DEBE tener un BranchProduct para ser visible en una sucursal |
| RN-034 | El precio se almacena en centavos como entero (`price_cents >= 0`); conversión: backend cents ↔ frontend pesos (÷100) |
| RN-035 | Al soft-delete una categoría se desactivan en cascada subcategorías y productos |
| RN-036 | Al soft-delete una subcategoría se desactivan en cascada los productos asociados |
| RN-037 | Las URLs de imágenes DEBEN pasar validación SSRF (bloqueo IPs internas, cloud metadata) |

---

## Reglas de Alérgenos y Seguridad Alimentaria

| ID | Regla |
|----|-------|
| RN-040 | La asociación ProductAllergen incluye obligatoriamente `presence_type` (CONTAINS, MAY_CONTAIN, FREE_FROM) y `risk_level` |
| RN-041 | `UNIQUE(product_id, allergen_id, presence_type)` — un producto no puede tener duplicados de la misma combinación |
| RN-042 | Las reacciones cruzadas (AllergenCrossReaction) DEBEN considerarse al filtrar menú para el comensal |
| RN-043 | Severity levels: mild, moderate, severe, life_threatening — impactan prioridad de visualización |
| RN-044 | Los 14 alérgenos principales DEBEN estar pre-cargados en el seed de cada tenant |

---

## Reglas de Autenticación y Tokens

| ID | Regla |
|----|-------|
| RN-010 | Access token JWT tiene validez de 15 minutos; refresh token 7 días (HttpOnly cookie) |
| RN-011 | Table token HMAC tiene validez de 3 horas y se transmite en header `X-Table-Token` |
| RN-012 | Un token de refresh usado se invalida inmediatamente en la blacklist de Redis |
| RN-013 | El logout DEBE deshabilitar retry en 401 para evitar loop infinito |
| RN-014 | La blacklist de tokens opera en modo fail-closed: si Redis no responde, se deniega acceso |

Dashboard y pwaWaiter refrescan el token proactivamente cada 14 minutos.

---

## Soft Delete y Auditoría

| ID | Regla |
|----|-------|
| RN-120 | Toda entidad hereda AuditMixin: `is_active`, `created_at`, `updated_at`, `deleted_at` |
| RN-121 | El soft delete registra `deleted_by_id`, `deleted_by_email` y `deleted_at` |
| RN-122 | Las queries DEBEN filtrar por `is_active = True` por defecto |
| RN-123 | El cascade soft delete propaga desactivación a entidades dependientes |

---

## WebSocket — Reglas de Infraestructura

| ID | Regla |
|----|-------|
| RN-110 | Heartbeat: cliente envía ping cada 30s; servidor cierra conexión tras 60s sin actividad |
| RN-111 | Close codes: 4001 (auth failed), 4003 (forbidden), 4029 (rate limited) |
| RN-112 | Eventos con `sector_id` se envían SOLO a mozos asignados a ese sector |
| RN-113 | ADMIN/MANAGER siempre reciben todos los eventos de su branch |
| RN-114 | Eventos críticos (billing, round SUBMITTED/READY, service call) usan Redis Streams (at-least-once) |
| RN-115 | Eventos de menor criticidad (cart, status change, entity CRUD) usan Redis Pub/Sub (at-most-once) |

---

## Convenciones Globales

| ID | Regla |
|----|-------|
| RN-150 | IDs en frontend: `crypto.randomUUID()` (string); en backend: BigInteger (numeric) |
| RN-151 | Conversión IDs: `String(backendId)` en frontend, `parseInt(frontendId, 10)` en backend |
| RN-152 | UI en español, comentarios de código en inglés |
| RN-153 | Color accent: naranja `#f97316` |
| RN-154 | pwaMenu: TODOS los textos de UI deben usar `t()` — cero hardcoded strings (soporta es/en/pt) |
| RN-155 | Comparación de booleanos SQLAlchemy: `.is_(True)`, nunca `== True` |
| RN-156 | Tablas con nombres reservados SQL usan prefijo: `Check` → `__tablename__ = "app_check"` |

---

## Gotchas y Edge Cases

- **Kitchen no ve PENDING/CONFIRMED.** Solo ve rondas a partir de SUBMITTED. Si la cocina no recibe un pedido, verificar que el manager/admin lo haya enviado.
- **Se puede pedir durante PAYING.** El estado PAYING no bloquea nuevos pedidos — los comensales pueden seguir agregando ítems mientras se gestiona el cobro.
- **La asignación del mozo es DIARIA.** Un mozo con rol WAITER en la sucursal pero sin WaiterSectorAssignment para HOY no puede acceder — recibirá "Acceso Denegado".
- **CANCELED es terminal.** No existe transición de salida desde CANCELED; una ronda cancelada no puede recuperarse.
- **Códigos de mesa NO son únicos globalmente.** "INT-01" puede existir en múltiples sucursales. Siempre referenciar con `branch_slug`.
- **Carrito vacío = ronda eliminada.** Si el último ítem de una ronda PENDING/CONFIRMED es eliminado, la ronda desaparece automáticamente.
- **Idempotency key en rondas.** El campo `idempotency_key` previene que un doble-submit del cliente genere dos rondas.
- **Outbox para billing y service calls.** Los eventos CHECK_*, PAYMENT_*, ROUND_SUBMITTED, ROUND_READY y SERVICE_CALL_CREATED van por Outbox (no Redis Pub/Sub directo) para garantizar entrega ante fallos.
- **Logout sin retry en 401.** En `api.ts`, `authAPI.logout()` debe llamar a `fetchAPI` con retry deshabilitado. De lo contrario: token expirado → 401 → onTokenExpired → logout() → 401 → loop infinito.
- **Soft delete en cascada.** Eliminar una categoría desactiva subcategorías y productos. Eliminar una subcategoría desactiva sus productos. Los datos no se borran físicamente.
- **Precios en centavos.** Backend almacena y recibe siempre enteros en centavos. Frontend muestra y envía en pesos (÷100 para mostrar, ×100 para enviar).
