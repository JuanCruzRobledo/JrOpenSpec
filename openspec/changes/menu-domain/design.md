---
sprint: 4
artifact: design
status: complete
---

# SDD Design — Sprint 4: Productos Avanzado y API Pública del Menú

## Status: APPROVED

---

## 1. Extended Database Schema

### 1.1 New Tables

```sql
-- ============================================
-- ALLERGENS
-- ============================================
CREATE TABLE allergens (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(code, tenant_id),
    CHECK (is_system = FALSE OR tenant_id IS NULL)  -- system allergens have no tenant
);

CREATE INDEX idx_allergens_tenant ON allergens(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_allergens_code ON allergens(code) WHERE deleted_at IS NULL;

-- Seed 14 EU allergens (in migration)
-- INSERT INTO allergens (code, name, description, icon, is_system) VALUES
-- ('gluten', 'Gluten', 'Cereales con gluten: trigo, centeno, cebada, avena, espelta, kamut', 'wheat', TRUE),
-- ('dairy', 'Lácteos', 'Leche y derivados incluyendo lactosa y caseína', 'milk', TRUE),
-- ('eggs', 'Huevos', 'Huevos y productos derivados', 'egg', TRUE),
-- ('fish', 'Pescado', 'Pescado y productos derivados', 'fish', TRUE),
-- ('crustaceans', 'Crustáceos', 'Crustáceos y productos derivados', 'shrimp', TRUE),
-- ('tree_nuts', 'Frutos secos', 'Almendras, avellanas, nueces, anacardos, pecanas, pistachos, etc.', 'nut', TRUE),
-- ('soy', 'Soja', 'Soja y productos derivados', 'soybean', TRUE),
-- ('celery', 'Apio', 'Apio y productos derivados', 'celery', TRUE),
-- ('mustard', 'Mostaza', 'Mostaza y productos derivados', 'mustard', TRUE),
-- ('sesame', 'Sésamo', 'Granos de sésamo y productos derivados', 'sesame', TRUE),
-- ('sulfites', 'Sulfitos', 'Dióxido de azufre y sulfitos (>10mg/kg)', 'sulfite', TRUE),
-- ('lupins', 'Altramuces', 'Altramuces y productos derivados', 'lupin', TRUE),
-- ('mollusks', 'Moluscos', 'Moluscos y productos derivados', 'shell', TRUE),
-- ('peanuts', 'Cacahuetes', 'Cacahuetes/maní y productos derivados', 'peanut', TRUE);

CREATE TABLE allergen_cross_reactions (
    id SERIAL PRIMARY KEY,
    allergen_id INTEGER NOT NULL REFERENCES allergens(id) ON DELETE CASCADE,
    related_allergen_id INTEGER NOT NULL REFERENCES allergens(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'moderate', 'severe', 'life_threatening')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(allergen_id, related_allergen_id),
    CHECK (allergen_id < related_allergen_id)  -- canonical ordering, prevents duplicates
);

CREATE INDEX idx_cross_reactions_allergen ON allergen_cross_reactions(allergen_id);
CREATE INDEX idx_cross_reactions_related ON allergen_cross_reactions(related_allergen_id);

-- Known cross-reactions seed data:
-- latex ↔ banana, avocado, kiwi, chestnut (via tree_nuts)
-- crustaceans ↔ dust mites (not in our allergen list, but noted in description)
-- dairy ↔ soy (caseín cross-reactivity)
-- peanuts ↔ tree_nuts, soy, lupins
-- fish ↔ crustaceans (parvalbumin cross-reactivity)
-- gluten ↔ celery (profilin cross-reactivity)

-- ============================================
-- PRODUCT-ALLERGEN ASSOCIATION
-- ============================================
CREATE TABLE product_allergens (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    allergen_id INTEGER NOT NULL REFERENCES allergens(id) ON DELETE CASCADE,
    presence_type VARCHAR(20) NOT NULL CHECK (presence_type IN ('contains', 'may_contain', 'free_of')),
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'moderate', 'severe', 'life_threatening')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(product_id, allergen_id),
    CHECK (presence_type != 'free_of' OR risk_level = 'low')  -- free_of must be low risk
);

CREATE INDEX idx_product_allergens_product ON product_allergens(product_id);
CREATE INDEX idx_product_allergens_allergen ON product_allergens(allergen_id);

-- ============================================
-- DIETARY PROFILES
-- ============================================
CREATE TABLE dietary_profiles (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(code, tenant_id),
    CHECK (is_system = FALSE OR tenant_id IS NULL)
);

-- Seed: vegetarian, vegan, gluten_free, dairy_free, celiac_safe, keto, low_sodium

CREATE TABLE product_dietary_profiles (
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    dietary_profile_id INTEGER NOT NULL REFERENCES dietary_profiles(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, dietary_profile_id)
);

CREATE INDEX idx_product_dietary_profile ON product_dietary_profiles(dietary_profile_id);

-- ============================================
-- COOKING METHODS
-- ============================================
CREATE TABLE cooking_methods (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(50),
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(code, tenant_id),
    CHECK (is_system = FALSE OR tenant_id IS NULL)
);

-- Seed: grill, oven, fryer, steam, raw, sous_vide, smoke, saute, boil, roast

CREATE TABLE product_cooking_methods (
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    cooking_method_id INTEGER NOT NULL REFERENCES cooking_methods(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, cooking_method_id)
);

-- ============================================
-- PRODUCT EXTENDED COLUMNS (alter existing products table)
-- ============================================
-- ALTER TABLE products ADD COLUMN flavor_profiles VARCHAR(20)[] DEFAULT '{}';
-- ALTER TABLE products ADD COLUMN texture_profiles VARCHAR(20)[] DEFAULT '{}';
-- Valid flavor values: sweet, salty, sour, bitter, umami, spicy
-- Valid texture values: crispy, creamy, crunchy, soft, chewy, liquid
-- Validated at application layer via Pydantic

-- ============================================
-- PRODUCT INGREDIENTS
-- ============================================
CREATE TABLE product_ingredients (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredients(id) ON DELETE SET NULL,  -- future catalog ref
    name VARCHAR(200) NOT NULL,  -- denormalized/standalone
    quantity DECIMAL(10, 3) NOT NULL CHECK (quantity > 0),
    unit VARCHAR(10) NOT NULL CHECK (unit IN ('g', 'kg', 'ml', 'l', 'unit', 'tbsp', 'tsp', 'cup', 'oz', 'lb', 'pinch')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_optional BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(product_id, sort_order)
);

CREATE INDEX idx_product_ingredients_product ON product_ingredients(product_id);

-- ============================================
-- BRANCH PRODUCT (pricing & availability)
-- ============================================
CREATE TABLE branch_products (
    id SERIAL PRIMARY KEY,
    branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    price_cents INTEGER CHECK (price_cents IS NULL OR price_cents >= 0),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(branch_id, product_id)
);

CREATE INDEX idx_branch_products_branch ON branch_products(branch_id) WHERE is_active = TRUE;
CREATE INDEX idx_branch_products_product ON branch_products(product_id);

-- ============================================
-- BADGES
-- ============================================
CREATE TABLE badges (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) NOT NULL DEFAULT '#000000',
    icon VARCHAR(50),
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(code, tenant_id),
    CHECK (is_system = FALSE OR tenant_id IS NULL)
);

-- Seed: new (#22C55E), best_seller (#F59E0B), chef_recommends (#8B5CF6), on_sale (#EF4444)

CREATE TABLE product_badges (
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (product_id, badge_id)
);

-- ============================================
-- SEALS
-- ============================================
CREATE TABLE seals (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) NOT NULL DEFAULT '#000000',
    icon VARCHAR(50),
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(code, tenant_id),
    CHECK (is_system = FALSE OR tenant_id IS NULL)
);

-- Seed: organic (#16A34A), local (#2563EB), preservative_free (#D97706),
--       artisan (#9333EA), sustainable (#059669), fair_trade (#0891B2)

CREATE TABLE product_seals (
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    seal_id INTEGER NOT NULL REFERENCES seals(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (product_id, seal_id)
);
```

