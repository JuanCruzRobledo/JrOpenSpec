"""Public menu service — assembles menu data with caching and filtering.

Pure business logic — no FastAPI imports.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from shared.exceptions import NotFoundError
from shared.models.catalog.allergen import Allergen
from shared.models.catalog.allergen_cross_reaction import AllergenCrossReaction
from shared.models.catalog.branch_product import BranchProduct
from shared.models.catalog.category import Category
from shared.models.catalog.dietary_profile import DietaryProfile
from shared.models.catalog.product import Product
from shared.models.catalog.product_allergen import ProductAllergen
from shared.models.catalog.product_badge import ProductBadge
from shared.models.catalog.product_cooking_method import ProductCookingMethod
from shared.models.catalog.product_dietary_profile import ProductDietaryProfile
from shared.models.catalog.product_seal import ProductSeal
from shared.models.catalog.subcategory import Subcategory
from shared.models.core.branch import Branch
from shared.models.core.tenant import Tenant
from shared.models.marketing.badge import Badge
from shared.models.marketing.seal import Seal
from shared.models.profiles.cooking_method import CookingMethod
from rest_api.app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class PublicMenuService:
    """Builds public API responses with Redis caching."""

    def __init__(self, db: AsyncSession, cache: CacheService) -> None:
        self._db = db
        self._cache = cache

    # ── Menu ──

    async def get_menu(
        self,
        branch_slug: str,
        dietary: list[str] | None = None,
        allergen_free: list[str] | None = None,
    ) -> dict:
        """Get full menu for a branch, with optional dietary/allergen filtering."""
        # Build cache key with query params hash
        cache_key = f"cache:public:menu:{branch_slug}"
        if dietary or allergen_free:
            params = f"d={','.join(sorted(dietary or []))}|a={','.join(sorted(allergen_free or []))}"
            params_hash = hashlib.md5(params.encode()).hexdigest()[:8]
            cache_key = f"{cache_key}:q:{params_hash}"

        async def _build():
            return await self._build_menu(branch_slug, dietary, allergen_free)

        return await self._cache.get_or_set(cache_key, _build, ttl=300)

    async def _build_menu(
        self,
        branch_slug: str,
        dietary: list[str] | None,
        allergen_free: list[str] | None,
    ) -> dict:
        """Build the menu response from DB."""
        # Resolve branch
        branch = await self._get_branch_by_slug(branch_slug)

        # Build product query
        stmt = (
            select(Product)
            .join(BranchProduct, BranchProduct.product_id == Product.id)
            .where(
                BranchProduct.branch_id == branch.id,
                BranchProduct.is_available.is_(True),
                Product.deleted_at.is_(None),
                Product.is_available.is_(True),
            )
            .options(
                joinedload(Product.subcategory).joinedload(Subcategory.category),
                selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
                selectinload(Product.product_dietary_profiles).joinedload(ProductDietaryProfile.dietary_profile),
                selectinload(Product.product_cooking_methods).joinedload(ProductCookingMethod.cooking_method),
                selectinload(Product.product_badges).joinedload(ProductBadge.badge),
                selectinload(Product.product_seals).joinedload(ProductSeal.seal),
                selectinload(Product.branch_products),
            )
        )

        # Dietary filter: AND logic
        if dietary:
            for code in dietary:
                stmt = stmt.where(
                    Product.id.in_(
                        select(ProductDietaryProfile.product_id)
                        .join(DietaryProfile, DietaryProfile.id == ProductDietaryProfile.dietary_profile_id)
                        .where(DietaryProfile.code == code)
                    )
                )

        # Allergen-free filter: exclude products containing/may_containing
        if allergen_free:
            stmt = stmt.where(
                ~Product.id.in_(
                    select(ProductAllergen.product_id)
                    .join(Allergen, Allergen.id == ProductAllergen.allergen_id)
                    .where(
                        Allergen.code.in_(allergen_free),
                        ProductAllergen.presence_type.in_(["contains", "may_contain"]),
                    )
                )
            )

        result = await self._db.execute(stmt)
        products = result.scalars().unique().all()

        # Group by category → subcategory (3-level hierarchy expected by frontend)
        # categories_map[cat_id]["subcategories"][sub_id]["products"]
        categories_map: dict[int, dict] = {}
        allergen_codes_used: set[str] = set()

        for product in products:
            sub = product.subcategory
            cat = sub.category if sub else None
            if cat is None or sub is None:
                continue

            # Ensure category entry exists
            if cat.id not in categories_map:
                categories_map[cat.id] = {
                    "id": str(cat.id),
                    "name": cat.name,
                    "slug": cat.slug,
                    "displayOrder": cat.display_order,
                    "subcategories": {},
                }

            # Ensure subcategory entry exists within this category
            subs_map = categories_map[cat.id]["subcategories"]
            if sub.id not in subs_map:
                subs_map[sub.id] = {
                    "id": str(sub.id),
                    "name": sub.name,
                    "slug": sub.slug,
                    "displayOrder": sub.display_order,
                    "products": [],
                }

            # Resolve effective price for this branch
            bp = next(
                (bp for bp in product.branch_products if bp.branch_id == branch.id),
                None,
            )
            price_cents = bp.effective_price_cents if bp else product.base_price_cents

            # Quick-filter allergen fields used by pwa_menu filter-engine.
            allergen_slugs: list[str] = []
            may_contain_slugs: list[str] = []
            for pa in product.product_allergens:
                allergen_codes_used.add(pa.allergen.code)
                if pa.presence_type == "contains":
                    allergen_slugs.append(pa.allergen.code)
                elif pa.presence_type == "may_contain":
                    may_contain_slugs.append(pa.allergen.code)

            # Dietary profile slugs
            dietary_codes: list[str] = []
            for pdp in product.product_dietary_profiles:
                if pdp.dietary_profile:
                    dietary_codes.append(pdp.dietary_profile.code)

            # Cooking method slugs
            cooking_codes: list[str] = []
            for pcm in product.product_cooking_methods:
                if pcm.cooking_method:
                    cooking_codes.append(pcm.cooking_method.code)

            # Badges — map to frontend Badge type
            badges = []
            for pb in product.product_badges:
                b = pb.badge
                if b:
                    badges.append({
                        "id": str(b.id),
                        "name": b.name,
                        "slug": b.code,
                        "colorHex": b.color,
                        "iconName": b.icon,
                    })

            # Seals — map to frontend Seal type
            seals = []
            for ps in product.product_seals:
                s = ps.seal
                if s:
                    seals.append({
                        "id": str(s.id),
                        "name": s.name,
                        "slug": s.code,
                        "imageUrl": None,
                        "description": None,
                    })

            prod_dict = {
                "id": str(product.id),
                "name": product.name,
                "slug": product.slug,
                "description": product.short_description,
                "priceCents": price_cents,
                "imageUrl": product.image_url,
                "isAvailable": True,
                "badges": badges,
                "seals": seals,
                "allergenSlugs": allergen_slugs,
                "mayContainSlugs": may_contain_slugs,
                "dietaryProfileSlugs": dietary_codes,
                "cookingMethodSlugs": cooking_codes,
            }
            subs_map[sub.id]["products"].append(prod_dict)

        # Serialize: convert nested dicts to sorted lists
        categories = []
        for cat_entry in sorted(categories_map.values(), key=lambda c: c["displayOrder"]):
            subcategories = sorted(
                cat_entry["subcategories"].values(),
                key=lambda s: s["displayOrder"],
            )
            categories.append({**cat_entry, "subcategories": subcategories})

        # Allergen legend
        allergen_legend = []
        if allergen_codes_used:
            legend_result = await self._db.execute(
                select(Allergen).where(
                    Allergen.code.in_(allergen_codes_used),
                    Allergen.deleted_at.is_(None),
                )
            )
            for a in legend_result.scalars().all():
                allergen_legend.append({
                    "code": a.code,
                    "name": a.name,
                    "icon": a.icon,
                })

        return {
            "branch": {
                "id": str(branch.id),
                "name": branch.name,
                "slug": branch.slug,
                "tenantSlug": branch.slug.split("-")[0] if branch.slug else "",
                "logoUrl": None,
                "address": branch.address,
                "phone": branch.phone,
            },
            "categories": categories,
            "generatedAt": datetime.now(UTC).isoformat(),
        }

    # ── Product Detail ──

    async def get_product(self, branch_slug: str, product_id: int) -> dict:
        """Get full product detail for public display."""
        cache_key = f"cache:public:product:{branch_slug}:{product_id}"

        async def _build():
            return await self._build_product_detail(branch_slug, product_id)

        return await self._cache.get_or_set(cache_key, _build, ttl=300)

    async def _build_product_detail(self, branch_slug: str, product_id: int) -> dict:
        """Build product detail response from DB."""
        branch = await self._get_branch_by_slug(branch_slug)

        result = await self._db.execute(
            select(Product)
            .join(BranchProduct, BranchProduct.product_id == Product.id)
            .where(
                Product.id == product_id,
                BranchProduct.branch_id == branch.id,
                BranchProduct.is_available.is_(True),
                Product.deleted_at.is_(None),
            )
            .options(
                joinedload(Product.subcategory).joinedload(Subcategory.category),
                selectinload(Product.product_allergens)
                    .joinedload(ProductAllergen.allergen)
                    .selectinload(Allergen.cross_reactions_as_source)
                    .joinedload(AllergenCrossReaction.related_allergen),
                selectinload(Product.product_allergens)
                    .joinedload(ProductAllergen.allergen)
                    .selectinload(Allergen.cross_reactions_as_related)
                    .joinedload(AllergenCrossReaction.allergen),
                selectinload(Product.product_dietary_profiles).joinedload(ProductDietaryProfile.dietary_profile),
                selectinload(Product.product_cooking_methods).joinedload(ProductCookingMethod.cooking_method),
                selectinload(Product.ingredients),
                selectinload(Product.product_badges).joinedload(ProductBadge.badge),
                selectinload(Product.product_seals).joinedload(ProductSeal.seal),
                selectinload(Product.branch_products),
            )
        )
        product = result.scalars().unique().first()

        if product is None:
            raise NotFoundError(message="Product not found or not available in this branch")

        bp = next(
            (bp for bp in product.branch_products if bp.branch_id == branch.id),
            None,
        )
        price_cents = bp.effective_price_cents if bp else product.base_price_cents

        # Allergens with cross-reactions
        allergens = []
        for pa in product.product_allergens:
            a = pa.allergen
            # Cross-reactions already loaded via eager load chains on the query
            cross_reactions = []
            for cr in a.all_cross_reactions:
                related = cr.related_allergen if cr.allergen_id == a.id else cr.allergen
                cross_reactions.append({
                    "allergenId": str(related.id),
                    "allergenSlug": related.code,
                    "allergenName": related.name,
                    "riskLevel": cr.severity,
                })

            allergens.append({
                "allergenId": str(a.id),
                "allergenSlug": a.code,
                "allergenName": a.name,
                "icon": a.icon,
                "presence": pa.presence_type,
                "riskLevel": pa.risk_level,
                "notes": pa.notes,
                "crossReactions": cross_reactions,
            })

        # Dietary profiles
        dietary_profiles = []
        for pdp in product.product_dietary_profiles:
            dp = pdp.dietary_profile
            if dp:
                dietary_profiles.append({"code": dp.code, "name": dp.name, "icon": dp.icon})

        # Cooking methods
        cooking_methods = []
        for pcm in product.product_cooking_methods:
            cm = pcm.cooking_method
            if cm:
                cooking_methods.append({"code": cm.code, "name": cm.name, "icon": cm.icon})

        # Ingredients
        ingredients = [
            {
                "name": i.name,
                "quantity": float(i.quantity),
                "unit": i.unit,
                "isOptional": i.is_optional,
            }
            for i in sorted(product.ingredients, key=lambda x: x.sort_order)
        ]

        # Badges
        badges = []
        for pb in product.product_badges:
            b = pb.badge
            if b:
                badges.append({"code": b.code, "name": b.name, "color": b.color, "icon": b.icon})

        # Seals
        seals = []
        for ps in product.product_seals:
            s = ps.seal
            if s:
                seals.append({"code": s.code, "name": s.name, "color": s.color, "icon": s.icon})

        cat = product.subcategory.category if product.subcategory else None

        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "shortDescription": product.short_description,
            "priceCents": price_cents,
            "imageUrls": [product.image_url] if product.image_url else [],
            "badges": badges,
            "seals": seals,
            "dietaryProfiles": dietary_profiles,
            "allergens": allergens,
            "cookingMethods": cooking_methods,
            "flavorProfiles": product.flavor_profiles_array or [],
            "textureProfiles": product.texture_profiles_array or [],
            "ingredients": ingredients,
            "branch": {
                "id": branch.id,
                "name": branch.name,
                "slug": branch.slug,
            },
            "category": {
                "id": cat.id if cat else 0,
                "name": cat.name if cat else "",
                "slug": cat.slug if cat else "",
            },
            "generatedAt": datetime.now(UTC).isoformat(),
        }

    # ── Branches ──

    async def get_branches(self, tenant_slug: str) -> dict:
        """Get active branches for a tenant."""
        cache_key = f"cache:public:branches:{tenant_slug}"

        async def _build():
            return await self._build_branches(tenant_slug)

        return await self._cache.get_or_set(cache_key, _build, ttl=300)

    async def _build_branches(self, tenant_slug: str) -> dict:
        """Build branches response from DB."""
        tenant = await self._get_tenant_by_slug(tenant_slug)

        result = await self._db.execute(
            select(Branch).where(
                Branch.tenant_id == tenant.id,
                Branch.deleted_at.is_(None),
                Branch.is_active.is_(True),
            ).order_by(Branch.display_order)
        )
        branches = result.scalars().all()

        items = []
        for b in branches:
            # Count products
            prod_count = (await self._db.execute(
                select(func.count(BranchProduct.id)).where(
                    BranchProduct.branch_id == b.id,
                    BranchProduct.is_available.is_(True),
                )
            )).scalar() or 0

            # Count categories (distinct)
            cat_count = (await self._db.execute(
                select(func.count(func.distinct(Category.id)))
                .join(Subcategory, Subcategory.category_id == Category.id)
                .join(Product, Product.subcategory_id == Subcategory.id)
                .join(BranchProduct, BranchProduct.product_id == Product.id)
                .where(
                    BranchProduct.branch_id == b.id,
                    BranchProduct.is_available.is_(True),
                    Product.deleted_at.is_(None),
                    Category.deleted_at.is_(None),
                )
            )).scalar() or 0

            items.append({
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "address": b.address,
                "phone": b.phone,
                "latitude": b.latitude,
                "longitude": b.longitude,
                "openNow": b.is_open,
                "productCount": prod_count,
                "categoryCount": cat_count,
            })

        return {
            "branches": items,
            "generatedAt": datetime.now(UTC).isoformat(),
        }

    # ── Allergens Catalog ──

    async def get_allergens(self, tenant_slug: str) -> dict:
        """Get allergen catalog with cross-reactions."""
        cache_key = f"cache:public:allergens:{tenant_slug}"

        async def _build():
            return await self._build_allergens(tenant_slug)

        return await self._cache.get_or_set(cache_key, _build, ttl=300)

    async def _build_allergens(self, tenant_slug: str) -> dict:
        """Build allergens response from DB."""
        tenant = await self._get_tenant_by_slug(tenant_slug)

        result = await self._db.execute(
            select(Allergen).where(
                or_(Allergen.tenant_id.is_(None), Allergen.tenant_id == tenant.id),
                Allergen.deleted_at.is_(None),
            )
            .options(
                selectinload(Allergen.cross_reactions_as_source).joinedload(AllergenCrossReaction.related_allergen),
                selectinload(Allergen.cross_reactions_as_related).joinedload(AllergenCrossReaction.allergen),
            )
            .order_by(Allergen.is_system.desc(), Allergen.name)
        )
        allergens = result.scalars().all()

        items = []
        for a in allergens:
            # Cross-reactions already loaded via eager load chains on the query
            cross_reactions = []
            for cr in a.all_cross_reactions:
                related = cr.related_allergen if cr.allergen_id == a.id else cr.allergen
                cross_reactions.append({
                    "allergenId": str(related.id),
                    "allergenSlug": related.code,
                    "allergenName": related.name,
                    "riskLevel": cr.severity,
                })

            items.append({
                "id": str(a.id),
                "slug": a.code,
                "name": a.name,
                "description": a.description,
                "icon": a.icon,
                "isSystem": a.is_system,
                "crossReacts": cross_reactions,
            })

        return {
            "allergens": items,
            "generatedAt": datetime.now(UTC).isoformat(),
        }

    # ── Helpers ──

    async def _get_branch_by_slug(self, slug: str) -> Branch:
        result = await self._db.execute(
            select(Branch).where(
                Branch.slug == slug,
                Branch.deleted_at.is_(None),
            )
        )
        branch = result.scalar_one_or_none()
        if branch is None:
            raise NotFoundError(message="Branch not found")
        return branch

    async def _get_tenant_by_slug(self, slug: str) -> Tenant:
        result = await self._db.execute(
            select(Tenant).where(
                Tenant.slug == slug,
                Tenant.deleted_at.is_(None),
            )
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise NotFoundError(message="Tenant not found")
        return tenant
