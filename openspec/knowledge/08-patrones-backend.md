# Patrones Backend
> Fuente de verdad para: todas las fases backend — foundation-auth, tenant-branch-core, menu-domain, table-session-domain, order-domain, billing-domain, realtime-infra

## Clean Architecture — capas

```
ROUTERS (thin controllers - HTTP only)
    → DOMAIN SERVICES (business logic: rest_api/services/domain/)
        → REPOSITORIES (data access: rest_api/services/crud/repository.py)
            → MODELS (SQLAlchemy: rest_api/models/)
```

### Regla de oro: Routers THIN

- Los routers deben contener SOLO: `Depends` + `PermissionContext` + llamada al service. Sin lógica de negocio.
- **CRUDFactory está DEPRECADO** — usar Domain Services para toda funcionalidad nueva.
- Todo acceso a datos va por Repository, nunca queries directas en el router.

---

## Domain Services

### Crear un nuevo Domain Service (pasos obligatorios)

```python
# 1. Crear en rest_api/services/domain/my_entity_service.py
from rest_api.services.base_service import BranchScopedService
from shared.utils.admin_schemas import MyEntityOutput

class MyEntityService(BranchScopedService[MyEntity, MyEntityOutput]):
    def __init__(self, db: Session):
        super().__init__(
            db=db,
            model=MyEntity,
            output_schema=MyEntityOutput,
            entity_name="Mi Entidad",
        )

    def _validate_create(self, data: dict, tenant_id: int) -> None:
        # Raises ValidationError si los datos son inválidos
        ...

    def _validate_delete(self, entity: MyEntity, tenant_id: int) -> None:
        # Raises ValidationError si no se puede eliminar (e.g. tiene dependencias activas)
        ...

    def _after_delete(self, entity_info: dict, user_id: int, user_email: str) -> None:
        # Publicar evento de dominio, etc.
        ...

# 2. Exportar en rest_api/services/domain/__init__.py
# 3. Usar en router (mantener router thin!)
```

### Thin router correspondiente

```python
# Router (thin - delega todo al service)
@router.get("/categories")
def list_categories(
    branch_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(current_user),
):
    ctx = PermissionContext(user)
    ctx.require_branch_access(branch_id)
    service = CategoryService(db)
    return service.list_by_branch(ctx.tenant_id, branch_id)

@router.post("/categories")
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(current_user),
):
    ctx = PermissionContext(user)
    ctx.require_management()
    service = CategoryService(db)
    return service.create_with_auto_order(data.model_dump(), ctx.tenant_id, ctx.user_id, ctx.user_email)
```

### Clases base disponibles

| Clase | Cuándo usarla |
|-------|--------------|
| `BaseService[Model]` | Base abstracta, solo acceso a repo y db |
| `BaseCRUDService[Model, Output]` | Entidades sin scope de branch (ej: tenant-level) |
| `BranchScopedService[Model, Output]` | Entidades dentro de un branch (caso más común) |

**Métodos override disponibles (hooks del ciclo de vida):**
- `_validate_create(data, tenant_id)` — validar antes de crear
- `_validate_update(entity, data, tenant_id)` — validar antes de actualizar
- `_validate_delete(entity, tenant_id)` — validar antes de eliminar (ej: dependencias activas)
- `_after_create(entity, user_id, user_email)` — side effects post-creación
- `_after_update(entity, old_values, user_id, user_email)` — side effects post-actualización
- `_after_delete(entity_info, user_id, user_email)` — publicar eventos post-eliminación

**Métodos CRUD heredados (no necesitan override):**
- `get_by_id(entity_id, tenant_id)` → `OutputT`
- `list_all(tenant_id)` → `list[OutputT]`
- `list_by_branch(tenant_id, branch_id)` → `list[OutputT]` (solo `BranchScopedService`)
- `list_by_branches(tenant_id, branch_ids)` → `list[OutputT]` (solo `BranchScopedService`)
- `create(data, tenant_id, user_id, user_email)` → `OutputT`
- `update(entity_id, data, tenant_id, user_id, user_email)` → `OutputT`
- `delete(entity_id, tenant_id, user_id, user_email)` → `None`
- `count(tenant_id)` → `int`
- `exists(entity_id, tenant_id)` → `bool`