### 1.2 SQLAlchemy Models (Python)

```
rest_api/
├── models/
│   ├── allergen.py          # Allergen, AllergenCrossReaction
│   ├── product_allergen.py  # ProductAllergen
│   ├── dietary_profile.py   # DietaryProfile, ProductDietaryProfile
│   ├── cooking_method.py    # CookingMethod, ProductCookingMethod
│   ├── product_ingredient.py # ProductIngredient
│   ├── branch_product.py    # BranchProduct
│   ├── badge.py             # Badge, ProductBadge
│   └── seal.py              # Seal, ProductSeal
```

**Key model patterns:**

```python
# Example: Allergen model
class Allergen(AuditMixin, Base):
    __tablename__ = "allergens"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    is_system: Mapped[bool] = mapped_column(default=False)
    tenant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenants.id"))
    
    # Relationships
    tenant: Mapped[Optional["Tenant"]] = relationship(back_populates="allergens")
    product_allergens: Mapped[list["ProductAllergen"]] = relationship(back_populates="allergen")
    
    # Cross-reactions (bidirectional via union query)
    cross_reactions_as_source: Mapped[list["AllergenCrossReaction"]] = relationship(
        foreign_keys="AllergenCrossReaction.allergen_id", back_populates="allergen"
    )
    cross_reactions_as_related: Mapped[list["AllergenCrossReaction"]] = relationship(
        foreign_keys="AllergenCrossReaction.related_allergen_id", back_populates="related_allergen"
    )
    
    @property
    def all_cross_reactions(self) -> list["AllergenCrossReaction"]:
        return self.cross_reactions_as_source + self.cross_reactions_as_related

    __table_args__ = (
        UniqueConstraint("code", "tenant_id"),
        CheckConstraint("is_system = FALSE OR tenant_id IS NULL"),
    )

class AllergenCrossReaction(Base):
    __tablename__ = "allergen_cross_reactions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    allergen_id: Mapped[int] = mapped_column(ForeignKey("allergens.id"))
    related_allergen_id: Mapped[int] = mapped_column(ForeignKey("allergens.id"))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # AllergenSeverity enum
    
    allergen: Mapped["Allergen"] = relationship(foreign_keys=[allergen_id])
    related_allergen: Mapped["Allergen"] = relationship(foreign_keys=[related_allergen_id])
    
    __table_args__ = (
        UniqueConstraint("allergen_id", "related_allergen_id"),
        CheckConstraint("allergen_id < related_allergen_id"),
    )

# Product extended (add to existing Product model)
class Product(AuditMixin, Base):
    # ... existing fields ...
    flavor_profiles: Mapped[list[str]] = mapped_column(ARRAY(String(20)), default=list)
    texture_profiles: Mapped[list[str]] = mapped_column(ARRAY(String(20)), default=list)
    
    # New relationships
    allergens: Mapped[list["ProductAllergen"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    dietary_profiles: Mapped[list["DietaryProfile"]] = relationship(secondary="product_dietary_profiles")
    cooking_methods: Mapped[list["CookingMethod"]] = relationship(secondary="product_cooking_methods")
    ingredients: Mapped[list["ProductIngredient"]] = relationship(back_populates="product", order_by="ProductIngredient.sort_order")
    branch_products: Mapped[list["BranchProduct"]] = relationship(back_populates="product")
    badges: Mapped[list["Badge"]] = relationship(secondary="product_badges", order_by="product_badges.c.sort_order")
    seals: Mapped[list["Seal"]] = relationship(secondary="product_seals", order_by="product_seals.c.sort_order")

class BranchProduct(Base):
    __tablename__ = "branch_products"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    is_active: Mapped[bool] = mapped_column(default=True)
    price_cents: Mapped[Optional[int]] = mapped_column()
    sort_order: Mapped[int] = mapped_column(default=0)
    
    branch: Mapped["Branch"] = relationship(back_populates="branch_products")
    product: Mapped["Product"] = relationship(back_populates="branch_products")
    
    @property
    def effective_price_cents(self) -> int:
        return self.price_cents if self.price_cents is not None else self.product.base_price_cents
    
    __table_args__ = (
        UniqueConstraint("branch_id", "product_id"),
        CheckConstraint("price_cents IS NULL OR price_cents >= 0"),
    )
```

