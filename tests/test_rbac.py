"""Focused RBAC tests for the reconciled PermissionContext contract."""

import pytest

from rest_api.app.services.permissions.context import PermissionContext
from rest_api.app.services.permissions.strategies import Action, AdminStrategy, ManagerStrategy
from shared.exceptions import BranchAccessError, ForbiddenError, InsufficientRoleError


class TestPermissionContextBranchAccess:
    """REQ-RBAC-01: Branch access control via PermissionContext."""

    def test_branch_access_allowed(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1, 2],
            "roles": ["ADMIN"],
        })

        ctx.require_branch_access(1)

    def test_branch_access_denied(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1, 2],
            "roles": ["MANAGER"],
        })

        with pytest.raises(BranchAccessError, match="Branch access denied"):
            ctx.require_branch_access(3)

    def test_superadmin_bypasses_branch_access(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [],
            "roles": [],
            "is_superadmin": True,
        })

        ctx.require_branch_access(999)


class TestPermissionContextRoleChecks:
    """REQ-RBAC-01: Role-based access checks."""

    def test_require_admin_with_admin_role(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["ADMIN"],
        })

        ctx.require_admin()

    def test_require_admin_with_waiter_role(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["WAITER"],
        })

        with pytest.raises(InsufficientRoleError, match="Admin role required"):
            ctx.require_admin()

    def test_require_management_with_manager(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["MANAGER"],
        })

        ctx.require_management()

    def test_require_management_blocks_waiter(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["WAITER"],
        })

        with pytest.raises(InsufficientRoleError, match="Management role required"):
            ctx.require_management()

    def test_require_management_blocks_kitchen(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["KITCHEN"],
        })

        with pytest.raises(InsufficientRoleError, match="Management role required"):
            ctx.require_management()

    def test_require_role_matching(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["WAITER"],
        })

        ctx.require_role("WAITER")

    def test_require_role_not_matching(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["WAITER"],
        })

        with pytest.raises(InsufficientRoleError, match="Role 'ADMIN' required"):
            ctx.require_role("ADMIN")

    def test_require_any_role_denies_when_none_match(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["KITCHEN"],
        })

        with pytest.raises(InsufficientRoleError, match="Insufficient role"):
            ctx.require_any_role(["ADMIN", "MANAGER"])


class TestStrategyDispatch:
    """REQ-RBAC-02: Strategy pattern dispatch via PermissionContext.can()."""

    def test_admin_strategy_selected_for_admin(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["ADMIN"],
        })

        assert isinstance(ctx.strategy, AdminStrategy)
        assert ctx.can(Action.DELETE, "Tenant") is True

    def test_highest_privilege_strategy_selected(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["WAITER", "MANAGER"],
        })

        assert isinstance(ctx.strategy, ManagerStrategy)
        ctx.require_management()
        assert ctx.can(Action.MANAGE, "StaffAssignment") is True
        assert ctx.can(Action.DELETE, "Product") is False

    def test_require_can_raises_for_denied_action_resource_pair(self):
        ctx = PermissionContext({
            "sub": "1",
            "tenant_id": 1,
            "branch_ids": [1],
            "roles": ["WAITER"],
        })

        with pytest.raises(ForbiddenError, match="Cannot delete Product"):
            ctx.require_can(Action.DELETE, "Product")
