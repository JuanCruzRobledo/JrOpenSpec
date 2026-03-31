"""Sector service — pure business logic for restaurant sectors."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from shared.enums import SECTOR_PREFIX_MAP, SectorType, TableStatus
from shared.exceptions import DuplicateError, NotFoundError, ValidationError
from shared.infrastructure.db import safe_commit
from shared.models.room.sector import Sector
from shared.repositories.sector_repository import SectorRepository

logger = logging.getLogger(__name__)


def _sector_to_dict(sector: Sector) -> dict:
    """Map Sector model to Spanish API dict."""
    return {
        "id": sector.id,
        "sucursal_id": sector.branch_id,
        "nombre": sector.name,
        "tipo": sector.type,
        "prefijo": sector.prefix,
        "capacidad": sector.capacity,
        "orden": sector.display_order,
        "estado": "activo" if sector.is_active else "inactivo",
        "created_at": sector.created_at.isoformat() if sector.created_at else "",
        "updated_at": sector.updated_at.isoformat() if sector.updated_at else "",
    }


class SectorService:
    """Business logic for sector CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Queries ─────────────────────────────────────────────────────────

    async def list_sectors(
        self, branch_id: int, include_inactive: bool = False
    ) -> list[dict]:
        """List all sectors for a branch."""
        repo = SectorRepository(self._db, branch_id)
        sectors = await repo.get_by_branch(include_inactive=include_inactive)
        return [_sector_to_dict(s) for s in sectors]

    async def get_sector(self, sector_id: int, branch_id: int) -> dict:
        """Get a single sector by ID."""
        repo = SectorRepository(self._db, branch_id)
        sector = await repo.get_by_id(sector_id)
        if sector is None:
            raise NotFoundError(message="Sector no encontrado")
        return _sector_to_dict(sector)

    # ── Commands ────────────────────────────────────────────────────────

    async def create_sector(
        self, branch_id: int, data: dict, user_id: int
    ) -> dict:
        """Create a new sector with auto-generated prefix."""
        repo = SectorRepository(self._db, branch_id)
        nombre = data["nombre"]
        sector_type = data.get("tipo", SectorType.INTERIOR)

        # Validate name uniqueness (case-insensitive)
        existing = await repo.get_by_name(nombre)
        if existing is not None:
            raise DuplicateError(
                message=f"Ya existe un sector con el nombre '{nombre}' en esta sucursal"
            )

        # Auto-generate prefix
        prefix = await self._generate_prefix(sector_type, branch_id)

        sector = Sector(
            branch_id=branch_id,
            name=nombre,
            type=sector_type,
            prefix=prefix,
            capacity=data.get("capacidad"),
            display_order=data.get("orden", 0),
            created_by=user_id,
        )

        self._db.add(sector)
        await safe_commit(self._db)
        await self._db.refresh(sector)

        logger.info("Sector created: id=%d name=%s branch=%d", sector.id, nombre, branch_id)
        return _sector_to_dict(sector)

    async def update_sector(
        self, sector_id: int, branch_id: int, data: dict, user_id: int
    ) -> dict:
        """Update a sector. Recalculates prefix if type changes."""
        repo = SectorRepository(self._db, branch_id)
        sector = await repo.get_by_id(sector_id)
        if sector is None:
            raise NotFoundError(message="Sector no encontrado")

        # Check name uniqueness if changing
        if "nombre" in data and data["nombre"] is not None:
            new_name = data["nombre"]
            if new_name.lower() != sector.name.lower():
                existing = await repo.get_by_name(new_name)
                if existing is not None:
                    raise DuplicateError(
                        message=f"Ya existe un sector con el nombre '{new_name}' en esta sucursal"
                    )
            sector.name = new_name

        # Recalculate prefix if type changes
        type_changed = False
        if "tipo" in data and data["tipo"] is not None and data["tipo"] != sector.type:
            sector.type = data["tipo"]
            sector.prefix = await self._generate_prefix(data["tipo"], branch_id)
            type_changed = True

        if "capacidad" in data:
            sector.capacity = data["capacidad"]
        if "orden" in data and data["orden"] is not None:
            sector.display_order = data["orden"]
        if "estado" in data and data["estado"] is not None:
            sector.is_active = data["estado"] == "activo"

        sector.updated_by = user_id
        await safe_commit(self._db)
        await self._db.refresh(sector)

        # If prefix changed, regenerate table codes
        if type_changed:
            await self._regenerate_table_codes(sector)

        logger.info("Sector updated: id=%d branch=%d", sector_id, branch_id)
        return _sector_to_dict(sector)

    async def delete_sector(
        self, sector_id: int, branch_id: int, user_id: int
    ) -> dict:
        """Soft-delete a sector. Blocks if non-libre active tables exist."""
        repo = SectorRepository(self._db, branch_id)
        sector = await repo.get_by_id(sector_id)
        if sector is None:
            raise NotFoundError(message="Sector no encontrado")

        # Check for active tables that are not libre/inactiva
        active_tables = [
            t for t in sector.tables
            if t.deleted_at is None
            and t.is_active
            and t.status not in (TableStatus.LIBRE, TableStatus.INACTIVA)
        ]
        if active_tables:
            raise ValidationError(
                message="No se puede eliminar un sector con mesas activas (no libres)"
            )

        # Cascade soft-delete to all non-deleted tables
        table_count = 0
        for table in sector.tables:
            if table.deleted_at is None:
                table.soft_delete(user_id)
                table_count += 1

        sector.soft_delete(user_id)
        await safe_commit(self._db)

        logger.info(
            "Sector deleted: id=%d branch=%d cascaded_tables=%d",
            sector_id, branch_id, table_count,
        )
        return {
            "message": "Sector eliminado",
            "cascade": {"mesas": table_count},
        }

    # ── Private helpers ─────────────────────────────────────────────────

    async def _generate_prefix(self, sector_type: str, branch_id: int) -> str:
        """Generate a unique prefix for the sector type within the branch.

        Algorithm:
        1. Look up base prefix from SECTOR_PREFIX_MAP (e.g., "interior" -> "INT")
        2. Check if prefix already exists for this branch
        3. If collision, append incrementing number: INT2, INT3, etc.
        """
        repo = SectorRepository(self._db, branch_id)
        base_prefix = SECTOR_PREFIX_MAP.get(sector_type, sector_type[:3].upper())

        # Try the base prefix first
        candidate = base_prefix
        existing = await repo.get_by_prefix(candidate)
        if existing is None:
            return candidate

        # Collision — append incrementing number
        counter = 2
        while True:
            candidate = f"{base_prefix}{counter}"
            existing = await repo.get_by_prefix(candidate)
            if existing is None:
                return candidate
            counter += 1
            if counter > 99:
                raise ValidationError(
                    message=f"No se pudo generar un prefijo unico para tipo '{sector_type}'"
                )

    async def _regenerate_table_codes(self, sector: Sector) -> None:
        """Regenerate codes for all active tables in the sector after prefix change."""
        for table in sector.tables:
            if table.deleted_at is None:
                table.code = f"{sector.prefix}-{table.number:02d}"

        await safe_commit(self._db)
        logger.info(
            "Regenerated table codes for sector id=%d prefix=%s",
            sector.id, sector.prefix,
        )