### 1.3 Pydantic Enums

```python
# shared/enums.py (additions)
class PresenceType(str, Enum):
    CONTAINS = "contains"
    MAY_CONTAIN = "may_contain"
    FREE_OF = "free_of"

class AllergenSeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"

class IngredientUnit(str, Enum):
    G = "g"
    KG = "kg"
    ML = "ml"
    L = "l"
    UNIT = "unit"
    TBSP = "tbsp"
    TSP = "tsp"
    CUP = "cup"
    OZ = "oz"
    LB = "lb"
    PINCH = "pinch"

class FlavorProfile(str, Enum):
    SWEET = "sweet"
    SALTY = "salty"
    SOUR = "sour"
    BITTER = "bitter"
    UMAMI = "umami"
    SPICY = "spicy"

class TextureProfile(str, Enum):
    CRISPY = "crispy"
    CREAMY = "creamy"
    CRUNCHY = "crunchy"
    SOFT = "soft"
    CHEWY = "chewy"
    LIQUID = "liquid"

class BatchPriceOperation(str, Enum):
    FIXED_ADD = "fixed_add"
    FIXED_SUBTRACT = "fixed_subtract"
    PERCENTAGE_INCREASE = "percentage_increase"
    PERCENTAGE_DECREASE = "percentage_decrease"
```

