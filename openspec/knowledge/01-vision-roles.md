# Visión del Producto y Roles
> Fuente de verdad para: todas las fases SDD, especialmente foundation-auth, pwa-waiter, pwa-menu, dashboard, table-session-domain

---

## Visión del producto

**Integrador** (nombre comercial: *Buen Sabor*) es una plataforma integral de gestión de restaurantes multi-sucursal que digitaliza la totalidad del flujo operativo: desde el momento en que un cliente escanea un código QR en la mesa hasta la finalización del pago, coordinando en tiempo real a comensales, mozos, cocina y administración.

**Problemas que resuelve:**

| # | Problema | Impacto sin el sistema |
|---|----------|----------------------|
| P1 | Toma de pedidos manual introduce errores, demoras y malentendidos | Platos devueltos, insatisfacción, pérdida de ingresos |
| P2 | Falta de visibilidad en tiempo real del estado de cada mesa y pedido | Cuellos de botella en cocina, mesas desatendidas, tiempos impredecibles |
| P3 | Gestión manual de múltiples sucursales con catálogos y precios diferentes | Inconsistencias de marca, costos administrativos altos |
| P4 | Ausencia de información sobre alérgenos y preferencias dietarias | Riesgo para la salud del comensal, exposición legal del restaurante |
| P5 | Facturación fragmentada (efectivo, digital, división de cuenta) | Errores de cobro, fugas de ingreso, cierre de caja lento |
| P6 | Imposibilidad de identificar clientes recurrentes ni personalizar la experiencia | Baja fidelización, oportunidades de upselling desperdiciadas |
| P7 | Comunicación entre roles dependiente de proximidad física | Pérdida de información, re-trabajo, estrés operativo |

**Propuesta de valor diferencial:**

| Valor | Descripción |
|-------|-------------|
| Pedido colaborativo desde el celular | Varios comensales arman un carrito compartido en tiempo real, sin depender del mozo |
| Operación 100% en tiempo real | WebSockets conectan todos los actores: un cambio en cocina se refleja instantáneamente en el mozo y el comensal |
| Multi-tenant y multi-sucursal | Un solo despliegue sirve a múltiples restaurantes con aislamiento total de datos; cada sucursal gestiona precios, sectores y personal de forma independiente |
| Seguridad alimentaria integrada | Catálogo de alérgenos con reacciones cruzadas, filtros dietarios avanzados y trazabilidad de ingredientes |
| Facturación flexible | División de cuenta por comensal, Mercado Pago, efectivo, tarjeta o transferencia — desde el celular o registrado por el mozo |
| PWA offline-ready | Las apps de mozo y comensal funcionan sin conexión estable; acciones se encolan y sincronizan al recuperar señal |
| Fidelización sin fricción | Reconocimiento de dispositivo → preferencias implícitas → perfil opt-in con consentimiento GDPR, sin obligar al comensal a registrarse |

---

## Componentes del sistema

| Componente | Puerto | Descripción |
|------------|--------|-------------|
| **Dashboard** | 5177 | Panel admin para gestión multi-sucursal (React 19 + Zustand). CRUD de sucursales, menú, staff, mesas, reportes. |
| **pwaMenu** | 5176 | PWA del comensal: menú digital con i18n (es/en/pt), carrito compartido multi-dispositivo, pedidos colaborativos, filtros de alérgenos. |
| **pwaWaiter** | 5178 | PWA del mozo: grilla de mesas por sector, comanda rápida, gestión de rondas, llamados de servicio, pagos manuales. |
| **backend** | 8000 | FastAPI REST API (PostgreSQL, Redis, JWT). Toda la lógica de negocio y persistencia. |
| **ws_gateway** | 8001 | WebSocket Gateway para eventos en tiempo real. Circuit breaker, rate limiting, Redis Streams, worker pool. |

**Stack tecnológico:** React 19.2 | Vite 7.2 | TypeScript 5.9 | Vitest | FastAPI 0.115 | SQLAlchemy 2.0 | PostgreSQL | Redis

---

## Usuarios y actores

