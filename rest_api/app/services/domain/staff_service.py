"""Staff service — pure business logic for staff (user) management."""

from __future__ import annotations

import logging
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.exceptions import ConflictError, DuplicateError, ForbiddenError, NotFoundError, ValidationError
from shared.infrastructure.db import safe_commit
from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
from shared.repositories.assignment_repository import AssignmentRepository
from shared.repositories.staff_repository import StaffRepository
from shared.security.passwords import hash_password

logger = logging.getLogger(__name__)

# Role hierarchy for assignment validation
_ROLE_HIERARCHY: dict[str, int] = {
    "ADMIN": 100,
    "MANAGER": 80,
    "KITCHEN": 40,
    "WAITER": 40,
    "READONLY": 10,
}

# Roles that a MANAGER can assign (everything except ADMIN)
_MANAGER_ASSIGNABLE = {"MANAGER", "KITCHEN", "WAITER", "READONLY"}


def _staff_to_dict(user: User) -> dict:
    """Map User model to Spanish API dict. NEVER includes password."""
    return {
        "id": user.id,
        "nombre_completo": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "telefono": user.phone,
        "rol": user.branch_roles[0].role if user.branch_roles else None,
        "dni": user.dni,
        "fecha_contratacion": user.hired_at.isoformat() if user.hired_at else None,
        "estado": "activo" if user.is_active else "inactivo",
        "created_at": user.created_at.isoformat() if user.created_at else "",
    }