---

## 2. API Layer Design

### 2.1 Router Structure

```
rest_api/routers/
├── public/
│   ├── __init__.py
│   ├── menu_router.py        # GET /api/public/menu/{slug}, /menu/{slug}/product/{id}
│   ├── branches_router.py    # GET /api/public/branches
│   └── allergens_router.py   # GET /api/public/allergens
├── dashboard/
│   ├── allergens_router.py   # CRUD /api/dashboard/allergens
│   ├── products_router.py    # Extended product CRUD (existing, enhanced)
│   ├── dietary_profiles_router.py  # CRUD
│   ├── cooking_methods_router.py   # CRUD
│   ├── branch_products_router.py   # Pricing & availability management
│   ├── batch_price_router.py       # Preview + apply
│   ├── badges_router.py      # CRUD
│   └── seals_router.py       # CRUD
```

### 2.2 Service Layer

```
rest_api/services/
├── allergen_service.py        # CRUD + cross-reactions + tenant scoping
├── product_extended_service.py # Extended product operations (allergens, dietary, etc.)
├── branch_product_service.py  # Pricing, availability, effective price resolution
├── batch_price_service.py     # Preview + apply with audit
├── badge_service.py           # CRUD + assignment
├── seal_service.py            # CRUD + assignment
├── public_menu_service.py     # Menu assembly, filtering, caching orchestration
└── cache_service.py           # Redis cache operations (get, set, invalidate)
```

### 2.3 Repository Layer

```
rest_api/repositories/
├── allergen_repository.py
├── product_allergen_repository.py
├── dietary_profile_repository.py
├── cooking_method_repository.py
├── product_ingredient_repository.py
├── branch_product_repository.py
├── badge_repository.py
├── seal_repository.py
└── public_menu_repository.py   # Optimized read queries with eager loading
```

### 2.4 Public Menu Query Strategy

The `public_menu_repository.py` MUST use eager loading to avoid N+1:

