"""Phase 5 — Table & Staff Domain: unit tests for enums, FSM, roles, and RBAC.

Tests are grouped into sections:
1. Enum shape tests   (no DB, no async)
2. Table FSM tests    (no DB, no async — pure dict validation)
3. Roles service      (no DB, no async)
4. Role assignment    (no DB, no async — StaffService._validate_role_assignment)
5. RBAC strategies    (no DB, no async — strategy.can())
"""

import pytest

from shared.enums import (
    SECTOR_PREFIX_MAP,
    TABLE_TRANSITIONS,
    TABLE_URGENCY_SCORE,
    SectorType,
    TableStatus,
)
from shared.exceptions import ForbiddenError
from rest_api.app.services.domain.roles_service import RolesService
from rest_api.app.services.domain.staff_service import StaffService
from rest_api.app.services.permissions.strategies import (
    Action,
    AdminStrategy,
    ManagerStrategy,
    ReadOnlyStrategy,
    WaiterStrategy,
)


# ---------------------------------------------------------------------------
# 1. Enum Tests
# ---------------------------------------------------------------------------


class TestTableTransitions:
    """TABLE_TRANSITIONS must be the single source of truth for the FSM."""

    def test_has_exactly_six_statuses(self):
        assert set(TABLE_TRANSITIONS.keys()) == {
            TableStatus.LIBRE,
            TableStatus.OCUPADA,
            TableStatus.PEDIDO_SOLICITADO,
            TableStatus.PEDIDO_CUMPLIDO,
            TableStatus.CUENTA,
            TableStatus.INACTIVA,
        }

    def test_libre_transitions(self):
        assert set(TABLE_TRANSITIONS[TableStatus.LIBRE]) == {
            TableStatus.OCUPADA,
            TableStatus.INACTIVA,
        }

    def test_ocupada_transitions(self):
        assert set(TABLE_TRANSITIONS[TableStatus.OCUPADA]) == {
            TableStatus.PEDIDO_SOLICITADO,
            TableStatus.LIBRE,
        }

    def test_pedido_solicitado_transitions(self):
        assert set(TABLE_TRANSITIONS[TableStatus.PEDIDO_SOLICITADO]) == {
            TableStatus.PEDIDO_CUMPLIDO,
        }

    def test_pedido_cumplido_transitions(self):
        assert set(TABLE_TRANSITIONS[TableStatus.PEDIDO_CUMPLIDO]) == {
            TableStatus.CUENTA,
            TableStatus.PEDIDO_SOLICITADO,
        }

    def test_cuenta_transitions(self):
        assert set(TABLE_TRANSITIONS[TableStatus.CUENTA]) == {
            TableStatus.LIBRE,
        }

    def test_inactiva_transitions(self):
        assert set(TABLE_TRANSITIONS[TableStatus.INACTIVA]) == {
            TableStatus.LIBRE,
        }


class TestTableUrgencyScore:
    """TABLE_URGENCY_SCORE must cover all 6 statuses with correct values."""

    def test_covers_all_six_statuses(self):
        assert set(TABLE_URGENCY_SCORE.keys()) == {
            TableStatus.CUENTA,
            TableStatus.PEDIDO_SOLICITADO,
            TableStatus.PEDIDO_CUMPLIDO,
            TableStatus.OCUPADA,
            TableStatus.LIBRE,
            TableStatus.INACTIVA,
        }

    def test_cuenta_is_highest_urgency(self):
        assert TABLE_URGENCY_SCORE[TableStatus.CUENTA] == 50

    def test_pedido_solicitado_urgency(self):
        assert TABLE_URGENCY_SCORE[TableStatus.PEDIDO_SOLICITADO] == 40

    def test_pedido_cumplido_urgency(self):
        assert TABLE_URGENCY_SCORE[TableStatus.PEDIDO_CUMPLIDO] == 30

    def test_ocupada_urgency(self):
        assert TABLE_URGENCY_SCORE[TableStatus.OCUPADA] == 20

    def test_libre_urgency(self):
        assert TABLE_URGENCY_SCORE[TableStatus.LIBRE] == 10

    def test_inactiva_is_lowest_urgency(self):
        assert TABLE_URGENCY_SCORE[TableStatus.INACTIVA] == 0

    def test_urgency_ordering_is_correct(self):
        """Statuses with more work pending must score higher."""
        assert (
            TABLE_URGENCY_SCORE[TableStatus.CUENTA]
            > TABLE_URGENCY_SCORE[TableStatus.PEDIDO_SOLICITADO]
            > TABLE_URGENCY_SCORE[TableStatus.PEDIDO_CUMPLIDO]
            > TABLE_URGENCY_SCORE[TableStatus.OCUPADA]
            > TABLE_URGENCY_SCORE[TableStatus.LIBRE]
            > TABLE_URGENCY_SCORE[TableStatus.INACTIVA]
        )