| Perfil | Rol en el sistema | Objetivo principal | Acceso |
|--------|-------------------|--------------------|--------|
| **Administrador (ADMIN)** | Gestión total: sucursales, menú, personal, reportes | Controlar la operación y tomar decisiones basadas en datos | JWT — Dashboard |
| **Manager (MANAGER)** | Gestión parcial: staff, mesas, alérgenos, promociones en sus sucursales | Supervisar la operación diaria | JWT — Dashboard |
| **Mozo / Mesero (WAITER)** | Opera mesas asignadas: confirma pedidos, registra pagos, atiende llamados | Atender mesas con eficiencia y mínima fricción | JWT — pwaWaiter |
| **Cocina (KITCHEN)** | Recibe tickets, marca preparación, notifica platos listos | Priorizar y preparar pedidos sin errores | JWT — Vista cocina |
| **Comensal (DINER)** | Escanea QR, explora menú, arma pedido, paga | Pedir y pagar rápido con información clara | Table Token — pwaMenu |
| **Cliente fidelizado (CUSTOMER)** | Comensal recurrente con perfil opt-in | Recibir recomendaciones personalizadas y acumular historial | Table Token + perfil opt-in |
| **Operador de plataforma** | Gestiona tenants (restaurantes) | Ofrecer el servicio SaaS a múltiples clientes | Acceso directo a DB / superadmin |

---

## RBAC detallado

| Rol | Create | Edit | Delete |
|-----|--------|------|--------|
| **ADMIN** | Todo | Todo | Todo |
| **MANAGER** | Staff, Mesas, Alérgenos, Promociones (solo sus sucursales) | Staff, Mesas, Alérgenos, Promociones (solo sus sucursales) | Ninguno |
| **KITCHEN** | Ninguno | Ninguno | Ninguno |
| **WAITER** | Ninguno | Ninguno | Ninguno |

**Notas importantes sobre RBAC:**
- MANAGER solo puede gestionar entidades de sus sucursales asignadas (`branch_ids` en el JWT).
- KITCHEN solo puede cambiar el estado de los tickets que le corresponden (SUBMITTED → IN_KITCHEN → READY).
- WAITER puede confirmar rondas PENDING, registrar pagos manuales y cerrar mesas.
- ADMIN y MANAGER reciben TODOS los eventos WebSocket de la sucursal. Los WAITERs solo reciben eventos filtrados por sector.
- El envío de rondas a cocina (CONFIRMED → SUBMITTED) es exclusivo de ADMIN/MANAGER — no WAITER.

**Implementación:** `PermissionContext` + Strategy Pattern en el backend. 403 descriptivo ante acceso no autorizado.

---

## Flujos principales por rol

### Waiter (Mozo)

**Flujo pre-login (crítico — no puede saltarse):**
1. `GET /api/public/branches` → seleccionar sucursal (sin autenticación)
2. Login con credenciales → `POST /api/auth/login` → JWT
3. `GET /api/waiter/verify-branch-assignment?branch_id={id}` → verificar asignación HOY
4. Si no asignado ese día → pantalla "Acceso Denegado" (no puede continuar)
5. Si asignado → carga grilla de mesas agrupadas por sector

**Flujo operativo:**
- Ver grilla de mesas por sector con estados en tiempo real (WebSocket)
- Activar mesas sin QR del cliente (`POST /api/waiter/tables/{id}/activate`)
- Confirmar rondas PENDING → CONFIRMED
- Tomar comanda rápida para clientes sin celular (`GET /api/waiter/branches/{id}/menu` — menú compacto sin imágenes)
- Gestionar llamados de servicio (SERVICE_CALL_CREATED via Outbox)
- Registrar pagos manuales (`POST /api/waiter/payments/manual`)
- Cerrar mesa tras pago (`POST /api/waiter/tables/{id}/close`)

**Prioridad visual en cards de mesa:** service call (rojo) > ready (naranja) > status change (azul) > new order (amarillo) > check requested (púrpura)

### Diner (Comensal)

1. Escanear QR en mesa → `POST /api/tables/code/{code}/session`
   - Mesa FREE → crea nueva sesión OPEN
   - Mesa ACTIVE → se une a sesión existente
2. Registrar nombre y color (identificación en el carrito compartido)
3. Explorar menú por categorías/subcategorías, buscar, filtrar por alérgenos
4. Agregar ítems al carrito compartido (sincronizado por WebSocket con otros comensales de la misma mesa)
5. Votación grupal para confirmar pedido → ronda PENDING
6. Seguir estado del pedido en tiempo real (IN_KITCHEN → READY)
7. Solicitar cuenta (`POST /api/diner/check`) → mesa pasa a PAYING
8. Pagar con Mercado Pago o esperar al mozo para pago manual

### Admin / Manager

- Seleccionar sucursal activa en Dashboard (persiste en localStorage)
- CRUD completo de: sucursales, categorías, subcategorías, productos, precios por sucursal
- Gestión de staff: crear usuarios, asignar roles por sucursal, asignación diaria de mozos a sectores
- Gestión de mesas y sectores: grilla con estados en tiempo real
- Enviar rondas confirmadas a cocina (CONFIRMED → SUBMITTED)
- Ver todos los eventos de la sucursal via `/ws/admin`
- Acceder a reportes operativos, de cocina y de ventas