```python
async def get_branch_menu(self, branch_slug: str, filters: MenuFilters) -> BranchMenuData:
    stmt = (
        select(Product)
        .join(BranchProduct, BranchProduct.product_id == Product.id)
        .join(Branch, Branch.id == BranchProduct.branch_id)
        .where(Branch.slug == branch_slug)
        .where(Branch.deleted_at.is_(None))
        .where(BranchProduct.is_active == True)
        .where(Product.deleted_at.is_(None))
        .options(
            joinedload(Product.category),
            selectinload(Product.allergens).joinedload(ProductAllergen.allergen),
            selectinload(Product.dietary_profiles),
            selectinload(Product.cooking_methods),
            selectinload(Product.ingredients),
            selectinload(Product.badges),
            selectinload(Product.seals),
            joinedload(Product.branch_products.and_(BranchProduct.branch_id == branch_subquery)),
        )
        .order_by(Product.category_id, BranchProduct.sort_order)
    )
    
    # Apply dietary filter
    if filters.dietary:
        for profile_code in filters.dietary:
            stmt = stmt.where(
                Product.id.in_(
                    select(ProductDietaryProfile.product_id)
                    .join(DietaryProfile)
                    .where(DietaryProfile.code == profile_code)
                )
            )
    
    # Apply allergen-free filter
    if filters.allergen_free:
        stmt = stmt.where(
            ~Product.id.in_(
                select(ProductAllergen.product_id)
                .join(Allergen)
                .where(Allergen.code.in_(filters.allergen_free))
                .where(ProductAllergen.presence_type.in_(['contains', 'may_contain']))
            )
        )
    
    result = await self.session.execute(stmt)
    return result.unique().scalars().all()
```

---

## 3. Caching Architecture

### 3.1 Cache Service

```python
# rest_api/services/cache_service.py
class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.default_ttl = 300  # 5 minutes
    
    async def get_or_set(self, key: str, factory: Callable, ttl: int = None) -> bytes:
        """Get from cache or compute and store."""
        cached = await self.redis.get(key)
        if cached:
            return orjson.loads(cached)
        
        result = await factory()
        serialized = orjson.dumps(result)
        await self.redis.setex(key, ttl or self.default_ttl, serialized)
        return result
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern using SCAN (non-blocking)."""
        deleted = 0
        async for key in self.redis.scan_iter(match=pattern, count=100):
            await self.redis.delete(key)
            deleted += 1
        return deleted
    
    async def invalidate_keys(self, *keys: str) -> int:
        """Delete specific keys."""
        if keys:
            return await self.redis.delete(*keys)
        return 0
```

### 3.2 Cache Decorator

```python
# rest_api/dependencies/cache.py
def cache_public(key_template: str, ttl: int = 300):
    """Decorator for public API caching.
    
    Usage:
        @cache_public("cache:public:menu:{slug}")
        async def get_menu(slug: str, ...): ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function args
            cache_key = key_template.format(**kwargs)
            
            # Append query params hash if present
            request = kwargs.get("request")
            if request and request.query_params:
                params_hash = hashlib.md5(str(sorted(request.query_params.items())).encode()).hexdigest()[:8]
                cache_key = f"{cache_key}:q:{params_hash}"
            
            cache_service = kwargs.get("cache_service")
            result = await cache_service.get_or_set(cache_key, lambda: func(*args, **kwargs), ttl)
            return result
        return wrapper
    return decorator
```

### 3.3 Invalidation Hooks

