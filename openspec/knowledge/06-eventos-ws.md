# Eventos WebSocket y Tiempo Real
> Fuente de verdad para: realtime-infra, order-domain, billing-domain, table-session-domain, pwa-waiter, pwa-menu, dashboard

## Endpoints WebSocket

| Endpoint | Auth | Roles requeridos | Uso |
|----------|------|-----------------|-----|
| `/ws/waiter?token=JWT` | JWT | WAITER, MANAGER, ADMIN | Notificaciones de meseros (sector-targeted) |
| `/ws/kitchen?token=JWT` | JWT | KITCHEN, MANAGER, ADMIN | Notificaciones de cocina |
| `/ws/diner?table_token=` | Table Token (HMAC) | N/A (token de sesión) | Actualizaciones en tiempo real del comensal |
| `/ws/admin?token=JWT` | JWT | MANAGER, ADMIN | Notificaciones del dashboard administrativo |

Puerto: **8001**

---

## Catálogo completo de eventos

### Round lifecycle
| Evento | Descripción |
|--------|-------------|
| `ROUND_PENDING` | Ronda creada, pendiente de confirmación del mesero |
| `ROUND_CONFIRMED` | Mesero confirmó la ronda |
| `ROUND_SUBMITTED` | Admin/Manager aprobó y envió a cocina |
| `ROUND_IN_KITCHEN` | Cocina recibió y está preparando |
| `ROUND_READY` | Cocina terminó la preparación |
| `ROUND_SERVED` | Pedido entregado a la mesa |
| `ROUND_CANCELED` | Pedido cancelado |

### Cart sync
| Evento | Descripción |
|--------|-------------|
| `CART_ITEM_ADDED` | Item agregado al carrito compartido |
| `CART_ITEM_UPDATED` | Item modificado en el carrito |
| `CART_ITEM_REMOVED` | Item eliminado del carrito |
| `CART_CLEARED` | Carrito vaciado completamente |

### Service calls
| Evento | Descripción |
|--------|-------------|
| `SERVICE_CALL_CREATED` | Cliente solicitó atención |
| `SERVICE_CALL_ACKED` | Mesero en camino |
| `SERVICE_CALL_CLOSED` | Atención completada |

### Billing
| Evento | Descripción |
|--------|-------------|
| `CHECK_REQUESTED` | Cliente solicitó la cuenta |
| `CHECK_PAID` | Cuenta pagada completamente |
| `PAYMENT_APPROVED` | Pago individual aprobado |
| `PAYMENT_REJECTED` | Pago rechazado |
| `PAYMENT_FAILED` | Error en procesamiento del pago |

### Tables
| Evento | Descripción |
|--------|-------------|
| `TABLE_SESSION_STARTED` | QR escaneado, sesión de mesa creada |
| `TABLE_CLEARED` | Mesa liberada |
| `TABLE_STATUS_CHANGED` | Cambio de estado de la mesa |

### Kitchen tickets
| Evento | Descripción |
|--------|-------------|
| `TICKET_IN_PROGRESS` | Cocina preparando el ticket |
| `TICKET_READY` | Ticket listo para servir |
| `TICKET_DELIVERED` | Ticket entregado |

### Admin (CRUD)
| Evento | Descripción |
|--------|-------------|
| `ENTITY_CREATED` | Entidad creada |
| `ENTITY_UPDATED` | Entidad modificada |
| `ENTITY_DELETED` | Entidad eliminada |
| `CASCADE_DELETE` | Eliminación en cascada |

---

## Routing de eventos por rol

| Evento | Admin/Manager | Kitchen | Waiters | Diners |
|--------|--------------|---------|---------|--------|
| `ROUND_PENDING` | si | no | si (toda la sucursal) | no |
| `ROUND_CONFIRMED` | si | no | si | no |
| `ROUND_SUBMITTED` | si | si | si | no |
| `ROUND_IN_KITCHEN` | si | si | si | si |
| `ROUND_READY` | si | si | si | si |
| `ROUND_SERVED` | si | si | si | si |
| `ROUND_CANCELED` | si | si | si | si |
| `CART_ITEM_*` | no | no | no | si (misma sesión) |
| `CART_CLEARED` | no | no | no | si (misma sesión) |
| `SERVICE_CALL_CREATED` | si | no | si | no |
| `SERVICE_CALL_ACKED` | si | no | si | no |
| `SERVICE_CALL_CLOSED` | si | no | si | no |
| `CHECK_REQUESTED` | si | no | si | si |
| `CHECK_PAID` | si | no | si | si |
| `PAYMENT_APPROVED` | si | no | si | si |
| `PAYMENT_REJECTED` | si | no | si | si |
| `TABLE_SESSION_STARTED` | si | no | si | no |
| `TABLE_CLEARED` | si | no | si | no |
| `TABLE_STATUS_CHANGED` | si | no | si | no |
| `TICKET_*` | si | si | no | no |
| `ENTITY_CREATED/UPDATED/DELETED` | si | no | no | no |
| `CASCADE_DELETE` | si | no | no | no |