class TestSectorPrefixMap:
    """SECTOR_PREFIX_MAP must cover all 4 sector types."""

    def test_covers_all_four_sector_types(self):
        assert set(SECTOR_PREFIX_MAP.keys()) == {
            SectorType.INTERIOR,
            SectorType.TERRAZA,
            SectorType.BARRA,
            SectorType.VIP,
        }

    def test_interior_prefix(self):
        assert SECTOR_PREFIX_MAP[SectorType.INTERIOR] == "INT"

    def test_terraza_prefix(self):
        assert SECTOR_PREFIX_MAP[SectorType.TERRAZA] == "TER"

    def test_barra_prefix(self):
        assert SECTOR_PREFIX_MAP[SectorType.BARRA] == "BAR"

    def test_vip_prefix(self):
        assert SECTOR_PREFIX_MAP[SectorType.VIP] == "VIP"


# ---------------------------------------------------------------------------
# 2. Table FSM Tests (pure dict validation — no DB required)
# ---------------------------------------------------------------------------


class TestFSMValidTransitions:
    """Happy-path FSM transitions that must exist in TABLE_TRANSITIONS."""

    def _assert_valid(self, from_status: str, to_status: str) -> None:
        assert to_status in TABLE_TRANSITIONS.get(from_status, []), (
            f"Expected {from_status} -> {to_status} to be valid"
        )

    def test_libre_to_ocupada(self):
        self._assert_valid(TableStatus.LIBRE, TableStatus.OCUPADA)

    def test_ocupada_to_pedido_solicitado(self):
        self._assert_valid(TableStatus.OCUPADA, TableStatus.PEDIDO_SOLICITADO)

    def test_pedido_solicitado_to_pedido_cumplido(self):
        self._assert_valid(TableStatus.PEDIDO_SOLICITADO, TableStatus.PEDIDO_CUMPLIDO)

    def test_pedido_cumplido_to_cuenta(self):
        self._assert_valid(TableStatus.PEDIDO_CUMPLIDO, TableStatus.CUENTA)

    def test_cuenta_to_libre(self):
        self._assert_valid(TableStatus.CUENTA, TableStatus.LIBRE)

    def test_libre_to_inactiva(self):
        self._assert_valid(TableStatus.LIBRE, TableStatus.INACTIVA)

    def test_inactiva_to_libre(self):
        self._assert_valid(TableStatus.INACTIVA, TableStatus.LIBRE)

    def test_ocupada_to_libre_cancel(self):
        """Guests can leave without ordering — ocupada -> libre is a cancellation."""
        self._assert_valid(TableStatus.OCUPADA, TableStatus.LIBRE)

    def test_pedido_cumplido_to_pedido_solicitado_reorder(self):
        """A second round — pedido_cumplido -> pedido_solicitado is a reorder."""
        self._assert_valid(TableStatus.PEDIDO_CUMPLIDO, TableStatus.PEDIDO_SOLICITADO)