```python
# rest_api/services/cache_invalidation.py
class CacheInvalidator:
    """Centralized cache invalidation logic. Called from service layer after writes."""
    
    def __init__(self, cache: CacheService, branch_repo: BranchRepository):
        self.cache = cache
        self.branch_repo = branch_repo
    
    async def on_product_change(self, product_id: int, tenant_id: int):
        branches = await self.branch_repo.get_slugs_by_tenant(tenant_id)
        for slug in branches:
            await self.cache.invalidate_pattern(f"cache:public:menu:{slug}*")
            await self.cache.invalidate_keys(f"cache:public:product:{slug}:{product_id}")
    
    async def on_branch_change(self, branch_slug: str, tenant_slug: str):
        await self.cache.invalidate_pattern(f"cache:public:menu:{branch_slug}*")
        await self.cache.invalidate_keys(f"cache:public:branches:{tenant_slug}")
    
    async def on_allergen_change(self, tenant_id: int, tenant_slug: str):
        await self.cache.invalidate_keys(f"cache:public:allergens:{tenant_slug}")
        branches = await self.branch_repo.get_slugs_by_tenant(tenant_id)
        for slug in branches:
            await self.cache.invalidate_pattern(f"cache:public:menu:{slug}*")
    
    async def on_branch_product_change(self, branch_slug: str):
        await self.cache.invalidate_pattern(f"cache:public:menu:{branch_slug}*")
        await self.cache.invalidate_pattern(f"cache:public:product:{branch_slug}:*")
    
    async def on_badge_or_seal_change(self, tenant_id: int):
        branches = await self.branch_repo.get_slugs_by_tenant(tenant_id)
        for slug in branches:
            await self.cache.invalidate_pattern(f"cache:public:menu:{slug}*")
```

---

## 4. Dashboard UI Components

### 4.1 Component Tree (React 19 + TailwindCSS 4)

```
dashboard/src/
├── features/
│   ├── allergens/
│   │   ├── pages/
│   │   │   ├── AllergenListPage.tsx         # List with search, filter system/custom
│   │   │   └── AllergenFormPage.tsx         # Create/edit allergen
│   │   ├── components/
│   │   │   ├── AllergenTable.tsx            # Presentational: table with columns
│   │   │   ├── AllergenForm.tsx             # Presentational: form fields
│   │   │   ├── CrossReactionManager.tsx     # Manage cross-reactions for an allergen
│   │   │   └── AllergenBadge.tsx            # Small badge showing allergen icon+name
│   │   ├── hooks/
│   │   │   ├── useAllergens.ts              # Zustand selector + API calls
│   │   │   └── useCrossReactions.ts
│   │   └── api/
│   │       └── allergenApi.ts               # API client functions
│   │
│   ├── products/
│   │   ├── pages/
│   │   │   ├── ProductListPage.tsx          # Enhanced with badges, allergen indicators
│   │   │   └── ProductFormPage.tsx          # Tabbed form (see below)
│   │   ├── components/
│   │   │   ├── ProductForm/
│   │   │   │   ├── ProductFormTabs.tsx      # Tab container
│   │   │   │   ├── BasicInfoTab.tsx         # Name, description, category, base price
│   │   │   │   ├── AllergensTab.tsx         # Allergen assignment with presence/risk
│   │   │   │   ├── DietaryTab.tsx           # Dietary profile multiselect
│   │   │   │   ├── CookingMethodsTab.tsx    # Cooking method multiselect
│   │   │   │   ├── FlavorTextureTab.tsx     # Flavor + texture chip selectors
│   │   │   │   ├── IngredientsTab.tsx       # Sortable ingredient list
│   │   │   │   ├── BadgesSealsTab.tsx       # Badge + seal assignment
│   │   │   │   └── BranchPricingTab.tsx     # Per-branch pricing grid
│   │   │   ├── ProductTable.tsx
│   │   │   ├── BatchPriceModal.tsx          # Modal: operation select, amount input, preview table, confirm
│   │   │   ├── BatchPricePreview.tsx        # Preview table (old → new prices)
│   │   │   └── BranchAvailabilityGrid.tsx   # Toggle grid for branch availability
│   │   ├── hooks/
│   │   │   ├── useProductForm.ts            # Form state management
│   │   │   ├── useBatchPrice.ts             # Preview + confirm flow
│   │   │   └── useBranchProducts.ts
│   │   └── api/
│   │       ├── productApi.ts
│   │       ├── batchPriceApi.ts
│   │       └── branchProductApi.ts
│   │
│   ├── badges/
│   │   ├── pages/
│   │   │   └── BadgeListPage.tsx
│   │   ├── components/
│   │   │   ├── BadgeTable.tsx
│   │   │   ├── BadgeForm.tsx                # Name, code, color picker, icon select
│   │   │   └── BadgePreview.tsx             # Visual preview of badge
│   │   └── api/
│   │       └── badgeApi.ts
│   │
│   └── seals/
│       ├── pages/
│       │   └── SealListPage.tsx
│       ├── components/
│       │   ├── SealTable.tsx
│       │   ├── SealForm.tsx
│       │   └── SealPreview.tsx
│       └── api/
│           └── sealApi.ts
```

