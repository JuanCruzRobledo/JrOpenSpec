"""Product extended service — manage sub-resources (allergens, dietary, cooking, ingredients, badges, seals).

Pure business logic — no FastAPI imports.
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.enums import FlavorProfileEnum, PresenceType, TextureProfileEnum
from shared.exceptions import NotFoundError, ValidationError
from shared.infrastructure.db import safe_commit
from shared.models.catalog.product import Product
from shared.models.catalog.product_allergen import ProductAllergen
from shared.models.catalog.product_badge import ProductBadge
from shared.models.catalog.product_cooking_method import ProductCookingMethod
from shared.models.catalog.product_dietary_profile import ProductDietaryProfile
from shared.models.catalog.product_ingredient import ProductIngredient
from shared.models.catalog.product_seal import ProductSeal

logger = logging.getLogger(__name__)


class ProductExtendedService:
    """Manages product enrichment: allergens, dietary profiles, cooking methods,
    ingredients, badges, seals, flavor/texture profiles."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _get_product(self, product_id: int, tenant_id: int) -> Product:
        """Fetch product or raise NotFoundError."""
        result = await self._db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
                Product.deleted_at.is_(None),
            )
        )
        product = result.scalar_one_or_none()
        if product is None:
            raise NotFoundError(message="Producto no encontrado")
        return product

    # ── Allergens ──

    async def set_allergens(
        self, product_id: int, tenant_id: int, allergen_data: list[dict],
    ) -> list[dict]:
        """Replace all allergen associations for a product.

        Each item: {allergen_id, presence_type, risk_level, notes?}
        """
        await self._get_product(product_id, tenant_id)

        # Validate free_of constraint
        for item in allergen_data:
            if item["presence_type"] == PresenceType.FREE_OF.value and item["risk_level"] != "low":
                raise ValidationError(
                    message="free_of presence must have low risk level"
                )

        # Delete existing
        await self._db.execute(
            delete(ProductAllergen).where(ProductAllergen.product_id == product_id)
        )

        # Insert new
        for item in allergen_data:
            pa = ProductAllergen(
                product_id=product_id,
                allergen_id=item["allergen_id"],
                presence_type=item["presence_type"],
                risk_level=item["risk_level"],
                notes=item.get("notes"),
            )
            self._db.add(pa)

        await safe_commit(self._db)

        # Fetch back with allergen info
        result = await self._db.execute(
            select(ProductAllergen)
            .where(ProductAllergen.product_id == product_id)
            .options(selectinload(ProductAllergen.allergen))
        )
        return [
            {
                "allergen_id": pa.allergen_id,
                "codigo": pa.allergen.code,
                "nombre": pa.allergen.name,
                "icono": pa.allergen.icon,
                "tipo_presencia": pa.presence_type,
                "nivel_riesgo": pa.risk_level,
                "notas": pa.notes,
            }
            for pa in result.scalars().all()
        ]

    # ── Dietary Profiles ──

    async def set_dietary_profiles(
        self, product_id: int, tenant_id: int, profile_ids: list[int],
    ) -> list[int]:
        """Replace all dietary profile associations for a product."""
        await self._get_product(product_id, tenant_id)

        await self._db.execute(
            delete(ProductDietaryProfile).where(ProductDietaryProfile.product_id == product_id)
        )

        for pid in profile_ids:
            self._db.add(ProductDietaryProfile(product_id=product_id, dietary_profile_id=pid))

        await safe_commit(self._db)
        return profile_ids

    # ── Cooking Methods ──

    async def set_cooking_methods(
        self, product_id: int, tenant_id: int, method_ids: list[int],
    ) -> list[int]:
        """Replace all cooking method associations for a product."""
        await self._get_product(product_id, tenant_id)

        await self._db.execute(
            delete(ProductCookingMethod).where(ProductCookingMethod.product_id == product_id)
        )

        for mid in method_ids:
            self._db.add(ProductCookingMethod(product_id=product_id, cooking_method_id=mid))

        await safe_commit(self._db)
        return method_ids

    # ── Flavor Profiles ──

    async def set_flavor_profiles(
        self, product_id: int, tenant_id: int, profiles: list[str],
    ) -> list[str]:
        """Update the flavor_profiles_array column on Product."""
        product = await self._get_product(product_id, tenant_id)

        # Validate enum values
        valid = {e.value for e in FlavorProfileEnum}
        invalid = set(profiles) - valid
        if invalid:
            raise ValidationError(
                message=f"Perfiles de sabor invalidos: {', '.join(invalid)}"
            )

        product.flavor_profiles_array = profiles
        await safe_commit(self._db)
        return profiles

    # ── Texture Profiles ──

    async def set_texture_profiles(
        self, product_id: int, tenant_id: int, profiles: list[str],
    ) -> list[str]:
        """Update the texture_profiles_array column on Product."""
        product = await self._get_product(product_id, tenant_id)

        valid = {e.value for e in TextureProfileEnum}
        invalid = set(profiles) - valid
        if invalid:
            raise ValidationError(
                message=f"Perfiles de textura invalidos: {', '.join(invalid)}"
            )

        product.texture_profiles_array = profiles
        await safe_commit(self._db)
        return profiles

    # ── Ingredients ──

    async def set_ingredients(
        self, product_id: int, tenant_id: int, ingredients_data: list[dict],
    ) -> list[dict]:
        """Replace all ingredients for a product."""
        await self._get_product(product_id, tenant_id)

        await self._db.execute(
            delete(ProductIngredient).where(ProductIngredient.product_id == product_id)
        )

        for idx, item in enumerate(ingredients_data):
            pi = ProductIngredient(
                product_id=product_id,
                name=item["nombre"],
                quantity=item["cantidad"],
                unit=item["unidad"],
                sort_order=item.get("orden", idx),
                is_optional=item.get("es_opcional", False),
                notes=item.get("notas"),
            )
            self._db.add(pi)

        await safe_commit(self._db)

        result = await self._db.execute(
            select(ProductIngredient)
            .where(ProductIngredient.product_id == product_id)
            .order_by(ProductIngredient.sort_order)
        )
        return [
            {
                "id": pi.id,
                "nombre": pi.name,
                "cantidad": pi.quantity,
                "unidad": pi.unit,
                "orden": pi.sort_order,
                "es_opcional": pi.is_optional,
                "notas": pi.notes,
            }
            for pi in result.scalars().all()
        ]

    # ── Badges ──

    async def set_badges(
        self, product_id: int, tenant_id: int, badge_data: list[dict],
    ) -> list[dict]:
        """Replace all badge associations for a product."""
        await self._get_product(product_id, tenant_id)

        await self._db.execute(
            delete(ProductBadge).where(ProductBadge.product_id == product_id)
        )

        for item in badge_data:
            self._db.add(ProductBadge(
                product_id=product_id,
                badge_id=item["badge_id"],
                sort_order=item.get("sort_order", 0),
            ))

        await safe_commit(self._db)
        return badge_data

    # ── Seals ──

    async def set_seals(
        self, product_id: int, tenant_id: int, seal_data: list[dict],
    ) -> list[dict]:
        """Replace all seal associations for a product."""
        await self._get_product(product_id, tenant_id)

        await self._db.execute(
            delete(ProductSeal).where(ProductSeal.product_id == product_id)
        )

        for item in seal_data:
            self._db.add(ProductSeal(
                product_id=product_id,
                seal_id=item["seal_id"],
                sort_order=item.get("sort_order", 0),
            ))

        await safe_commit(self._db)
        return seal_data