class TestFSMInvalidTransitions:
    """Transitions that must NOT exist in TABLE_TRANSITIONS."""

    def _assert_invalid(self, from_status: str, to_status: str) -> None:
        assert to_status not in TABLE_TRANSITIONS.get(from_status, []), (
            f"Expected {from_status} -> {to_status} to be INVALID"
        )

    def test_libre_cannot_go_to_cuenta(self):
        self._assert_invalid(TableStatus.LIBRE, TableStatus.CUENTA)

    def test_libre_cannot_go_to_pedido_solicitado(self):
        self._assert_invalid(TableStatus.LIBRE, TableStatus.PEDIDO_SOLICITADO)

    def test_libre_cannot_go_to_pedido_cumplido(self):
        self._assert_invalid(TableStatus.LIBRE, TableStatus.PEDIDO_CUMPLIDO)

    def test_ocupada_cannot_go_to_cuenta(self):
        self._assert_invalid(TableStatus.OCUPADA, TableStatus.CUENTA)

    def test_ocupada_cannot_go_to_pedido_cumplido(self):
        self._assert_invalid(TableStatus.OCUPADA, TableStatus.PEDIDO_CUMPLIDO)

    def test_pedido_solicitado_cannot_go_to_libre(self):
        self._assert_invalid(TableStatus.PEDIDO_SOLICITADO, TableStatus.LIBRE)

    def test_pedido_solicitado_cannot_go_to_cuenta(self):
        self._assert_invalid(TableStatus.PEDIDO_SOLICITADO, TableStatus.CUENTA)

    def test_pedido_solicitado_cannot_go_to_inactiva(self):
        self._assert_invalid(TableStatus.PEDIDO_SOLICITADO, TableStatus.INACTIVA)

    def test_cuenta_cannot_go_to_ocupada(self):
        self._assert_invalid(TableStatus.CUENTA, TableStatus.OCUPADA)

    def test_cuenta_cannot_go_to_inactiva(self):
        self._assert_invalid(TableStatus.CUENTA, TableStatus.INACTIVA)

    def test_inactiva_cannot_go_to_ocupada(self):
        self._assert_invalid(TableStatus.INACTIVA, TableStatus.OCUPADA)

    def test_inactiva_cannot_go_to_pedido_solicitado(self):
        self._assert_invalid(TableStatus.INACTIVA, TableStatus.PEDIDO_SOLICITADO)

    def test_inactiva_cannot_go_to_cuenta(self):
        self._assert_invalid(TableStatus.INACTIVA, TableStatus.CUENTA)

    def test_inactiva_cannot_self_loop(self):
        self._assert_invalid(TableStatus.INACTIVA, TableStatus.INACTIVA)

    def test_pedido_cumplido_cannot_go_to_libre_directly(self):
        """Session close goes through cuenta, not directly to libre."""
        self._assert_invalid(TableStatus.PEDIDO_CUMPLIDO, TableStatus.LIBRE)


class TestFSMIsSingleSourceOfTruth:
    """Transitions dict is the contract — no magic booleans elsewhere."""

    def test_all_states_have_a_transitions_entry(self):
        """Every TableStatus must appear as a key (even terminal ones)."""
        all_statuses = {s.value for s in TableStatus}
        transition_keys = {k for k in TABLE_TRANSITIONS}
        assert all_statuses == transition_keys

    def test_all_transition_targets_are_valid_statuses(self):
        """Targets must be valid TableStatus values — no typos."""
        all_statuses = {s.value for s in TableStatus}
        for from_status, targets in TABLE_TRANSITIONS.items():
            for target in targets:
                assert target in all_statuses, (
                    f"Transition target '{target}' is not a valid TableStatus"
                )


# ---------------------------------------------------------------------------
# 3. Roles Service Tests
# ---------------------------------------------------------------------------


class TestRolesService:
    """RolesService.get_permissions_matrix() must expose the full RBAC matrix."""

    def setup_method(self):
        self.service = RolesService()

    def test_returns_all_five_roles(self):
        matrix = self.service.get_permissions_matrix()
        roles = [entry["rol"] for entry in matrix]
        assert set(roles) == {"ADMIN", "MANAGER", "WAITER", "KITCHEN", "READONLY"}

    def test_admin_has_wildcard_permission(self):
        matrix = self.service.get_permissions_matrix()
        admin = next(e for e in matrix if e["rol"] == "ADMIN")
        assert admin["permisos"] == ["*"]

    def test_each_role_has_spanish_label(self):
        matrix = self.service.get_permissions_matrix()
        for entry in matrix:
            assert "etiqueta" in entry, f"Role {entry['rol']} missing 'etiqueta'"
            assert isinstance(entry["etiqueta"], str)
            assert len(entry["etiqueta"]) > 0

    def test_admin_label(self):
        entry = self.service.get_role_permissions("ADMIN")
        assert entry is not None
        assert entry["etiqueta"] == "Administrador"

    def test_manager_label(self):
        entry = self.service.get_role_permissions("MANAGER")
        assert entry is not None
        assert entry["etiqueta"] == "Gerente"

    def test_waiter_label(self):
        entry = self.service.get_role_permissions("WAITER")
        assert entry is not None
        assert entry["etiqueta"] == "Mozo"

    def test_kitchen_label(self):
        entry = self.service.get_role_permissions("KITCHEN")
        assert entry is not None
        assert entry["etiqueta"] == "Cocina"

    def test_readonly_label(self):
        entry = self.service.get_role_permissions("READONLY")
        assert entry is not None
        assert entry["etiqueta"] == "Solo Lectura"

    def test_unknown_role_returns_none(self):
        assert self.service.get_role_permissions("SUPERUSER") is None

    def test_get_available_roles_returns_five_roles(self):
        roles = self.service.get_available_roles()
        assert set(roles) == {"ADMIN", "MANAGER", "WAITER", "KITCHEN", "READONLY"}


