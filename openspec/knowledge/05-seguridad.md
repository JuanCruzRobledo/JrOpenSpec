# Seguridad y Autenticación

> Fuente de verdad para: foundation-auth, pwa-waiter, pwa-menu, dashboard, todas las fases con JWT

---

## Métodos de autenticación por contexto

| Contexto | Método | Header/Param |
|---------|--------|--------------|
| Dashboard, pwaWaiter | JWT | `Authorization: Bearer {token}` |
| pwaMenu (diners) | Table Token (HMAC) | `X-Table-Token: {token}` |
| WebSocket (staff) | JWT | Query param `?token=` |
| WebSocket (diners) | Table Token | Query param `?table_token=` |

---

## Tiempos de vida de tokens

| Token | Duración | Almacenamiento |
|-------|----------|----------------|
| Access Token (JWT) | 15 minutos | Memoria (no persistido en localStorage) |
| Refresh Token | 7 días | HttpOnly cookie (`credentials: 'include'`) |
| Table Token | 3 horas | Memoria / sessionStorage del diner |

---

## Estrategia de refresh de tokens

- Dashboard y pwaWaiter realizan un **refresh proactivo cada 14 minutos** (1 min antes del vencimiento del access token).
- Los refresh tokens se almacenan en **HttpOnly cookies** — inaccesibles desde JavaScript.
- Todas las requests que usen cookies deben incluir `credentials: 'include'` en fetch.
- El sistema mantiene una **blacklist de tokens en Redis** con patrón **fail-closed**: si Redis no responde, el token se considera inválido.

---

## Table Token (pwaMenu)

- Token basado en **HMAC** para autenticar diners en pwaMenu.
- Se pasa en el header `X-Table-Token: {token}`.
- Duración: **3 horas**.
- Se genera al iniciar una sesión de mesa y se invalida cuando la sesión cierra.
- Los endpoints `/api/diner/*` y `/api/customer/*` usan exclusivamente este mecanismo (sin JWT).
- Secret configurado via variable de entorno `TABLE_TOKEN_SECRET`.

---

## JWT — Estructura del payload

```python
{
    "sub": "42",          # user_id (string, convertir a int en backend)
    "tenant_id": 1,       # ID del tenant (restaurant)
    "branch_ids": [1, 2], # IDs de sucursales accesibles
    "roles": ["WAITER"]   # Roles del usuario
}
```

Secret configurado via `JWT_SECRET` (mínimo 32 caracteres).

---

## Extracción del contexto de usuario en backend

```python
user_id = int(user["sub"])       # "sub" contiene el user ID como string
tenant_id = user["tenant_id"]
branch_ids = user["branch_ids"]
roles = user["roles"]
```

---

## PermissionContext pattern

```python
from rest_api.services.permissions import PermissionContext

ctx = PermissionContext(user)
ctx.require_management()              # Raises ForbiddenError si no es ADMIN/MANAGER
ctx.require_branch_access(branch_id) # Raises ForbiddenError si branch no está en branch_ids
```

---

## Middlewares de seguridad

### SecurityHeadersMiddleware

Aplica a todas las respuestas:

| Header | Valor |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (solo en `ENVIRONMENT=production`) |
| `server` header | Eliminado de todas las respuestas |

### ContentTypeValidationMiddleware

- Valida que `POST`, `PUT` y `PATCH` usen `application/json` o `application/x-www-form-urlencoded`.
- Devuelve **HTTP 415** si el Content-Type no es válido.
- Paths exentos: `/api/billing/webhook`, `/api/health`.

### CORS

- **Producción**: lee orígenes de `ALLOWED_ORIGINS` (comma-separated).
- **Desarrollo**: usa `DEFAULT_CORS_ORIGINS` (puertos localhost 5173–5180, incluye `127.0.0.1` y `192.168.1.106`).
- `allow_credentials: true` (necesario para HttpOnly cookies).
- Headers permitidos: `Authorization`, `Content-Type`, `X-Table-Token`, `X-Request-ID`, `X-Requested-With`, `X-Device-Id`, `Accept`, `Accept-Language`, `Cache-Control`.
- Header expuesto al cliente: `X-Request-ID`.

### Rate Limiting (slowapi)

| Contexto | Límite |
|----------|--------|
| Endpoints públicos | 100/min |
| Endpoints autenticados | 30/min |
| Login | 5/min por email |
| Endpoints de billing | 5–20/min (más restrictivos) |

