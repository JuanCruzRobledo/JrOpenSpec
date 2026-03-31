"""Assignment service — pure business logic for waiter-sector assignments."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.exceptions import NotFoundError, ValidationError
from shared.infrastructure.db import safe_commit
from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
from shared.models.room.sector import Sector
from shared.models.services.waiter_sector_assignment import WaiterSectorAssignment
from shared.repositories.assignment_repository import AssignmentRepository

logger = logging.getLogger(__name__)

VALID_SHIFTS = {"morning", "afternoon", "night"}


def _assignment_to_dict(a: WaiterSectorAssignment) -> dict:
    """Map WaiterSectorAssignment model to Spanish API dict."""
    return {
        "id": a.id,
        "mozo": {
            "id": a.user.id,
            "nombre_completo": f"{a.user.first_name} {a.user.last_name}",
        },
        "sector": {
            "id": a.sector.id,
            "nombre": a.sector.name,
        },
        "turno": a.shift,
        "fecha": a.date.isoformat(),
    }


class AssignmentService:
    """Business logic for waiter-sector assignment operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Queries ─────────────────────────────────────────────────────────

    async def list_assignments(self, branch_id: int, date_: date) -> dict:
        """List assignments for a branch on a date, grouped by shift.

        Returns::

            {
                "morning": [...],
                "afternoon": [...],
                "night": [...],
            }
        """
        repo = AssignmentRepository(self._db)
        assignments = await repo.get_by_date(branch_id, date_)

        grouped: dict[str, list[dict]] = {
            "morning": [],
            "afternoon": [],
            "night": [],
        }
        for a in assignments:
            shift_key = a.shift.lower()
            if shift_key in grouped:
                grouped[shift_key].append(_assignment_to_dict(a))
            else:
                grouped[shift_key] = [_assignment_to_dict(a)]

        return grouped

    # ── Commands ────────────────────────────────────────────────────────

    async def bulk_save(
        self,
        branch_id: int,
        date_: date,
        shift: str,
        assignments: list[dict],
        user_id: int,
    ) -> dict:
        """Atomic delete-and-reinsert for assignments on a date+shift.

        Validates ALL assignments first (waiter exists + is WAITER,
        sector exists + is active), then deletes old and creates new.
        """
        shift_lower = shift.lower()
        if shift_lower not in VALID_SHIFTS:
            raise ValidationError(
                message=f"Turno '{shift}' no es valido. Turnos validos: {', '.join(VALID_SHIFTS)}"
            )

        # Phase 1: Validate ALL assignments before making any changes
        validated: list[dict] = []
        for idx, entry in enumerate(assignments):
            waiter_id = entry.get("mozo_id")
            sector_id = entry.get("sector_id")

            if waiter_id is None or sector_id is None:
                raise ValidationError(
                    message=f"Asignacion #{idx + 1}: se requieren mozo_id y sector_id"
                )

            await self._validate_waiter(waiter_id, branch_id)
            await self._validate_sector(sector_id)

            validated.append({
                "user_id": waiter_id,
                "sector_id": sector_id,
            })

        # Phase 2: Delete existing assignments for this date+shift+branch
        repo = AssignmentRepository(self._db)
        deleted_count = await repo.delete_by_date_shift(branch_id, date_, shift_lower)

        # Phase 3: Create new assignments
        new_assignments = [
            WaiterSectorAssignment(
                user_id=v["user_id"],
                branch_id=branch_id,
                sector_id=v["sector_id"],
                date=date_,
                shift=shift_lower,
                created_by=user_id,
            )
            for v in validated
        ]

        if new_assignments:
            created = await repo.bulk_create(new_assignments)
        else:
            created = []

        logger.info(
            "Bulk save assignments: branch=%d date=%s shift=%s deleted=%d created=%d",
            branch_id, date_, shift_lower, deleted_count, len(created),
        )

        return {
            "turno": shift_lower,
            "fecha": date_.isoformat(),
            "eliminadas": deleted_count,
            "creadas": len(created),
        }

    async def delete_assignment(self, assignment_id: int) -> dict:
        """Soft-delete a single assignment."""
        repo = AssignmentRepository(self._db)
        assignment = await repo.get_by_id(assignment_id)
        if assignment is None:
            raise NotFoundError(message="Asignacion no encontrada")

        assignment.soft_delete()
        await safe_commit(self._db)

        logger.info("Assignment deleted: id=%d", assignment_id)
        return {"message": "Asignacion eliminada", "id": assignment_id}

    # ── Private validation helpers ──────────────────────────────────────

    async def _validate_waiter(self, user_id: int, branch_id: int) -> None:
        """Check user exists, is active, and has WAITER role."""
        from sqlalchemy import select

        stmt = (
            select(User)
            .where(
                User.id == user_id,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
            .options(selectinload(User.branch_roles))
        )
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise ValidationError(
                message=f"Mozo con id={user_id} no encontrado o inactivo"
            )

        has_waiter_role = any(
            r.role == "WAITER" for r in user.branch_roles
        )
        if not has_waiter_role:
            raise ValidationError(
                message=f"El usuario id={user_id} no tiene rol WAITER"
            )

    async def _validate_sector(self, sector_id: int) -> None:
        """Check sector exists and is active."""
        from sqlalchemy import select

        stmt = select(Sector).where(
            Sector.id == sector_id,
            Sector.is_active.is_(True),
            Sector.deleted_at.is_(None),
        )
        result = await self._db.execute(stmt)
        sector = result.scalar_one_or_none()

        if sector is None:
            raise ValidationError(
                message=f"Sector con id={sector_id} no encontrado o inactivo"
            )
