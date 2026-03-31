"""Table service — pure business logic for restaurant tables and FSM transitions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from shared.enums import TABLE_TRANSITIONS, TableStatus
from shared.exceptions import (
    ConflictError,
    InvalidStateError,
    NotFoundError,
    ValidationError,
)
from shared.infrastructure.db import safe_commit
from shared.models.room.table import Table
from shared.models.room.table_session import TableSession
from shared.repositories.sector_repository import SectorRepository
from shared.repositories.table_repository import TableRepository
from shared.repositories.table_session_repository import TableSessionRepository

logger = logging.getLogger(__name__)


def _table_to_dict(table: Table) -> dict:
    """Map Table model to Spanish API dict."""
    return {
        "id": table.id,
        "sector_id": table.sector_id,
        "numero": table.number,
        "capacidad": table.capacity,
        "estado": table.status,
        "codigo": table.code,
        "pos_x": table.pos_x,
        "pos_y": table.pos_y,
        "version": table.version,
        "status_changed_at": (
            table.status_changed_at.isoformat() if table.status_changed_at else None
        ),
        "occupied_at": table.occupied_at.isoformat() if table.occupied_at else None,
        "order_requested_at": (
            table.order_requested_at.isoformat() if table.order_requested_at else None
        ),
        "order_fulfilled_at": (
            table.order_fulfilled_at.isoformat() if table.order_fulfilled_at else None
        ),
        "check_requested_at": (
            table.check_requested_at.isoformat() if table.check_requested_at else None
        ),
        "session_count": table.session_count,
        "estado_activo": "activo" if table.is_active else "inactivo",
        "created_at": table.created_at.isoformat() if table.created_at else "",
        "updated_at": table.updated_at.isoformat() if table.updated_at else "",
    }


class TableService:
    """Business logic for table CRUD and FSM status transitions."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Queries ─────────────────────────────────────────────────────────

    async def list_tables(
        self,
        branch_id: int,
        sector_id: int | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """List tables for a branch with optional filters."""
        repo = TableRepository(self._db, branch_id)
        tables = await repo.get_by_branch(sector_id=sector_id, status=status)
        return [_table_to_dict(t) for t in tables]

    # ── Single create ───────────────────────────────────────────────────

    async def create_table(
        self, branch_id: int, data: dict, user_id: int
    ) -> dict:
        """Create a single table with auto-generated code."""
        sector_id = data["sector_id"]
        sector = await self._get_active_sector(branch_id, sector_id)

        table_repo = TableRepository(self._db, branch_id)

        # Auto-assign number if not provided
        number = data.get("numero")
        if number is None:
            max_num = await table_repo.get_max_number(sector_id)
            number = (max_num or 0) + 1

        # Check number collision
        existing = await table_repo.get_by_sector_and_number(sector_id, number)
        if existing is not None:
            raise ConflictError(
                message=f"Ya existe la mesa numero {number} en este sector"
            )

        code = f"{sector.prefix}-{number:02d}"

        table = Table(
            sector_id=sector_id,
            number=number,
            capacity=data.get("capacidad", 4),
            status=TableStatus.LIBRE,
            code=code,
            pos_x=data.get("pos_x"),
            pos_y=data.get("pos_y"),
            version=1,
            session_count=0,
            created_by=user_id,
        )

        self._db.add(table)
        await safe_commit(self._db)
        await self._db.refresh(table)

        logger.info("Table created: id=%d code=%s sector=%d", table.id, code, sector_id)
        return _table_to_dict(table)

    # ── Batch create ────────────────────────────────────────────────────

    async def batch_create(
        self, branch_id: int, data: dict, user_id: int
    ) -> dict:
        """Create multiple tables at once for a sector.

        ``data`` must include ``sector_id`` and ``cantidad``.
        Optionally ``numero_inicio`` (start number) and ``capacidad``.
        """
        sector_id = data["sector_id"]
        quantity = data["cantidad"]
        sector = await self._get_active_sector(branch_id, sector_id)

        table_repo = TableRepository(self._db, branch_id)

        # Determine start number
        start_number = data.get("numero_inicio")
        if start_number is None:
            max_num = await table_repo.get_max_number(sector_id)
            start_number = (max_num or 0) + 1

        numbers = list(range(start_number, start_number + quantity))

        # Collision check
        existing_nums = await table_repo.get_existing_numbers(sector_id, numbers)
        if existing_nums:
            raise ConflictError(
                message=f"Ya existen mesas con numeros {existing_nums} en este sector"
            )

        capacity = data.get("capacidad", 4)
        tables = [
            Table(
                sector_id=sector_id,
                number=num,
                capacity=capacity,
                status=TableStatus.LIBRE,
                code=f"{sector.prefix}-{num:02d}",
                version=1,
                session_count=0,
                created_by=user_id,
            )
            for num in numbers
        ]

        created = await table_repo.bulk_create(tables)

        logger.info(
            "Batch created %d tables for sector=%d branch=%d",
            len(created), sector_id, branch_id,
        )
        return {
            "cantidad_creadas": len(created),
            "mesas": [_table_to_dict(t) for t in created],
        }

    # ── Update ──────────────────────────────────────────────────────────

    async def update_table(
        self, table_id: int, branch_id: int, data: dict, user_id: int
    ) -> dict:
        """Update table properties. Only allowed when status is libre or inactiva."""
        table_repo = TableRepository(self._db, branch_id)
        table = await table_repo.get_by_id(table_id)
        if table is None:
            raise NotFoundError(message="Mesa no encontrada")

        if table.status not in (TableStatus.LIBRE, TableStatus.INACTIVA):
            raise InvalidStateError(
                message="Solo se puede editar una mesa libre o inactiva"
            )

        sector_changed = False
        if "sector_id" in data and data["sector_id"] is not None and data["sector_id"] != table.sector_id:
            new_sector = await self._get_active_sector(branch_id, data["sector_id"])
            table.sector_id = new_sector.id
            sector_changed = True

        if "capacidad" in data and data["capacidad"] is not None:
            table.capacity = data["capacidad"]
        if "pos_x" in data:
            table.pos_x = data["pos_x"]
        if "pos_y" in data:
            table.pos_y = data["pos_y"]

        # Regenerate code if sector changed
        if sector_changed:
            sector_repo = SectorRepository(self._db, branch_id)
            sector = await sector_repo.get_by_id(table.sector_id)
            table.code = f"{sector.prefix}-{table.number:02d}"

        table.updated_by = user_id
        await safe_commit(self._db)
        await self._db.refresh(table)

        logger.info("Table updated: id=%d branch=%d", table_id, branch_id)
        return _table_to_dict(table)

    # ── Delete ──────────────────────────────────────────────────────────

    async def delete_table(
        self, table_id: int, branch_id: int, user_id: int
    ) -> dict:
        """Soft-delete a table. Only allowed when libre or inactiva."""
        table_repo = TableRepository(self._db, branch_id)
        table = await table_repo.get_by_id(table_id)
        if table is None:
            raise NotFoundError(message="Mesa no encontrada")

        if table.status not in (TableStatus.LIBRE, TableStatus.INACTIVA):
            raise InvalidStateError(
                message="Solo se puede eliminar una mesa libre o inactiva"
            )

        table.soft_delete(user_id)
        await safe_commit(self._db)

        logger.info("Table deleted: id=%d branch=%d", table_id, branch_id)
        return {"message": "Mesa eliminada"}

    # ── FSM Status Transition ───────────────────────────────────────────

    async def transition_status(
        self,
        table_id: int,
        branch_id: int,
        new_status: str,
        version: int,
        user_id: int,
    ) -> dict:
        """Transition table status with optimistic locking and row-level lock.

        1. Acquire row lock (FOR UPDATE)
        2. Verify version matches (optimistic locking)
        3. Validate FSM transition
        4. Apply side effects (timestamps, session archiving)
        5. Bump version + commit
        """
        table_repo = TableRepository(self._db, branch_id)
        table = await table_repo.get_for_update(table_id)
        if table is None:
            raise NotFoundError(message="Mesa no encontrada")

        # Optimistic locking check
        if table.version != version:
            raise ConflictError(
                message="Version mismatch — la mesa fue modificada por otro usuario"
            )

        current_status = table.status
        valid_transitions = TABLE_TRANSITIONS.get(current_status, [])
        if new_status not in valid_transitions:
            raise InvalidStateError(
                message=f"Transicion invalida: {current_status} -> {new_status}"
            )

        now = datetime.now(timezone.utc)

        # Apply side effects based on target status
        if new_status == TableStatus.OCUPADA:
            table.occupied_at = now

        elif new_status == TableStatus.PEDIDO_SOLICITADO:
            table.order_requested_at = now

        elif new_status == TableStatus.PEDIDO_CUMPLIDO:
            table.order_fulfilled_at = now

        elif new_status == TableStatus.CUENTA:
            table.check_requested_at = now

        elif new_status == TableStatus.LIBRE and current_status == TableStatus.CUENTA:
            # Session ends — archive and reset
            await self._archive_session(table, user_id)

        elif new_status == TableStatus.LIBRE and current_status == TableStatus.OCUPADA:
            # Cancellation — guests left without ordering, clear temporal fields
            table.occupied_at = None

        elif new_status == TableStatus.INACTIVA:
            # Archive session if table was in an active state
            if current_status not in (TableStatus.LIBRE, TableStatus.INACTIVA):
                await self._archive_session(table, user_id)

        table.status = new_status
        table.status_changed_at = now
        table.version += 1

        await safe_commit(self._db)
        await self._db.refresh(table)

        logger.info(
            "Table transition: id=%d %s -> %s (v%d)",
            table_id, current_status, new_status, table.version,
        )
        return _table_to_dict(table)

    # ── Private helpers ─────────────────────────────────────────────────

    async def _archive_session(self, table: Table, user_id: int) -> None:
        """Create a TableSession record from the current table state, then reset."""
        now = datetime.now(timezone.utc)

        duration_minutes = None
        if table.occupied_at is not None:
            delta = now - table.occupied_at
            duration_minutes = int(delta.total_seconds() / 60)

        session_record = TableSession(
            table_id=table.id,
            opened_at=table.occupied_at or now,
            closed_at=now,
            opened_by=user_id,
            closed_by=user_id,
            status="closed",
            order_requested_at=table.order_requested_at,
            order_fulfilled_at=table.order_fulfilled_at,
            check_requested_at=table.check_requested_at,
            duration_minutes=duration_minutes,
        )

        self._db.add(session_record)

        # Reset temporal fields
        table.occupied_at = None
        table.order_requested_at = None
        table.order_fulfilled_at = None
        table.check_requested_at = None
        table.session_count += 1

    async def _get_active_sector(self, branch_id: int, sector_id: int):
        """Fetch a sector by ID, ensuring it's active and belongs to the branch."""
        sector_repo = SectorRepository(self._db, branch_id)
        sector = await sector_repo.get_by_id(sector_id)
        if sector is None:
            raise NotFoundError(message="Sector no encontrado")
        if not sector.is_active:
            raise ValidationError(message="El sector esta inactivo")
        return sector