### Kitchen (Cocina)

- Conectar via `/ws/kitchen?token=JWT` → recibe eventos SUBMITTED+
- Ver tickets FIFO agrupados por estación (BAR / HOT_KITCHEN / COLD_KITCHEN)
- Cambiar estado: SUBMITTED → IN_KITCHEN → READY
- NO ve pedidos en estado PENDING ni CONFIRMED (solo SUBMITTED en adelante)
- Los eventos ROUND_READY usan Outbox pattern (garantía de entrega)

---

## Ciclo de vida de la sesión de mesa

```
FREE → [QR scan / mozo activa] → ACTIVE (sesión OPEN)
                                        ↓
                              [comensal solicita cuenta]
                                        ↓
                                    PAYING
                                        ↓
                              [mozo confirma pago]
                                        ↓
                                    CLOSED → mesa vuelve a FREE
```

**Estados de mesa:** FREE | ACTIVE | PAYING | OUT_OF_SERVICE

**Ciclo completo de rondas:**
```
PENDING → CONFIRMED → SUBMITTED → IN_KITCHEN → READY → SERVED
(Diner)   (Waiter)   (Admin/Mgr)   (Kitchen)  (Kitchen) (Staff)
```

**Formato de códigos de mesa:** alfanumérico (ej: "INT-01", "EXT-03"). El código identifica la mesa dentro de una sucursal.

---

## Gotchas y edge cases

- **Códigos de mesa NO son únicos globalmente**: el código "INT-01" puede existir en múltiples sucursales. Siempre se requiere `branch_slug` junto con el código para identificar una mesa unívocamente.
- **Asignación de mozo es diaria**: la tabla `WaiterSectorAssignment` registra por día y turno. Un mozo que trabajó ayer debe ser reasignado hoy; si no aparece en la asignación del día, el sistema le deniega el acceso aunque tenga rol WAITER activo en la sucursal.
- **Se puede seguir pidiendo en estado PAYING**: cuando la sesión está en PAYING (cuenta solicitada), los comensales aún pueden agregar ítems y enviar rondas. El cierre definitivo solo ocurre cuando el mozo confirma el pago y cierra la mesa.
- **Cocina nunca ve PENDING ni CONFIRMED**: el flujo de confirmación (mozo) y envío (admin/manager) existe para que cocina solo procese pedidos validados. Un mozo no puede saltar este paso.
- **Un mozo puede tener múltiples sectores asignados**: un WAITER puede estar asignado a más de un sector en el mismo día.
- **Precios en centavos**: todos los precios se almacenan como enteros en centavos (ej: $125.50 = 12550). La conversión es responsabilidad del frontend.
- **Sin precio en sucursal = producto no visible**: si un producto no tiene registro en `BranchProduct` para la sucursal activa, no aparece en el menú público.
- **Fidelización progresiva sin fricción**: el sistema reconoce dispositivos sin requerir registro. Phase 1 = device tracking silencioso; Phase 2 = preferencias implícitas; Phase 4 = perfil opt-in con consentimiento GDPR explícito.
- **Loop infinito en logout**: `authAPI.logout()` debe deshabilitar el retry en 401. Si no, el ciclo es: token expirado → 401 → onTokenExpired → logout() → 401 → loop. Se resuelve pasando `false` como tercer argumento a `fetchAPI`.
- **Refresh proactivo de tokens**: el frontend renueva el access token cada 14 minutos (antes de los 15 de expiración). Los refresh tokens se guardan en HttpOnly cookies (`credentials: 'include'`).
- **Outbox pattern para eventos críticos**: CHECK_REQUESTED/PAID, PAYMENT_*, ROUND_SUBMITTED/READY y SERVICE_CALL_CREATED usan el patrón Outbox para garantía de entrega. Los eventos de menor criticidad (CART_*, TABLE_*, ENTITY_*) se publican directamente a Redis.
- **Sector-based filtering en WebSocket**: los eventos con `sector_id` se entregan solo a los mozos asignados a ese sector. ADMIN y MANAGER siempre reciben todos los eventos de la sucursal.
- **Multi-tenancy estricto**: `tenant_id` está presente en todas las entidades y se filtra automáticamente en todas las queries. Los catálogos de cocción, sabor, textura y cocina son por tenant.
- **pwaMenu i18n obligatoria**: TODO el texto visible al usuario en pwaMenu debe usar `t()`. Cero strings hardcodeados. Idiomas: es/en/pt.