### Services existentes

```python
from rest_api.services.domain import (
    CategoryService,
    SubcategoryService,
    BranchService,
    SectorService,
    TableService,
    ProductService,
    AllergenService,
    StaffService,
    PromotionService,
    RoundService,
    BillingService,
    DinerService,
    ServiceCallService,
    TicketService,
)
```

---

## PermissionContext

```python
from rest_api.services.permissions import PermissionContext, Action

ctx = PermissionContext(user)

# Propiedades de usuario
ctx.user_id        # int — extraído de user["sub"]
ctx.user_email     # str
ctx.tenant_id      # int
ctx.branch_ids     # list[int]
ctx.roles          # list[str]
ctx.is_admin       # bool
ctx.is_manager     # bool
ctx.is_management  # bool (admin OR manager)

# Checks de permisos — lanzan ForbiddenError si no se cumple
ctx.require_management()                # Raises ForbiddenError si no es ADMIN/MANAGER
ctx.require_admin()                     # Raises ForbiddenError si no es ADMIN
ctx.require_branch_access(branch_id)   # Raises ForbiddenError si no tiene acceso al branch

# Checks sin raise
ctx.has_branch_access(branch_id)       # bool

# Action-based checks (usa Strategy Pattern internamente)
ctx.can(Action.CREATE, "Product", branch_id=5)  # bool
ctx.can(Action.DELETE, entity)                   # bool
ctx.can(Action.READ, entity)                     # bool
ctx.can(Action.UPDATE, entity)                   # bool

# Filtrado de queries SQLAlchemy según permisos
ctx.filter_query(query, Model)

# Decoradores disponibles
from rest_api.services.permissions import require_permission, require_admin, require_management
```

---

## Contexto del usuario en JWT

```python
user_id    = int(user["sub"])    # "sub" contiene el user ID como string
tenant_id  = user["tenant_id"]
branch_ids = user["branch_ids"]  # list[int]
roles      = user["roles"]       # list[str]: "ADMIN", "MANAGER", "WAITER", "KITCHEN"
```

---

## safe_commit

```python
from shared.infrastructure.db import safe_commit

safe_commit(db)  # Siempre — incluye automatic rollback en caso de error
# NUNCA usar db.commit() directo en routers ni services
```

---

## Eager loading — prevenir N+1

```python
from sqlalchemy.orm import selectinload, joinedload

rounds = db.execute(
    select(Round).options(
        selectinload(Round.items).joinedload(RoundItem.product)
    )
).scalars().unique().all()
```

---

## Race condition prevention

```python
# Usar with_for_update() para billing, rounds y cualquier operación concurrente crítica
locked = db.scalar(select(Entity).where(...).with_for_update())
```

---

## SQLAlchemy boolean — IMPORTANTE

```python
# CORRECTO
.where(Model.is_active.is_(True))
.where(Model.is_active.is_(False))

# INCORRECTO — nunca usar == True / == False con SQLAlchemy
.where(Model.is_active == True)
```

---

## Repository pattern

```python
from rest_api.services.crud import TenantRepository, BranchRepository

# TenantRepository — entidades scoped a tenant
product_repo = TenantRepository(Product, db)
products = product_repo.find_all(tenant_id=1, options=[selectinload(Product.allergens)])

# BranchRepository — entidades scoped a branch
category_repo = BranchRepository(Category, db)
categories = category_repo.find_by_branch(branch_id=5, tenant_id=1)
```

---

## Redis — async pool

```python
from shared.infrastructure.events import get_redis_pool, publish_event

redis = await get_redis_pool()  # Singleton — NO cerrar manualmente
await publish_event(redis, channel="...", event_type="...", data={...})
```

---

## Excepciones centralizadas (con auto-logging)

Todas heredan de `AppException` — se loguean automáticamente al instanciarse.

