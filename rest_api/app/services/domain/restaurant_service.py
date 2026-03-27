"""Restaurant (Tenant) service — pure business logic.

Maps DB Tenant fields (English) to API fields (Spanish).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import ConflictError, NotFoundError
from shared.infrastructure.db import safe_commit
from shared.models.core.tenant import Tenant

logger = logging.getLogger(__name__)


def _slug_from_name(name: str) -> str:
    """Generate a URL slug from a name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


def _tenant_to_dict(tenant: Tenant) -> dict:
    """Map Tenant DB model to Spanish API dict."""
    return {
        "id": tenant.id,
        "nombre": tenant.name,
        "slug": tenant.slug,
        "descripcion": tenant.description,
        "logo_url": tenant.logo_url,
        "banner_url": tenant.banner_url,
        "telefono": tenant.phone,
        "email": tenant.email,
        "direccion": tenant.address,
    }


class RestaurantService:
    """Business logic for tenant/restaurant operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_tenant_id(self, tenant_id: int) -> dict:
        """Retrieve the restaurant (tenant) for the current user."""
        stmt = select(Tenant).where(
            Tenant.id == tenant_id,
            Tenant.deleted_at.is_(None),
        )
        result = await self._db.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            raise NotFoundError(message="Restaurante no encontrado")

        return _tenant_to_dict(tenant)

    async def update(self, tenant_id: int, data: dict, user_id: int) -> dict:
        """Update the restaurant (tenant) info."""
        stmt = select(Tenant).where(
            Tenant.id == tenant_id,
            Tenant.deleted_at.is_(None),
        )
        result = await self._db.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            raise NotFoundError(message="Restaurante no encontrado")

        # Check slug uniqueness if changing
        new_slug = data.get("slug")
        if new_slug and new_slug != tenant.slug:
            slug_check = await self._db.execute(
                select(Tenant).where(
                    Tenant.slug == new_slug,
                    Tenant.id != tenant_id,
                    Tenant.deleted_at.is_(None),
                )
            )
            if slug_check.scalar_one_or_none() is not None:
                raise ConflictError(message="Slug ya existe")

        # Apply updates (map Spanish -> English DB fields)
        field_map = {
            "nombre": "name",
            "slug": "slug",
            "descripcion": "description",
            "logo_url": "logo_url",
            "banner_url": "banner_url",
            "telefono": "phone",
            "email": "email",
            "direccion": "address",
        }

        for api_field, db_field in field_map.items():
            if api_field in data:
                setattr(tenant, db_field, data[api_field])

        tenant.updated_by = user_id
        await safe_commit(self._db)
        await self._db.refresh(tenant)

        return _tenant_to_dict(tenant)