# ---------------------------------------------------------------------------
# 4. Role Assignment Validation Tests
# ---------------------------------------------------------------------------


class TestRoleAssignmentValidation:
    """StaffService._validate_role_assignment enforces the RBAC assignment rules."""

    # -- ADMIN assigner --

    def test_admin_can_assign_admin(self):
        # Must not raise
        StaffService._validate_role_assignment(["ADMIN"], "ADMIN")

    def test_admin_can_assign_manager(self):
        StaffService._validate_role_assignment(["ADMIN"], "MANAGER")

    def test_admin_can_assign_waiter(self):
        StaffService._validate_role_assignment(["ADMIN"], "WAITER")

    def test_admin_can_assign_kitchen(self):
        StaffService._validate_role_assignment(["ADMIN"], "KITCHEN")

    def test_admin_can_assign_readonly(self):
        StaffService._validate_role_assignment(["ADMIN"], "READONLY")

    # -- MANAGER assigner --

    def test_manager_can_assign_manager(self):
        StaffService._validate_role_assignment(["MANAGER"], "MANAGER")

    def test_manager_can_assign_waiter(self):
        StaffService._validate_role_assignment(["MANAGER"], "WAITER")

    def test_manager_can_assign_kitchen(self):
        StaffService._validate_role_assignment(["MANAGER"], "KITCHEN")

    def test_manager_can_assign_readonly(self):
        StaffService._validate_role_assignment(["MANAGER"], "READONLY")

    def test_manager_cannot_assign_admin(self):
        with pytest.raises(ForbiddenError):
            StaffService._validate_role_assignment(["MANAGER"], "ADMIN")

    # -- Low-privilege assigners --

    def test_waiter_cannot_assign_any_role(self):
        with pytest.raises(ForbiddenError):
            StaffService._validate_role_assignment(["WAITER"], "READONLY")

    def test_kitchen_cannot_assign_any_role(self):
        with pytest.raises(ForbiddenError):
            StaffService._validate_role_assignment(["KITCHEN"], "WAITER")

    def test_readonly_cannot_assign_any_role(self):
        with pytest.raises(ForbiddenError):
            StaffService._validate_role_assignment(["READONLY"], "READONLY")

    def test_empty_roles_cannot_assign(self):
        with pytest.raises(ForbiddenError):
            StaffService._validate_role_assignment([], "WAITER")

    def test_no_roles_cannot_assign(self):
        """Even with valid target, empty assigner list must be forbidden."""
        with pytest.raises(ForbiddenError):
            StaffService._validate_role_assignment([], "READONLY")


# ---------------------------------------------------------------------------
# 5. RBAC Strategy Tests
# ---------------------------------------------------------------------------


class TestAdminStrategy:
    """AdminStrategy.can() must return True for every action/resource combo."""

    def setup_method(self):
        self.strategy = AdminStrategy()

    def test_can_create_anything(self):
        assert self.strategy.can(Action.CREATE, "Order") is True
        assert self.strategy.can(Action.CREATE, "Staff") is True
        assert self.strategy.can(Action.CREATE, "Tenant") is True

    def test_can_read_anything(self):
        assert self.strategy.can(Action.READ, "AuditLog") is True

    def test_can_edit_anything(self):
        assert self.strategy.can(Action.EDIT, "User") is True

    def test_can_delete_anything(self):
        assert self.strategy.can(Action.DELETE, "Branch") is True

    def test_can_manage_anything(self):
        assert self.strategy.can(Action.MANAGE, "StaffAssignment") is True

    def test_can_do_unknown_resource(self):
        assert self.strategy.can(Action.DELETE, "SomeUnknownResource") is True