**Regla clave**: Kitchen NO recibe `ROUND_PENDING` ni `ROUND_CONFIRMED`. Los pedidos pasan primero por Dashboard donde un admin los aprueba antes de que cocina los vea (a partir de `ROUND_SUBMITTED`).

---

## Sector-based filtering

- Eventos que incluyen `sector_id` se envían **solo** a los meseros asignados a ese sector ese día.
- Eventos sin `sector_id` se envían a todos los meseros de la sucursal.
- ADMIN y MANAGER siempre reciben **todos** los eventos de sus sucursales, sin importar el sector.
- El mesero puede enviar el comando `refresh_sectors` para recargar sus asignaciones de sector desde la base de datos.
- Las asignaciones de sector se cachean con TTL de 5 minutos para evitar queries repetidas.

### Canales Redis usados por el backend

```
channel:branch:{branch_id}:waiters              # Eventos para meseros
channel:branch:{branch_id}:kitchen              # Eventos para cocina
channel:branch:{branch_id}:admin                # Eventos para dashboard
channel:sector:{branch_id}:{sector_id}:waiters  # Eventos específicos de sector
channel:session:{session_id}                    # Eventos para comensales
```

---

## Outbox Pattern (Guaranteed Delivery)

### Qué eventos usan Outbox (nunca se pueden perder)

- `CHECK_REQUESTED`, `CHECK_PAID`
- `PAYMENT_APPROVED`, `PAYMENT_REJECTED`, `PAYMENT_FAILED`
- `ROUND_SUBMITTED`, `ROUND_READY`
- `SERVICE_CALL_CREATED`

Estos eventos se escriben en la base de datos de forma **atómica** con la operación de negocio, y un procesador de fondo los publica a Redis. Si Redis falla al momento del commit, el evento no se pierde — el procesador lo reintentará.

### Qué eventos usan Direct Redis (menor latencia)

- `ROUND_CONFIRMED`, `ROUND_IN_KITCHEN`, `ROUND_SERVED`
- `CART_ITEM_ADDED`, `CART_ITEM_UPDATED`, `CART_ITEM_REMOVED`, `CART_CLEARED`
- `TABLE_SESSION_STARTED`, `TABLE_CLEARED`, `TABLE_STATUS_CHANGED`
- `ENTITY_CREATED`, `ENTITY_UPDATED`, `ENTITY_DELETED`

Estos se publican directamente a Redis sin pasar por la tabla de outbox.

### Cómo usar Outbox en código

```python
from rest_api.services.events.outbox_service import write_billing_outbox_event

write_billing_outbox_event(
    db=db,
    tenant_id=tenant_id,
    event_type=CHECK_REQUESTED,
    branch_id=branch_id,
    session_id=session_id,
    data={...}
)
db.commit()  # Atómico con la operación de negocio
```

### Cómo publicar eventos directos

```python
from shared.infrastructure.events import publish_event, ROUND_SUBMITTED

await publish_event(
    redis_pool,
    f"channel:branch:{branch_id}:waiters",
    {
        "type": ROUND_SUBMITTED,
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "sector_id": sector_id,   # opcional — activa filtrado por sector
        "round_id": round.id,
        "data": {...}
    }
)
```

---

## Heartbeat

- **Cliente envía** cada 30 segundos: `{"type": "ping"}` (también acepta el string simple `"ping"`)
- **Gateway responde**: `{"type": "pong"}`
- **Timeout del servidor**: 60 segundos sin heartbeat → conexión marcada como stale y cerrada
- **Limpieza periódica**: un task corre cada 30 segundos para detectar y cerrar conexiones stale y dead

---

## Códigos de cierre WebSocket

| Código | Constante | Significado |
|--------|-----------|-------------|
| 1000 | NORMAL | Cierre normal |
| 1001 | GOING_AWAY | Servidor apagándose |
| 1008 | POLICY_VIOLATION | Origen no permitido |
| 1009 | MESSAGE_TOO_BIG | Mensaje excede 64KB |
| 1013 | SERVER_OVERLOADED | Límite de conexiones alcanzado (max 1000 total, 3 por usuario) |
| 4001 | AUTH_FAILED | Token inválido o expirado |
| 4003 | FORBIDDEN | Rol insuficiente u origen inválido |
| 4029 | RATE_LIMITED | Exceso de mensajes (límite: 20 msg/seg por conexión) |

---

## Arquitectura interna del WS Gateway

### Componentes principales

```
ws_gateway/
├── main.py                    # Punto de entrada FastAPI
├── connection_manager.py      # Orquestador de conexiones (thin, ~463 líneas)
├── redis_subscriber.py        # Orquestador de suscripción Redis (thin, ~326 líneas)
├── core/
│   ├── connection/            # lifecycle, broadcaster, cleanup, stats
│   └── subscriber/            # drop_tracker, validator, processor, stream_consumer
└── components/
    ├── auth/strategies.py     # JWT, TableToken, Composite, Null (testing)
    ├── broadcast/router.py    # Estrategias de broadcast + filtrado multi-tenant
    ├── connection/            # index, locks, heartbeat, rate_limiter
    ├── events/router.py       # Enrutamiento de eventos por tipo
    ├── resilience/            # circuit_breaker, retry con jitter
    └── metrics/               # collector Prometheus
```

