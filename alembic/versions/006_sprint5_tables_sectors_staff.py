"""Sprint 5 — Table & Staff Domain: sectors, tables, sessions, users, assignments.

Changes:
- Sector: add type, prefix, capacity columns + constraints
- Table: number VARCHAR->INTEGER, status default 'libre', add code/version/timestamps/session_count
- TableSession: add order lifecycle timestamps + duration_minutes + index
- User: add dni, hired_at
- WaiterSectorAssignment: drop old model, create new date+shift model

Revision ID: 006
Revises: 005
Create Date: 2026-03-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. SECTOR: add type, prefix, capacity + constraints
    # ------------------------------------------------------------------
    op.add_column("sectors", sa.Column("type", sa.String(20), nullable=True))
    op.add_column("sectors", sa.Column("prefix", sa.String(10), nullable=True))
    op.add_column("sectors", sa.Column("capacity", sa.Integer(), nullable=True))

    # Populate existing rows: default type='interior', generate prefix from name
    op.execute("UPDATE sectors SET type = 'interior' WHERE type IS NULL")
    op.execute("""
        UPDATE sectors SET prefix = UPPER(LEFT(name, 3))
        WHERE prefix IS NULL
    """)

    # Now make NOT NULL
    op.alter_column("sectors", "type", nullable=False)
    op.alter_column("sectors", "prefix", nullable=False)

    # Constraints
    op.create_unique_constraint("uq_sectors_branch_prefix", "sectors", ["branch_id", "prefix"])
    op.create_check_constraint("ck_sector_capacity_positive", "sectors", "capacity > 0")

    # ------------------------------------------------------------------
    # 2. TABLE: alter number, status, add new columns + constraints
    # ------------------------------------------------------------------

    # Drop old unique constraint first (depends on number column type)
    op.drop_constraint("uq_tables_sector_number", "tables", type_="unique")

    # number: VARCHAR(20) -> INTEGER
    op.alter_column(
        "tables",
        "number",
        type_=sa.Integer(),
        existing_type=sa.String(20),
        postgresql_using="regexp_replace(number, '[^0-9]', '', 'g')::integer",
    )

    # status: change default + widen column
    op.alter_column(
        "tables",
        "status",
        type_=sa.String(25),
        existing_type=sa.String(20),
        server_default="libre",
    )
    # Migrate existing data
    op.execute("UPDATE tables SET status = 'libre' WHERE status = 'available'")

    # New columns
    op.add_column("tables", sa.Column("code", sa.String(15), nullable=True))
    op.add_column("tables", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("tables", sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tables", sa.Column("occupied_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tables", sa.Column("order_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tables", sa.Column("order_fulfilled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tables", sa.Column("check_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tables", sa.Column("session_count", sa.Integer(), nullable=False, server_default="0"))

    # New indexes (partial)
    op.create_index(
        "uq_tables_sector_number_active",
        "tables",
        ["sector_id", "number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_tables_sector_status_active",
        "tables",
        ["sector_id", "status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Check constraints
    op.create_check_constraint("ck_table_capacity_range", "tables", "capacity >= 1 AND capacity <= 20")
    op.create_check_constraint("ck_table_number_positive", "tables", "number > 0")

    # ------------------------------------------------------------------
    # 3. TABLE_SESSION: add order lifecycle timestamps + duration + index
    # ------------------------------------------------------------------
    op.add_column("table_sessions", sa.Column("order_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("table_sessions", sa.Column("order_fulfilled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("table_sessions", sa.Column("check_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("table_sessions", sa.Column("duration_minutes", sa.Integer(), nullable=True))

    op.create_index(
        "ix_table_sessions_table_closed",
        "table_sessions",
        ["table_id", "closed_at"],
    )

    # ------------------------------------------------------------------
    # 4. USER: add dni, hired_at
    # ------------------------------------------------------------------
    op.add_column("users", sa.Column("dni", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("hired_at", sa.Date(), nullable=True))

    # ------------------------------------------------------------------
    # 5. WAITER_SECTOR_ASSIGNMENT: drop old, create new date+shift model
    # ------------------------------------------------------------------

    # Drop old table completely
    op.drop_index("uq_waiter_sector_active", table_name="waiter_sector_assignments")
    op.drop_table("waiter_sector_assignments")

    # Create new table with date+shift design
    op.create_table(
        "waiter_sector_assignments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("branch_id", sa.BigInteger(), nullable=False),
        sa.Column("sector_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("shift", sa.String(15), nullable=False),
        # Audit fields from BaseModel (AuditMixin)
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["sector_id"], ["sectors.id"]),
        sa.UniqueConstraint("user_id", "sector_id", "date", "shift", name="uq_waiter_sector_date_shift"),
    )

    op.create_index("ix_waiter_sector_assignments_user_id", "waiter_sector_assignments", ["user_id"])
    op.create_index("ix_waiter_sector_assignments_branch_id", "waiter_sector_assignments", ["branch_id"])
    op.create_index("ix_waiter_sector_assignments_sector_id", "waiter_sector_assignments", ["sector_id"])
    op.create_index("ix_assignments_date_shift", "waiter_sector_assignments", ["date", "shift"])
    op.create_index("ix_assignments_waiter_date", "waiter_sector_assignments", ["user_id", "date"])


def downgrade() -> None:
    # ------------------------------------------------------------------
    # 5. WAITER_SECTOR_ASSIGNMENT: drop new, restore old
    # ------------------------------------------------------------------
    op.drop_index("ix_assignments_waiter_date", table_name="waiter_sector_assignments")
    op.drop_index("ix_assignments_date_shift", table_name="waiter_sector_assignments")
    op.drop_index("ix_waiter_sector_assignments_sector_id", table_name="waiter_sector_assignments")
    op.drop_index("ix_waiter_sector_assignments_branch_id", table_name="waiter_sector_assignments")
    op.drop_index("ix_waiter_sector_assignments_user_id", table_name="waiter_sector_assignments")
    op.drop_table("waiter_sector_assignments")

    # Recreate old table
    op.create_table(
        "waiter_sector_assignments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("branch_id", sa.BigInteger(), nullable=False),
        sa.Column("sector_id", sa.BigInteger(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
        # Audit fields
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["sector_id"], ["sectors.id"]),
    )
    op.create_index("ix_waiter_sector_assignments_user_id", "waiter_sector_assignments", ["user_id"])
    op.create_index("ix_waiter_sector_assignments_branch_id", "waiter_sector_assignments", ["branch_id"])
    op.create_index("ix_waiter_sector_assignments_sector_id", "waiter_sector_assignments", ["sector_id"])
    op.create_index(
        "uq_waiter_sector_active",
        "waiter_sector_assignments",
        ["user_id", "sector_id"],
        unique=True,
        postgresql_where=sa.text("unassigned_at IS NULL"),
    )

    # ------------------------------------------------------------------
    # 4. USER: drop dni, hired_at
    # ------------------------------------------------------------------
    op.drop_column("users", "hired_at")
    op.drop_column("users", "dni")

    # ------------------------------------------------------------------
    # 3. TABLE_SESSION: drop new columns + index
    # ------------------------------------------------------------------
    op.drop_index("ix_table_sessions_table_closed", table_name="table_sessions")
    op.drop_column("table_sessions", "duration_minutes")
    op.drop_column("table_sessions", "check_requested_at")
    op.drop_column("table_sessions", "order_fulfilled_at")
    op.drop_column("table_sessions", "order_requested_at")

    # ------------------------------------------------------------------
    # 2. TABLE: reverse all changes
    # ------------------------------------------------------------------
    # Drop new check constraints
    op.drop_constraint("ck_table_number_positive", "tables", type_="check")
    op.drop_constraint("ck_table_capacity_range", "tables", type_="check")

    # Drop new indexes
    op.drop_index("ix_tables_sector_status_active", table_name="tables")
    op.drop_index("uq_tables_sector_number_active", table_name="tables")

    # Drop new columns
    op.drop_column("tables", "session_count")
    op.drop_column("tables", "check_requested_at")
    op.drop_column("tables", "order_fulfilled_at")
    op.drop_column("tables", "order_requested_at")
    op.drop_column("tables", "occupied_at")
    op.drop_column("tables", "status_changed_at")
    op.drop_column("tables", "version")
    op.drop_column("tables", "code")

    # Restore status data and column type
    op.execute("UPDATE tables SET status = 'available' WHERE status = 'libre'")
    op.alter_column(
        "tables",
        "status",
        type_=sa.String(20),
        existing_type=sa.String(25),
        server_default="available",
    )

    # number: INTEGER -> VARCHAR(20)
    op.alter_column(
        "tables",
        "number",
        type_=sa.String(20),
        existing_type=sa.Integer(),
        postgresql_using="number::varchar",
    )

    # Restore old unique constraint
    op.create_unique_constraint("uq_tables_sector_number", "tables", ["sector_id", "number"])

    # ------------------------------------------------------------------
    # 1. SECTOR: drop new columns + constraints
    # ------------------------------------------------------------------
    op.drop_constraint("ck_sector_capacity_positive", "sectors", type_="check")
    op.drop_constraint("uq_sectors_branch_prefix", "sectors", type_="unique")
    op.drop_column("sectors", "capacity")
    op.drop_column("sectors", "prefix")
    op.drop_column("sectors", "type")
