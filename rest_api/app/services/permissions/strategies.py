"""RBAC Strategy Pattern — per-role permission strategies.

Each strategy defines what actions a role can perform on each resource type.
PermissionContext selects the highest-privilege strategy from the user's roles.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod


class Action(str, enum.Enum):
    """Actions that can be checked against RBAC strategies."""

    CREATE = "create"
    READ = "read"
    EDIT = "edit"
    DELETE = "delete"
    MANAGE = "manage"  # Administrative operations (e.g. assign staff)


class BaseStrategy(ABC):
    """Abstract base for role-specific permission strategies."""

    # Priority used when selecting highest-privilege strategy.
    # Higher number = more privileges.
    priority: int = 0

    @abstractmethod
    def can(self, action: Action, resource: str, **context: object) -> bool:
        """Check whether this role can perform *action* on *resource*.

        Args:
            action: The Action being attempted.
            resource: Resource type name (e.g. "Product", "Order", "User").
            **context: Extra context such as branch_id, owner_id, etc.

        Returns:
            True if the action is allowed, False otherwise.
        """


class AdminStrategy(BaseStrategy):
    """ADMIN — full access to everything within the tenant."""

    priority = 100

    def can(self, action: Action, resource: str, **context: object) -> bool:
        # Admin can do anything
        return True


class ManagerStrategy(BaseStrategy):
    """MANAGER — can read/manage most resources, limited create/delete.

    Managers can manage staff, view reports, and handle day-to-day
    operations within their assigned branches.
    """

    priority = 75

    # Resources managers can fully manage
    _full_access: frozenset[str] = frozenset({
        "Order", "Round", "Table", "Sector", "ServiceCall",
        "Check", "Category", "Promotion", "Recipe", "Ingredient",
    })

    # Resources managers can read but not create/delete
    _read_only: frozenset[str] = frozenset({
        "Product", "User", "Branch", "Tenant", "AuditLog",
    })

    # Resources managers can manage (assign, unassign)
    _manageable: frozenset[str] = frozenset({
        "StaffAssignment", "WaiterSector",
    })

    def can(self, action: Action, resource: str, **context: object) -> bool:
        if resource in self._full_access:
            return True
        if resource in self._read_only:
            return action == Action.READ
        if resource in self._manageable:
            return action in (Action.READ, Action.MANAGE, Action.CREATE, Action.DELETE)
        return False


class KitchenStrategy(BaseStrategy):
    """KITCHEN — can view and update orders/rounds relevant to the kitchen."""

    priority = 25

    _allowed_resources: frozenset[str] = frozenset({
        "Order", "Round", "KitchenTicket", "Product", "Recipe", "Ingredient",
    })

    def can(self, action: Action, resource: str, **context: object) -> bool:
        if resource not in self._allowed_resources:
            return False
        # Kitchen can read anything in their scope, edit orders/rounds/tickets
        if action == Action.READ:
            return True
        if action == Action.EDIT and resource in ("Order", "Round", "KitchenTicket"):
            return True
        return False


class WaiterStrategy(BaseStrategy):
    """WAITER — can manage orders and tables within assigned sectors."""

    priority = 10

    _read_resources: frozenset[str] = frozenset({
        "Product", "Category", "Table", "Sector", "Promotion",
        "Allergen", "DietaryProfile",
    })

    _manage_resources: frozenset[str] = frozenset({
        "Order", "Round", "ServiceCall",
    })

    def can(self, action: Action, resource: str, **context: object) -> bool:
        if resource in self._read_resources:
            return action == Action.READ
        if resource in self._manage_resources:
            return action in (Action.READ, Action.CREATE, Action.EDIT)
        if resource == "Table":
            return action in (Action.READ, Action.EDIT)
        return False


# Registry: role name → strategy instance (singletons)
STRATEGY_REGISTRY: dict[str, BaseStrategy] = {
    "ADMIN": AdminStrategy(),
    "MANAGER": ManagerStrategy(),
    "KITCHEN": KitchenStrategy(),
    "WAITER": WaiterStrategy(),
}