```python
from shared.utils.exceptions import (
    NotFoundError,          # 404
    ForbiddenError,         # 403
    ValidationError,        # 400
    ConflictError,          # 409
    DatabaseError,          # 500 — operación de DB fallida
    InternalError,          # 500
    RateLimitError,         # 429
    InvalidStateError,      # 400 — estado inválido para la operación
    InvalidTransitionError, # 400 — transición de estado inválida
    DuplicateEntityError,   # 400 — entidad ya existe
    PaymentAmountError,     # 400 — monto inválido
    AlreadyPaidError,       # 409 — cuenta ya pagada
    BranchAccessError,      # 403 — sin acceso al branch
    InsufficientRoleError,  # 403 — rol insuficiente
)

# Uso típico
raise NotFoundError("Producto", product_id, tenant_id=tenant_id)
raise ForbiddenError("eliminar este producto", user_id=user_id)
raise ValidationError("El precio debe ser positivo", field="price")
raise InvalidStateError("Round", current_state="SERVED", expected_states=["PENDING"])
raise DatabaseError("crear producto")  # mensaje genérico seguro para el cliente
```

---

## Outbox Pattern — eventos críticos garantizados

Para eventos financieros/críticos que no pueden perderse, usar Transactional Outbox:

```python
from rest_api.services.events.outbox_service import write_billing_outbox_event

write_billing_outbox_event(
    db=db,
    tenant_id=tenant_id,
    event_type="CHECK_REQUESTED",
    ...
)
db.commit()  # Atómico con los datos de negocio
```

| Patrón | Eventos |
|--------|---------|
| **Outbox** (no se puede perder) | `CHECK_REQUESTED/PAID`, `PAYMENT_*`, `ROUND_SUBMITTED/READY`, `SERVICE_CALL_CREATED` |
| **Direct Redis** (baja latencia) | `ROUND_CONFIRMED/IN_KITCHEN/SERVED`, `CART_*`, `TABLE_*`, `ENTITY_*` |

---

## Cascade soft delete

```python
from rest_api.services.crud import cascade_soft_delete

affected = cascade_soft_delete(db, product, user_id, user_email)
# Retorna dict con entidades afectadas por el cascade
```

---

## Input validation

```python
from shared.utils.validators import validate_image_url, escape_like_pattern

# validate_image_url bloquea SSRF (IPs internas, cloud metadata)
url = validate_image_url(raw_url)  # raises ValueError si inválida

# escape_like_pattern para búsquedas LIKE seguras
pattern = escape_like_pattern(user_input)
```

---

## Constantes centralizadas

```python
from shared.config.constants import Roles, RoundStatus, MANAGEMENT_ROLES

# Roles
Roles.ADMIN      # "ADMIN"
Roles.MANAGER    # "MANAGER"
Roles.WAITER     # "WAITER"
Roles.KITCHEN    # "KITCHEN"

MANAGEMENT_ROLES  # {"ADMIN", "MANAGER"}

# RoundStatus
RoundStatus.PENDING     # "PENDING"
RoundStatus.CONFIRMED   # "CONFIRMED"
RoundStatus.SUBMITTED   # "SUBMITTED"
RoundStatus.IN_KITCHEN  # "IN_KITCHEN"
RoundStatus.READY       # "READY"
RoundStatus.SERVED      # "SERVED"
RoundStatus.CANCELED    # "CANCELED"
```

---

## Logging

```python
from shared.config.logging import get_logger

logger = get_logger(__name__)

logger.info("Producto creado", product_id=product.id, tenant_id=tenant_id)
logger.warning("Acceso denegado", user_id=user_id, branch_id=branch_id)
logger.error("Fallo en DB", error=str(e), operation="crear producto")

# NUNCA usar print() ni logging.getLogger() directo
```

---

## Governance por dominio

| Nivel | Dominios | Política |
|-------|----------|----------|
| **CRITICO** | Auth, Billing, Allergens, Staff | Solo análisis — sin cambios a código de producción |
| **ALTO** | Products, WebSocket, Rate Limiting | Proponer cambio, esperar revisión humana |
| **MEDIO** | Orders, Kitchen, Waiter, Tables, Customer | Implementar con checkpoints |
| **BAJO** | Categories, Sectors, Recipes, Ingredients, Promotions | Autonomía total si tests pasan |