class StaffService:
    """Business logic for staff CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Queries ─────────────────────────────────────────────────────────

    async def list_staff(
        self,
        tenant_id: int,
        q: str | None = None,
        role: str | None = None,
        is_active: bool = True,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """List staff with optional search, role filter, and pagination."""
        repo = StaffRepository(self._db, tenant_id)
        users, total = await repo.search(
            q=q, role=role, is_active=is_active, page=page, limit=limit
        )
        return [_staff_to_dict(u) for u in users], total

    async def get_staff(self, user_id: int, tenant_id: int) -> dict:
        """Get a single staff member by ID."""
        repo = StaffRepository(self._db, tenant_id)
        user = await repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(message="Staff no encontrado")

        # Ensure branch_roles are loaded
        await self._db.refresh(user, ["branch_roles"])
        return _staff_to_dict(user)

    # ── Commands ────────────────────────────────────────────────────────

    async def create_staff(
        self, tenant_id: int, data: dict, current_user: dict
    ) -> dict:
        """Create a new staff member with role assignment.

        Validates:
        - Role assignment rules (who can assign what)
        - Email uniqueness within the tenant
        - Hashes password before storing
        """
        assigner_roles = current_user.get("roles", [])
        target_role = data.get("rol", "READONLY")

        self._validate_role_assignment(assigner_roles, target_role)

        # Check email uniqueness within tenant
        repo = StaffRepository(self._db, tenant_id)
        existing = await repo.get_by_email(data["email"])
        if existing is not None:
            raise DuplicateError(
                message=f"Ya existe un usuario con el email '{data['email']}' en este tenant"
            )

        # Validate role name
        if target_role not in _ROLE_HIERARCHY:
            raise ValidationError(
                message=f"Rol '{target_role}' no es valido. Roles validos: {', '.join(_ROLE_HIERARCHY.keys())}"
            )

        # Create user
        user = User(
            tenant_id=tenant_id,
            email=data["email"],
            hashed_password=hash_password(data["password"]),
            first_name=data["nombre"],
            last_name=data["apellido"],
            phone=data.get("telefono"),
            dni=data.get("dni"),
            hired_at=data.get("fecha_contratacion", date.today()),
            created_by=current_user.get("id"),
        )

        self._db.add(user)
        await safe_commit(self._db)
        await self._db.refresh(user)

        # Create branch role
        branch_id = data.get("sucursal_id") or current_user.get("branch_id")
        if branch_id is None:
            raise ValidationError(message="Se requiere sucursal_id para asignar el rol")

        role = UserBranchRole(
            user_id=user.id,
            branch_id=branch_id,
            role=target_role,
        )
        self._db.add(role)
        await safe_commit(self._db)

        # Reload with relationships
        await self._db.refresh(user, ["branch_roles"])

        logger.info(
            "Staff created: id=%d email=%s role=%s tenant=%d",
            user.id, user.email, target_role, tenant_id,
        )
        return _staff_to_dict(user)

    async def update_staff(
        self, user_id: int, tenant_id: int, data: dict, current_user: dict
    ) -> dict:
        """Update a staff member. Re-validates role assignment if role changes."""
        repo = StaffRepository(self._db, tenant_id)
        user = await repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(message="Staff no encontrado")

        await self._db.refresh(user, ["branch_roles"])

        # Role change validation
        new_role = data.get("rol")
        if new_role is not None:
            assigner_roles = current_user.get("roles", [])
            self._validate_role_assignment(assigner_roles, new_role)

            if new_role not in _ROLE_HIERARCHY:
                raise ValidationError(
                    message=f"Rol '{new_role}' no es valido"
                )

            # Update or create the branch role
            if user.branch_roles:
                user.branch_roles[0].role = new_role
            else:
                branch_id = data.get("sucursal_id") or current_user.get("branch_id")
                if branch_id is None:
                    raise ValidationError(message="Se requiere sucursal_id para asignar el rol")
                role = UserBranchRole(
                    user_id=user.id,
                    branch_id=branch_id,
                    role=new_role,
                )
                self._db.add(role)

        # Update basic fields
        if "nombre" in data and data["nombre"] is not None:
            user.first_name = data["nombre"]
        if "apellido" in data and data["apellido"] is not None:
            user.last_name = data["apellido"]
        if "email" in data and data["email"] is not None:
            # Check uniqueness if changing
            if data["email"].lower() != user.email.lower():
                existing = await repo.get_by_email(data["email"])
                if existing is not None:
                    raise DuplicateError(
                        message=f"Ya existe un usuario con el email '{data['email']}'"
                    )
            user.email = data["email"]
        if "telefono" in data:
            user.phone = data["telefono"]
        if "dni" in data:
            user.dni = data["dni"]
        if "fecha_contratacion" in data:
            user.hired_at = data["fecha_contratacion"]
        if "password" in data and data["password"]:
            user.hashed_password = hash_password(data["password"])

        user.updated_by = current_user.get("id")
        await safe_commit(self._db)
        await self._db.refresh(user, ["branch_roles"])

        logger.info("Staff updated: id=%d tenant=%d", user_id, tenant_id)
        return _staff_to_dict(user)

    async def delete_staff(self, user_id: int, tenant_id: int) -> dict:
        """Soft-delete a staff member. Blocks if active assignments exist for today."""
        repo = StaffRepository(self._db, tenant_id)
        user = await repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(message="Staff no encontrado")

        # Check for today's active assignments
        assignment_repo = AssignmentRepository(self._db)
        has_assignments = await assignment_repo.has_active_assignments(
            waiter_id=user_id, date_=date.today()
        )
        if has_assignments:
            raise ConflictError(
                message="No se puede eliminar un staff con asignaciones activas para hoy. "
                "Elimine las asignaciones primero."
            )

        user.soft_delete()
        await safe_commit(self._db)

        logger.info("Staff deleted: id=%d tenant=%d", user_id, tenant_id)
        return {"message": "Staff eliminado", "id": user_id}

    # ── Private helpers ─────────────────────────────────────────────────

    @staticmethod
    def _validate_role_assignment(
        assigner_roles: list[str], target_role: str
    ) -> None:
        """Validate that the assigner can assign the target role.

        Rules:
        - ADMIN can assign any role
        - MANAGER can assign MANAGER, KITCHEN, WAITER, READONLY (NOT ADMIN)
        - Others get 403
        """
        if not assigner_roles:
            raise ForbiddenError(message="No tiene permisos para asignar roles")

        # Check if assigner has ADMIN role
        if "ADMIN" in assigner_roles:
            return

        # Check if assigner has MANAGER role
        if "MANAGER" in assigner_roles:
            if target_role not in _MANAGER_ASSIGNABLE:
                raise ForbiddenError(
                    message=f"Un MANAGER no puede asignar el rol '{target_role}'"
                )
            return

        # All other roles cannot assign
        raise ForbiddenError(
            message="No tiene permisos para asignar roles. Se requiere ADMIN o MANAGER."
        )