### Patrones implementados

- **Composición**: `connection_manager` y `redis_subscriber` son orquestadores delgados que componen módulos especializados. No son monolitos.
- **Strategy** (Auth): `JWTAuthStrategy`, `TableTokenAuthStrategy`, `CompositeAuthStrategy`, `NullAuthStrategy` (testing).
- **Template Method** (Endpoints): `WebSocketEndpointBase` define el ciclo de vida; cada endpoint hereda e implementa solo lo específico.
- **Observer** (Métricas): `BroadcastRouter` notifica a observadores con resultados de broadcast sin acoplar métricas a lógica de envío.
- **Circuit Breaker**: protege contra cascadas cuando Redis no está disponible. 5 fallos consecutivos → OPEN (falla rápido por 30s) → HALF_OPEN (prueba recuperación).

### Rendimiento y concurrencia

- **Broadcast paralelo**: lotes de 50 conexiones con `asyncio.gather()` → broadcast a 400 usuarios en ~160ms (vs ~4s en serie).
- **Sharded locks por sucursal**: locks independientes por `branch_id` reducen contención un 90%. El lock de la sucursal 1 no bloquea a la sucursal 2.
- **Índices O(1)**: búsquedas por usuario, sucursal, sector, sesión y rol admin sin escaneo lineal.
- **Multi-tenant estricto**: todos los broadcasts filtran por `tenant_id` antes de enviar. Los eventos de un restaurante nunca llegan a clientes de otro.
- **Capacidad**: diseñado para 400–600 usuarios concurrentes con latencias de broadcast < 200ms.

### Redis Streams (entrega garantizada)

- Consumer group sobre Redis Streams para eventos críticos.
- **At-least-once delivery**: si el procesamiento falla, el mensaje se reintenta.
- **DLQ**: mensajes que fallan repetidamente se mueven a Dead Letter Queue.
- El archivo relevante es `ws_gateway/core/subscriber/stream_consumer.py`.

### Event Queue (backpressure)

- Buffer interno con capacidad de 5000 eventos.
- Al saturarse, descarta los eventos más antiguos (deque con maxlen).
- **Drop Tracker**: monitorea tasa de descarte en ventana de 60s. Si supera 5% → alerta (con cooldown de 5 min para no saturar logs).

---

## Seguridad

### JWT revalidation periódica

Cada 5 minutos el gateway verifica que el token no esté en la blacklist de Redis. Esto detecta logouts y revocaciones sin esperar a la expiración natural (tokens viven 15 min).

### Validación de origen

Los endpoints JWT validan el header `Origin` contra `ALLOWED_ORIGINS`. Los endpoints de Table Token (diners) no validan origen para soportar apps móviles.

---

## Gotchas y edge cases

- **Kitchen NO ve ROUND_PENDING ni ROUND_CONFIRMED**: kitchen solo ve pedidos a partir de `ROUND_SUBMITTED`. El flujo correcto es Diner → PENDING → Waiter confirma → CONFIRMED → Admin envía → SUBMITTED → Kitchen.
- **ROUND_IN_KITCHEN y posteriores llegan a Diners también**: los comensales ven el progreso de su pedido a partir de que entra a cocina, no antes.
- **sector_id en eventos activa filtrado automático**: si un evento incluye `sector_id`, el gateway lo envía solo a los meseros asignados a ese sector ese día. Si no incluye `sector_id`, va a todos los meseros de la sucursal.
- **WS Gateway requiere PYTHONPATH**: necesita acceso a módulos del backend. Siempre iniciar con `PYTHONPATH=$PWD/backend` (o `$env:PYTHONPATH = "$PWD\backend"` en PowerShell).
- **Windows StatReload puede fallar**: rutas nuevas en el backend pueden requerir reinicio manual de uvicorn en Windows.
- **Imports: ambas rutas funcionan**: tanto `from ws_gateway.components import X` (forma antigua) como `from ws_gateway.components.broadcast.router import X` (forma nueva) son válidas.
- **Desconexiones cada ~30s**: si el cliente no implementa el heartbeat (ping cada 30s), el servidor cierra la conexión por timeout a los 60s. Verificar también expiración del JWT.
- **Conexiones dead no interrumpen broadcasts**: si una conexión falla durante el envío, se marca como "dead" en lugar de abortar el broadcast completo. Un proceso de limpieza la retira luego.
- **Logout infinite loop prevention**: en `api.ts` del frontend, `authAPI.logout()` debe deshabilitar retry en 401. Si no, el token expirado genera 401 → `onTokenExpired` → `logout()` → 401 → bucle infinito.
- **Límite de conexiones**: máximo 3 conexiones por usuario y 1000 totales. Superarlos resulta en cierre con código 1013.