---

## Convenciones

- **Naming**: `snake_case` en todo el backend
- **SQL reserved words**: usar `__tablename__` alternativo (ej: `Check` → `app_check`)
- **Precios**: siempre en centavos como `int` (ej: $125.50 = `12550`)
- **IDs**: `BigInteger` en modelos SQLAlchemy
- **Idioma de UI**: español; comentarios de código en inglés

---

## Canonical Import Paths

```python
# Infrastructure
from shared.infrastructure.db import get_db, SessionLocal, safe_commit
from shared.infrastructure.events import get_redis_pool, publish_event

# Config
from shared.config.settings import settings
from shared.config.logging import get_logger
from shared.config.constants import Roles, RoundStatus, MANAGEMENT_ROLES

# Security
from shared.security.auth import current_user_context, verify_jwt

# Exceptions & Validators
from shared.utils.exceptions import NotFoundError, ForbiddenError, ValidationError
from shared.utils.validators import validate_image_url, escape_like_pattern

# Schemas
from shared.utils.admin_schemas import CategoryOutput, ProductOutput

# Models
from rest_api.models import Product, Category, Round

# Domain Services
from rest_api.services.domain import ProductService, CategoryService

# Base Services
from rest_api.services.base_service import BaseCRUDService, BranchScopedService

# Repositories
from rest_api.services.crud import TenantRepository, BranchRepository

# Soft Delete
from rest_api.services.crud.soft_delete import soft_delete

# Permissions
from rest_api.services.permissions import PermissionContext, Action

# Events
from rest_api.services.events.outbox_service import write_billing_outbox_event
```

---

## Gotchas y edge cases

- **CRUDFactory DEPRECADO** — usar Domain Services; CRUDFactory existe en `crud/factory.py` pero no debe usarse en código nuevo.
- **SQLAlchemy boolean**: `is_(True)` obligatorio, `== True` genera warnings y puede fallar en algunos backends.
- **`safe_commit` siempre** — nunca llamar `db.commit()` directo; `safe_commit` hace rollback automático y loguea el error.
- **Router THIN** — si el router tiene más de ~10 líneas de lógica, algo está mal; delegá al service.
- **Exportar en `__init__.py`** — todo nuevo service debe agregarse a `rest_api/services/domain/__init__.py` o no será importable desde `from rest_api.services.domain import X`.
- **`with_for_update()`** — usar en billing y rounds para prevenir race conditions en operaciones concurrentes.
- **`permissions/` es un paquete** — el import correcto es `from rest_api.services.permissions import PermissionContext`; `from rest_api.services.permissions.context import PermissionContext` también funciona pero es un detalle de implementación.
- **`_after_delete` recibe `entity_info: dict`**, no la entidad — porque la entidad ya fue soft-deleted. Los datos se capturan en `_get_entity_info_for_event()` antes de la eliminación.
- **`validate_image_url`** bloquea activamente IPs internas (127.x, 10.x, 192.168.x) y URLs de metadata de cloud. El base service lo llama automáticamente para el campo `image`; otros campos de imagen requieren configurar `image_url_fields` en el constructor.
- **`DatabaseError`** usa un mensaje genérico seguro para el cliente — no exponer detalles de DB al exterior.
- **`_validate_delete` verifica dependencias activas** con `.is_(True)` — si una categoría tiene subcategorías activas, lanzar `ValidationError` antes de intentar eliminar.
- **`BranchScopedService` activa `BranchRepository` automáticamente** al pasar `has_branch_id=True` al padre; no hace falta instanciar el repo manualmente.
- **PermissionContext usa Strategy Pattern** internamente (`AdminStrategy`, `ManagerStrategy`, `KitchenStrategy`, `WaiterStrategy`, `ReadOnlyStrategy`) — selecciona la estrategia de mayor privilegio según los roles del usuario.
