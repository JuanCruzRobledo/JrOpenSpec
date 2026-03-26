"""PermissionContext — authorization facade built from a JWT user dict.

Usage in routers::

    @router.post("/products")
    async def create_product(
        body: ProductCreate,
        user: dict = Depends(get_current_user),
    ):
        ctx = PermissionContext(user)
        ctx.require_management()
        ctx.require_branch_access(body.branch_id)
        ...
"""

from __future__ import annotations

import logging

from shared.exceptions import BranchAccessError, ForbiddenError, InsufficientRoleError

from rest_api.app.services.permissions.strategies import (
    STRATEGY_REGISTRY,
    Action,
    BaseStrategy,
)

logger = logging.getLogger(__name__)

# Roles considered "management" (can access admin/dashboard features)
MANAGEMENT_ROLES: frozenset[str] = frozenset({"ADMIN", "MANAGER"})


class PermissionContext:
    """Authorization context derived from the current user's JWT payload.

    Attributes:
        user_id: The authenticated user's id (str from JWT ``sub``).
        tenant_id: Tenant the user belongs to.
        branch_ids: List of branch ids the user has access to.
        roles: List of role strings from the JWT.
        is_superadmin: Whether the user is a superadmin.
        strategy: The highest-privilege strategy selected from the user's roles.
    """

    def __init__(self, user: dict) -> None:
        self.user_id: str = user["sub"]
        self.tenant_id: int = user["tenant_id"]
        self.branch_ids: list[int] = user.get("branch_ids", [])
        self.roles: list[str] = user.get("roles", [])
        self.is_superadmin: bool = user.get("is_superadmin", False)
        self.strategy: BaseStrategy | None = self._select_strategy()

    def _select_strategy(self) -> BaseStrategy | None:
        """Select the highest-priority strategy from the user's roles."""
        best: BaseStrategy | None = None
        for role in self.roles:
            strategy = STRATEGY_REGISTRY.get(role)
            if strategy is not None and (best is None or strategy.priority > best.priority):
                best = strategy
        return best

    # --- Guard methods (raise on failure) ---

    def require_management(self) -> None:
        """Raise ForbiddenError if user has no management role (ADMIN or MANAGER)."""
        if self.is_superadmin:
            return
        if not set(self.roles) & MANAGEMENT_ROLES:
            raise InsufficientRoleError(
                message="Management role required",
                detail=f"User roles {self.roles} do not include ADMIN or MANAGER",
            )

    def require_admin(self) -> None:
        """Raise ForbiddenError if user is not ADMIN or superadmin."""
        if self.is_superadmin:
            return
        if "ADMIN" not in self.roles:
            raise InsufficientRoleError(
                message="Admin role required",
                detail=f"User roles {self.roles} do not include ADMIN",
            )

    def require_branch_access(self, branch_id: int) -> None:
        """Raise BranchAccessError if user is not assigned to *branch_id*.

        Superadmins bypass this check.
        """
        if self.is_superadmin:
            return
        if branch_id not in self.branch_ids:
            raise BranchAccessError(
                message="Branch access denied",
                detail=f"User does not have access to branch {branch_id}",
            )

    def require_role(self, role: str) -> None:
        """Raise InsufficientRoleError if user does not hold *role*."""
        if self.is_superadmin:
            return
        if role not in self.roles:
            raise InsufficientRoleError(
                message=f"Role '{role}' required",
                detail=f"User roles {self.roles} do not include {role}",
            )

    def require_any_role(self, roles: list[str] | tuple[str, ...]) -> None:
        """Raise InsufficientRoleError if user holds none of the given *roles*."""
        if self.is_superadmin:
            return
        if not set(self.roles) & set(roles):
            raise InsufficientRoleError(
                message="Insufficient role",
                detail=f"User roles {self.roles} do not include any of {list(roles)}",
            )

    # --- Query methods (return bool) ---

    def can(self, action: Action, resource: str, **context: object) -> bool:
        """Check whether the current user can perform *action* on *resource*.

        Superadmins always return True.  If no strategy is found for the
        user's roles, returns False.
        """
        if self.is_superadmin:
            return True
        if self.strategy is None:
            return False
        return self.strategy.can(action, resource, **context)

    def require_can(self, action: Action, resource: str, **context: object) -> None:
        """Like :meth:`can` but raises ForbiddenError on denial."""
        if not self.can(action, resource, **context):
            raise ForbiddenError(
                message=f"Cannot {action.value} {resource}",
                detail=f"Roles {self.roles} lack permission for {action.value} on {resource}",
            )