class TestManagerStrategy:
    """ManagerStrategy.can() covers sectors, tables, and staff but not superadmin ops."""

    def setup_method(self):
        self.strategy = ManagerStrategy()

    def test_can_manage_sector(self):
        assert self.strategy.can(Action.CREATE, "Sector") is True
        assert self.strategy.can(Action.EDIT, "Sector") is True
        assert self.strategy.can(Action.DELETE, "Sector") is True

    def test_can_manage_table(self):
        assert self.strategy.can(Action.CREATE, "Table") is True
        assert self.strategy.can(Action.EDIT, "Table") is True
        assert self.strategy.can(Action.DELETE, "Table") is True

    def test_can_manage_staff(self):
        assert self.strategy.can(Action.CREATE, "Staff") is True
        assert self.strategy.can(Action.EDIT, "Staff") is True
        assert self.strategy.can(Action.DELETE, "Staff") is True

    def test_can_read_product(self):
        assert self.strategy.can(Action.READ, "Product") is True

    def test_cannot_delete_product(self):
        assert self.strategy.can(Action.DELETE, "Product") is False

    def test_cannot_create_user(self):
        assert self.strategy.can(Action.CREATE, "User") is False

    def test_cannot_access_unknown_resource(self):
        assert self.strategy.can(Action.READ, "SomethingObscure") is False


class TestWaiterStrategy:
    """WaiterStrategy.can() — read + status transitions on tables, order management."""

    def setup_method(self):
        self.strategy = WaiterStrategy()

    def test_can_read_table(self):
        assert self.strategy.can(Action.READ, "Table") is True

    def test_can_edit_table(self):
        """Status transitions are EDIT actions on Table."""
        assert self.strategy.can(Action.EDIT, "Table") is True

    def test_cannot_create_table(self):
        assert self.strategy.can(Action.CREATE, "Table") is False

    def test_cannot_delete_table(self):
        assert self.strategy.can(Action.DELETE, "Table") is False

    def test_can_read_order(self):
        assert self.strategy.can(Action.READ, "Order") is True

    def test_can_create_order(self):
        assert self.strategy.can(Action.CREATE, "Order") is True

    def test_can_edit_order(self):
        assert self.strategy.can(Action.EDIT, "Order") is True

    def test_cannot_delete_order(self):
        assert self.strategy.can(Action.DELETE, "Order") is False

    def test_can_read_sector(self):
        assert self.strategy.can(Action.READ, "Sector") is True

    def test_cannot_edit_sector(self):
        assert self.strategy.can(Action.EDIT, "Sector") is False

    def test_cannot_manage_staff(self):
        assert self.strategy.can(Action.READ, "Staff") is False
        assert self.strategy.can(Action.CREATE, "Staff") is False


class TestReadOnlyStrategy:
    """ReadOnlyStrategy.can() — READ only on an explicit allowlist."""

    def setup_method(self):
        self.strategy = ReadOnlyStrategy()

    def test_can_read_staff(self):
        assert self.strategy.can(Action.READ, "Staff") is True

    def test_cannot_create_staff(self):
        assert self.strategy.can(Action.CREATE, "Staff") is False

    def test_cannot_edit_staff(self):
        assert self.strategy.can(Action.EDIT, "Staff") is False

    def test_cannot_delete_staff(self):
        assert self.strategy.can(Action.DELETE, "Staff") is False

    def test_can_read_table(self):
        assert self.strategy.can(Action.READ, "Table") is True

    def test_cannot_edit_table(self):
        assert self.strategy.can(Action.EDIT, "Table") is False

    def test_can_read_order(self):
        assert self.strategy.can(Action.READ, "Order") is True

    def test_cannot_create_order(self):
        assert self.strategy.can(Action.CREATE, "Order") is False

    def test_can_read_audit_log(self):
        assert self.strategy.can(Action.READ, "AuditLog") is True

    def test_cannot_access_unknown_resource(self):
        assert self.strategy.can(Action.READ, "UnknownResource") is False
        assert self.strategy.can(Action.CREATE, "UnknownResource") is False
