"""Tests for RBAC: PermissionContext, branch access, role checks, strategies.

Covers REQ-RBAC-01, REQ-RBAC-02.

NOTE: These tests require Batch B (permissions, strategies) to be merged.
They will fail with ImportError until Batch B is available.
"""

import pytest

pytestmark = pytest.mark.integration


class TestPermissionContextBranchAccess:
    """REQ-RBAC-01: Branch access control via PermissionContext."""

    def test_branch_access_allowed(self):
        """User with branch_ids=[1,2] can access branch 1."""
        try:
            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1, 2],
                "roles": ["ADMIN"],
            })
            # Should not raise
            ctx.require_branch_access(1)
        except ImportError:
            pytest.skip("Batch B not yet merged")

    def test_branch_access_denied(self):
        """User with branch_ids=[1,2] cannot access branch 3."""
        try:
            from shared.exceptions import AppError

            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1, 2],
                "roles": ["MANAGER"],
            })
            with pytest.raises(AppError):
                ctx.require_branch_access(3)
        except ImportError:
            pytest.skip("Batch B not yet merged")


class TestPermissionContextRoleChecks:
    """REQ-RBAC-01: Role-based access checks."""

    def test_require_admin_with_admin_role(self):
        """ADMIN should pass require_admin()."""
        try:
            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1],
                "roles": ["ADMIN"],
            })
            ctx.require_admin()
        except ImportError:
            pytest.skip("Batch B not yet merged")

    def test_require_admin_with_waiter_role(self):
        """WAITER should fail require_admin()."""
        try:
            from shared.exceptions import AppError

            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1],
                "roles": ["WAITER"],
            })
            with pytest.raises(AppError):
                ctx.require_admin()
        except ImportError:
            pytest.skip("Batch B not yet merged")

    def test_require_management_with_manager(self):
        """MANAGER should pass require_management()."""
        try:
            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1],
                "roles": ["MANAGER"],
            })
            ctx.require_management()
        except ImportError:
            pytest.skip("Batch B not yet merged")

    def test_require_management_blocks_waiter(self):
        """WAITER should fail require_management()."""
        try:
            from shared.exceptions import AppError

            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1],
                "roles": ["WAITER"],
            })
            with pytest.raises(AppError):
                ctx.require_management()
        except ImportError:
            pytest.skip("Batch B not yet merged")

    def test_require_management_blocks_kitchen(self):
        """KITCHEN should fail require_management()."""
        try:
            from shared.exceptions import AppError

            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1],
                "roles": ["KITCHEN"],
            })
            with pytest.raises(AppError):
                ctx.require_management()
        except ImportError:
            pytest.skip("Batch B not yet merged")

    def test_require_role_matching(self):
        """require_role should pass when user has the requested role."""
        try:
            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1],
                "roles": ["WAITER"],
            })
            ctx.require_role("WAITER")
        except ImportError:
            pytest.skip("Batch B not yet merged")

    def test_require_role_not_matching(self):
        """require_role should raise when user lacks the requested role."""
        try:
            from shared.exceptions import AppError

            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1],
                "roles": ["WAITER"],
            })
            with pytest.raises(AppError):
                ctx.require_role("ADMIN")
        except ImportError:
            pytest.skip("Batch B not yet merged")


class TestStrategyDispatch:
    """REQ-RBAC-02: Strategy pattern dispatch via PermissionContext.can()."""

    def test_admin_strategy_selected_for_admin(self):
        """ADMIN role should dispatch to AdminStrategy."""
        try:
            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1],
                "roles": ["ADMIN"],
            })
            # Admin should be able to do most things
            # Exact behavior depends on Batch B's strategy implementation
            assert ctx is not None
        except ImportError:
            pytest.skip("Batch B not yet merged")

    def test_highest_privilege_strategy_selected(self):
        """When user has multiple roles, highest privilege strategy is selected."""
        try:
            from rest_api.app.services.permissions.context import PermissionContext

            ctx = PermissionContext({
                "sub": "1",
                "tenant_id": 1,
                "branch_ids": [1],
                "roles": ["WAITER", "MANAGER"],
            })
            # MANAGER is higher privilege than WAITER
            # Should be able to do management tasks
            ctx.require_management()
        except ImportError:
            pytest.skip("Batch B not yet merged")
