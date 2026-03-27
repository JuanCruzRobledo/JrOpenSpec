"""Add missing columns to tenants, branches, categories, and products.

These columns were defined in the API spec (dashboard-shell) but never
added to the DB models. Services used getattr/hasattr hacks as workaround.

Revision ID: 003
Revises: 002
Create Date: 2026-03-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Tenants: add description, banner_url, phone, email, address ──
    op.add_column("tenants", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("tenants", sa.Column("banner_url", sa.String(500), nullable=True))
    op.add_column("tenants", sa.Column("phone", sa.String(50), nullable=True))
    op.add_column("tenants", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("tenants", sa.Column("address", sa.String(300), nullable=True))

    # ── Branches: add email, image_url, opening_time, closing_time, display_order ──
    op.add_column("branches", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("branches", sa.Column("image_url", sa.String(500), nullable=True))
    op.add_column(
        "branches",
        sa.Column("opening_time", sa.String(5), nullable=False, server_default="09:00"),
    )
    op.add_column(
        "branches",
        sa.Column("closing_time", sa.String(5), nullable=False, server_default="23:00"),
    )
    op.add_column(
        "branches",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── Categories: add branch_id (FK), icon, is_home ──
    op.add_column(
        "categories",
        sa.Column("branch_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_categories_branch_id",
        "categories",
        "branches",
        ["branch_id"],
        ["id"],
    )
    op.create_index("ix_categories_branch_id", "categories", ["branch_id"])
    op.add_column("categories", sa.Column("icon", sa.String(50), nullable=True))
    op.add_column(
        "categories",
        sa.Column("is_home", sa.Boolean(), nullable=False, server_default="false"),
    )

    # ── Products: add is_featured, is_popular ──
    op.add_column(
        "products",
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "products",
        sa.Column("is_popular", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    # ── Products ──
    op.drop_column("products", "is_popular")
    op.drop_column("products", "is_featured")

    # ── Categories ──
    op.drop_column("categories", "is_home")
    op.drop_column("categories", "icon")
    op.drop_index("ix_categories_branch_id", table_name="categories")
    op.drop_constraint("fk_categories_branch_id", "categories", type_="foreignkey")
    op.drop_column("categories", "branch_id")

    # ── Branches ──
    op.drop_column("branches", "display_order")
    op.drop_column("branches", "closing_time")
    op.drop_column("branches", "opening_time")
    op.drop_column("branches", "image_url")
    op.drop_column("branches", "email")

    # ── Tenants ──
    op.drop_column("tenants", "address")
    op.drop_column("tenants", "email")
    op.drop_column("tenants", "phone")
    op.drop_column("tenants", "banner_url")
    op.drop_column("tenants", "description")