### 4.2 Product Form UX Design

**Tabbed interface with progressive disclosure:**

| Tab | Content | Validation |
|-----|---------|------------|
| Basico | Name, short description, full description, category (select), base price (cents input with $ formatting), image | Required: name, category, base price |
| Alergenos | Table of allergens with checkboxes. Selected → shows presence type dropdown + risk level dropdown + notes | At least 1 allergen record before publish |
| Dieta | Multiselect chips for dietary profiles (system + custom) | Optional |
| Coccion | Multiselect chips for cooking methods | Optional |
| Sabor y Textura | Two groups of toggle chips: flavors and textures | Optional |
| Ingredientes | Sortable list (drag & drop). Each row: name, quantity, unit select, optional toggle, notes. Add/remove buttons | Optional but recommended |
| Insignias y Sellos | Two sections with available badges/seals as selectable cards | Optional |
| Sucursales | Grid: branch name / active toggle / price input (blank = base price). Toggle "Precios diferenciados" | Auto-populated from tenant branches |

### 4.3 Zustand Store Slices

```typescript
// stores/allergenStore.ts
interface AllergenState {
  allergens: Allergen[];
  isLoading: boolean;
  error: string | null;
  fetchAllergens: () => Promise<void>;
  createAllergen: (data: AllergenCreate) => Promise<Allergen>;
  updateAllergen: (id: number, data: AllergenUpdate) => Promise<Allergen>;
  deleteAllergen: (id: number) => Promise<void>;
}

// stores/batchPriceStore.ts  
interface BatchPriceState {
  selectedProductIds: number[];
  preview: BatchPricePreview | null;
  isPreviewLoading: boolean;
  isApplying: boolean;
  toggleProduct: (id: number) => void;
  selectAll: (ids: number[]) => void;
  clearSelection: () => void;
  fetchPreview: (params: BatchPriceParams) => Promise<void>;
  applyBatchPrice: (params: BatchPriceParams) => Promise<void>;
}
```

**Zustand convention**: Individual selectors only (no destructuring) per project convention (React 19 infinite loop prevention).

```typescript
// CORRECT
const allergens = useAllergenStore(state => state.allergens);
const fetchAllergens = useAllergenStore(state => state.fetchAllergens);

// WRONG - causes infinite loops in React 19
const { allergens, fetchAllergens } = useAllergenStore();
```

---

## 5. Batch Price Update Algorithm