### Input Validation

`validate_image_url()` bloquea SSRF: rechaza IPs internas, cloud metadata endpoints y esquemas no-HTTP.

### WebSocket Origin Validation

El ws_gateway valida el origen de la conexión WebSocket contra la lista de orígenes permitidos antes de aceptarla.

---

## Flujo pre-login de pwaWaiter

El mozo selecciona la sucursal ANTES de hacer login:

1. `GET /api/public/branches` (sin auth) → lista de sucursales activas
2. Login estándar con JWT → `GET /api/waiter/verify-branch-assignment?branch_id={id}`
3. Si no está asignado HOY → pantalla "Acceso Denegado" con botón "Elegir otra sucursal"
4. Si está asignado → `assignmentVerified: true` + `selectedBranchId` en authStore

Archivo relevante: `pwaWaiter/src/stores/authStore.ts` (proactive refresh a los 14 min, branch assignment verification).

---

## RBAC

| Rol | Crear | Editar | Eliminar |
|-----|-------|--------|----------|
| ADMIN | Todo | Todo | Todo |
| MANAGER | Staff, Tables, Allergens, Promotions (propias sucursales) | Ídem | Nada |
| KITCHEN | Nada | Nada | Nada |
| WAITER | Nada | Nada | Nada |

Constantes centralizadas: `from shared.config.constants import Roles, MANAGEMENT_ROLES`

---

## WebSocket — Códigos de cierre

| Código | Significado |
|--------|-------------|
| `4001` | Auth failed (token inválido o expirado) |
| `4003` | Forbidden (rol insuficiente) |
| `4029` | Rate limited |

---

## Logout — Prevención de infinite loop

`authAPI.logout()` DEBE deshabilitar el retry en 401. Sin esto se produce el loop:

```
token expirado → 401 → onTokenExpired() → logout() → 401 → onTokenExpired() → loop infinito
```

Solución: pasar `false` como tercer argumento a `fetchAPI` en la llamada de logout para deshabilitar el retry automático.

Archivo relevante: `pwaWaiter/src/services/api.ts` (y equivalente en Dashboard y pwaMenu).

---

## Variables de entorno para producción

```env
JWT_SECRET=<mínimo 32 caracteres random>
TABLE_TOKEN_SECRET=<mínimo 32 caracteres random>
ALLOWED_ORIGINS=https://yourdomain.com
DEBUG=false
ENVIRONMENT=production
COOKIE_SECURE=true
```

---

## Gotchas y edge cases

- **Logout infinite loop**: `authAPI.logout()` debe deshabilitar retry en 401. Es el único lugar donde esto aplica.
- **CORS en desarrollo**: agregar un nuevo origen requiere actualizar DOS archivos: `backend/rest_api/core/cors.py` (DEFAULT_CORS_ORIGINS) y `ws_gateway/components/core/constants.py`.
- **Table codes NO son únicos entre sucursales**: la autenticación y resolución de sesiones debe incluir siempre `branch_slug` junto al código de mesa.
- **branch_ids en JWT**: es una lista. `require_branch_access()` valida contra esta lista. Un usuario con múltiples roles puede tener acceso a múltiples sucursales.
- **Rate limiting en billing**: más restrictivo que el resto (5–20/min). Tenerlo en cuenta en tests de integración y en flujos de pago de alta frecuencia.
- **HSTS solo en producción**: `Strict-Transport-Security` solo se agrega cuando `ENVIRONMENT=production`. En desarrollo no se agrega para evitar problemas con HTTP local.
- **Refresh token en HttpOnly cookie**: el frontend NUNCA puede leer este token via JS. El browser lo envía automáticamente con `credentials: 'include'`.
- **CSP `connect-src 'self'`**: las conexiones a la API deben ir desde el mismo origen. En producción, si el frontend y la API están en dominios distintos, esta directiva debe actualizarse.
- **CorrelationIdMiddleware**: se registra antes que todos los demás middlewares para que el `X-Request-ID` esté disponible en logs de toda la cadena.
- **Middleware execution order**: en FastAPI/Starlette los middlewares se ejecutan en orden inverso al de registro. CORS se registra último para ejecutarse primero (maneja preflight OPTIONS antes que cualquier otro middleware).