```python
# rest_api/services/batch_price_service.py

async def preview_batch_update(
    self,
    product_ids: list[int],
    operation: BatchPriceOperation,
    amount: Decimal,
    branch_id: Optional[int],
    tenant_id: int,
) -> BatchPricePreviewResult:
    """Generate preview of price changes without applying."""
    
    # 1. Validate input
    if len(product_ids) > 500:
        raise ValueError("Maximum 500 products per batch")
    if amount < 0:
        raise ValueError("Amount must be non-negative")
    
    # 2. Fetch affected BranchProducts
    branch_products = await self.branch_product_repo.get_by_products_and_branch(
        product_ids=product_ids,
        branch_id=branch_id,  # None = all branches
        tenant_id=tenant_id,
    )
    
    # 3. Calculate new prices
    changes = []
    for bp in branch_products:
        old_price = bp.effective_price_cents
        new_price = self._calculate_new_price(old_price, operation, amount)
        
        changes.append(BatchPriceChange(
            product_id=bp.product_id,
            product_name=bp.product.name,
            branch_id=bp.branch_id,
            branch_name=bp.branch.name,
            old_price_cents=old_price,
            new_price_cents=new_price,
        ))
    
    return BatchPricePreviewResult(changes=changes, total_changes=len(changes))

def _calculate_new_price(
    self, old_price: int, operation: BatchPriceOperation, amount: Decimal
) -> int:
    """Calculate new price based on operation. Clamps to >= 0."""
    match operation:
        case BatchPriceOperation.FIXED_ADD:
            new = old_price + int(amount)
        case BatchPriceOperation.FIXED_SUBTRACT:
            new = old_price - int(amount)
        case BatchPriceOperation.PERCENTAGE_INCREASE:
            new = round(old_price * (1 + float(amount) / 100))
        case BatchPriceOperation.PERCENTAGE_DECREASE:
            new = round(old_price * (1 - float(amount) / 100))
    
    return max(0, new)  # Clamp to 0

async def apply_batch_update(
    self,
    product_ids: list[int],
    operation: BatchPriceOperation,
    amount: Decimal,
    branch_id: Optional[int],
    tenant_id: int,
    user_id: int,
) -> BatchPriceApplyResult:
    """Apply batch price update transactionally with audit logging."""
    
    async with self.session.begin():
        preview = await self.preview_batch_update(product_ids, operation, amount, branch_id, tenant_id)
        
        audit_entries = []
        for change in preview.changes:
            # Update BranchProduct price
            await self.branch_product_repo.update_price(
                branch_id=change.branch_id,
                product_id=change.product_id,
                new_price_cents=change.new_price_cents,
            )
            
            # Create audit log
            audit = AuditLog(
                entity_type="branch_product",
                entity_id=f"{change.branch_id}:{change.product_id}",
                action="batch_price_update",
                old_value=str(change.old_price_cents),
                new_value=str(change.new_price_cents),
                metadata={"operation": operation.value, "amount": str(amount)},
                user_id=user_id,
                tenant_id=tenant_id,
            )
            self.session.add(audit)
            audit_entries.append(audit)
        
        await self.session.flush()
    
    # Invalidate cache for affected branches
    affected_branch_slugs = set()
    for change in preview.changes:
        slug = await self.branch_repo.get_slug(change.branch_id)
        affected_branch_slugs.add(slug)
    
    for slug in affected_branch_slugs:
        await self.cache_invalidator.on_branch_product_change(slug)
    
    return BatchPriceApplyResult(
        applied=len(preview.changes),
        audit_log_ids=[a.id for a in audit_entries],
    )
```

---

## 6. Rate Limiting (Public API)

```python
# rest_api/middleware/rate_limit.py
from fastapi import Request, HTTPException
from redis.asyncio import Redis

class RateLimiter:
    def __init__(self, redis: Redis, max_requests: int = 60, window_seconds: int = 60):
        self.redis = redis
        self.max_requests = max_requests
        self.window = window_seconds
    
    async def check(self, request: Request):
        ip = request.client.host
        key = f"rate_limit:public:{ip}"
        
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, self.window)
        
        if current > self.max_requests:
            ttl = await self.redis.ttl(key)
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers={"Retry-After": str(ttl)},
            )

# Applied as dependency on public router
# app.include_router(public_router, dependencies=[Depends(rate_limiter.check)])
```

---

## 7. Migration Strategy

**Alembic migrations** (ordered):

1. `001_create_allergens_table.py` — allergens + seed EU 14
2. `002_create_allergen_cross_reactions.py` — cross-reactions table + seed known reactions
3. `003_create_dietary_profiles.py` — dietary_profiles + seed 7 + junction table
4. `004_create_cooking_methods.py` — cooking_methods + seed 10 + junction table
5. `005_alter_products_add_flavor_texture.py` — Add ARRAY columns to products
6. `006_create_product_allergens.py` — product_allergens junction
7. `007_create_product_ingredients.py` — product_ingredients table
8. `008_create_branch_products.py` — branch_products table
9. `009_create_badges.py` — badges + seed 4 + junction
10. `010_create_seals.py` — seals + seed 6 + junction

---

## Next Recommended

→ `sdd-tasks` (implementation task breakdown with acceptance criteria)
