"""Initial migration — create all tables.

Revision ID: 001
Revises: None
Create Date: 2026-03-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension BEFORE any table creation
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── 1. tenants (no FK) ──────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        # AuditMixin columns
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )

    # ── 2. branches (FK → tenants) ──────────────────────────────────────
    op.create_table(
        "branches",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, index=True),
        sa.Column("address", sa.String(300), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="America/Argentina/Buenos_Aires"),
        sa.Column("is_open", sa.Boolean, nullable=False, server_default=sa.text("false")),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_branches_tenant_slug"),
    )

    # ── 3. users (FK → tenants) ─────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_superadmin", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )

    # ── 4. user_branch_roles (FK → users, branches) ─────────────────────
    op.create_table(
        "user_branch_roles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False, index=True),
        sa.Column("role", sa.String(50), nullable=False),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("user_id", "branch_id", "role", name="uq_user_branch_roles_user_branch_role"),
    )

    # ── 5. allergens (no FK, global table) ───────────────────────────────
    op.create_table(
        "allergens",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )

    # ── 6. cooking_methods (FK → tenants) ────────────────────────────────
    op.create_table(
        "cooking_methods",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_cooking_methods_tenant_name"),
    )

    # ── 6b. flavor_profiles (FK → tenants) ───────────────────────────────
    op.create_table(
        "flavor_profiles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_flavor_profiles_tenant_name"),
    )

    # ── 6c. texture_profiles (FK → tenants) ──────────────────────────────
    op.create_table(
        "texture_profiles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_texture_profiles_tenant_name"),
    )

    # ── 6d. cuisine_types (FK → tenants) ─────────────────────────────────
    op.create_table(
        "cuisine_types",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_cuisine_types_tenant_name"),
    )

    # ── 7. categories (FK → tenants) ─────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_categories_tenant_slug"),
    )

    # ── 8. subcategories (FK → categories) ───────────────────────────────
    op.create_table(
        "subcategories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("category_id", "slug", name="uq_subcategories_category_slug"),
    )

    # ── 9. products (FK → tenants, subcategories, profiles) ──────────────
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("subcategory_id", sa.Integer, sa.ForeignKey("subcategories.id"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("base_price_cents", sa.Integer, nullable=False),
        sa.Column("prep_time_minutes", sa.Integer, nullable=True),
        sa.Column("is_available", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("is_visible_in_menu", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("cooking_method_id", sa.Integer, sa.ForeignKey("cooking_methods.id"), nullable=True),
        sa.Column("flavor_profile_id", sa.Integer, sa.ForeignKey("flavor_profiles.id"), nullable=True),
        sa.Column("texture_profile_id", sa.Integer, sa.ForeignKey("texture_profiles.id"), nullable=True),
        sa.Column("cuisine_type_id", sa.Integer, sa.ForeignKey("cuisine_types.id"), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_products_tenant_slug"),
        sa.CheckConstraint("base_price_cents >= 0", name="ck_products_price_positive"),
    )

    # ── 10. branch_products (FK → branches, products) ────────────────────
    op.create_table(
        "branch_products",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False, index=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False, index=True),
        sa.Column("price_override_cents", sa.Integer, nullable=True),
        sa.Column("is_available", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("stock_quantity", sa.Integer, nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("branch_id", "product_id", name="uq_branch_products_branch_product"),
        sa.CheckConstraint(
            "price_override_cents >= 0 OR price_override_cents IS NULL",
            name="ck_branch_products_override_positive",
        ),
    )

    # ── 11. product_allergens (FK → products, allergens) ─────────────────
    op.create_table(
        "product_allergens",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False, index=True),
        sa.Column("allergen_id", sa.Integer, sa.ForeignKey("allergens.id"), nullable=False, index=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="contains"),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("product_id", "allergen_id", name="uq_product_allergens_product_allergen"),
    )

    # ── 12. ingredient_groups (FK → tenants) ─────────────────────────────
    op.create_table(
        "ingredient_groups",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_ingredient_groups_tenant_name"),
    )

    # ── 13. ingredients (FK → tenants, ingredient_groups) ────────────────
    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("ingredient_groups.id"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("cost_per_unit_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("stock_quantity", sa.Numeric(10, 3), nullable=True),
        sa.Column("min_stock_threshold", sa.Numeric(10, 3), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_ingredients_tenant_name"),
        sa.CheckConstraint("cost_per_unit_cents >= 0", name="ck_ingredients_cost_positive"),
    )

    # ── 14. sub_ingredients (FK → ingredients x2) ────────────────────────
    op.create_table(
        "sub_ingredients",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("parent_ingredient_id", sa.Integer, sa.ForeignKey("ingredients.id"), nullable=False, index=True),
        sa.Column("child_ingredient_id", sa.Integer, sa.ForeignKey("ingredients.id"), nullable=False, index=True),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint(
            "parent_ingredient_id", "child_ingredient_id", name="uq_sub_ingredients_parent_child"
        ),
    )

    # ── 15. sectors (FK → branches) ──────────────────────────────────────
    op.create_table(
        "sectors",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("branch_id", "name", name="uq_sectors_branch_name"),
    )

    # ── 16. tables (FK → sectors) ────────────────────────────────────────
    op.create_table(
        "tables",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("sector_id", sa.Integer, sa.ForeignKey("sectors.id"), nullable=False, index=True),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("capacity", sa.Integer, nullable=False, server_default="4"),
        sa.Column("status", sa.String(20), nullable=False, server_default="available"),
        sa.Column("pos_x", sa.Float, nullable=True),
        sa.Column("pos_y", sa.Float, nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("sector_id", "number", name="uq_tables_sector_number"),
    )

    # ── 17. table_sessions (FK → tables, users x2) ──────────────────────
    op.create_table(
        "table_sessions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("table_id", sa.Integer, sa.ForeignKey("tables.id"), nullable=False, index=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("closed_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("guest_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_table_sessions_table_status", "table_sessions", ["table_id", "status"])

    # ── 18. diners (FK → table_sessions, users) ─────────────────────────
    op.create_table(
        "diners",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("table_sessions.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("seat_number", sa.Integer, nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )
    # Partial unique: only enforce uniqueness when seat_number is not null
    op.create_index(
        "uq_diners_session_seat",
        "diners",
        ["session_id", "seat_number"],
        unique=True,
        postgresql_where=sa.text("seat_number IS NOT NULL"),
    )

    # ── 19. rounds (FK → table_sessions) ─────────────────────────────────
    op.create_table(
        "rounds",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("table_sessions.id"), nullable=False, index=True),
        sa.Column("round_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("session_id", "round_number", name="uq_rounds_session_number"),
    )

    # ── 20. round_items (FK → rounds, products, diners) ─────────────────
    op.create_table(
        "round_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("round_id", sa.Integer, sa.ForeignKey("rounds.id"), nullable=False, index=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False, index=True),
        sa.Column("diner_id", sa.Integer, sa.ForeignKey("diners.id"), nullable=True),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("unit_price_cents", sa.Integer, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("quantity > 0", name="ck_round_items_quantity_positive"),
        sa.CheckConstraint("unit_price_cents >= 0", name="ck_round_items_unit_price_positive"),
    )
    op.create_index("ix_round_items_status", "round_items", ["status"])

    # ── 21. kitchen_tickets (FK → round_items, users) ────────────────────
    op.create_table(
        "kitchen_tickets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("round_item_id", sa.Integer, sa.ForeignKey("round_items.id"), nullable=False, index=True),
        sa.Column("station", sa.String(50), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_to", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_kitchen_tickets_station_status", "kitchen_tickets", ["station", "status"])

    # ── 22. checks (FK → table_sessions, users) ─────────────────────────
    op.create_table(
        "checks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("table_sessions.id"), nullable=False, unique=True),
        sa.Column("subtotal_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tax_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("discount_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tip_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("subtotal_cents >= 0", name="ck_checks_subtotal_positive"),
    )

    # ── 23. charges (FK → checks, round_items) ──────────────────────────
    op.create_table(
        "charges",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("check_id", sa.Integer, sa.ForeignKey("checks.id"), nullable=False, index=True),
        sa.Column("round_item_id", sa.Integer, sa.ForeignKey("round_items.id"), nullable=False, index=True),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("amount_cents >= 0", name="ck_charges_amount_positive"),
    )

    # ── 24. allocations (FK → charges, diners) ──────────────────────────
    op.create_table(
        "allocations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("charge_id", sa.Integer, sa.ForeignKey("charges.id"), nullable=False, index=True),
        sa.Column("diner_id", sa.Integer, sa.ForeignKey("diners.id"), nullable=False, index=True),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("split_type", sa.String(20), nullable=False, server_default="equal"),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("charge_id", "diner_id", name="uq_allocations_charge_diner"),
    )

    # ── 25. payments (FK → checks, diners) ───────────────────────────────
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("check_id", sa.Integer, sa.ForeignKey("checks.id"), nullable=False, index=True),
        sa.Column("diner_id", sa.Integer, sa.ForeignKey("diners.id"), nullable=True),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("external_id", sa.String(200), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("amount_cents > 0", name="ck_payments_amount_positive"),
    )

    # ── 26. service_calls (FK → tables, table_sessions, users) ──────────
    op.create_table(
        "service_calls",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("table_id", sa.Integer, sa.ForeignKey("tables.id"), nullable=False, index=True),
        sa.Column("session_id", sa.Integer, sa.ForeignKey("table_sessions.id"), nullable=False, index=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("called_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_service_calls_table_status", "service_calls", ["table_id", "status"])

    # ── 27. waiter_sector_assignments (FK → users, branches, sectors) ────
    op.create_table(
        "waiter_sector_assignments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False, index=True),
        sa.Column("sector_id", sa.Integer, sa.ForeignKey("sectors.id"), nullable=False, index=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )
    # Partial unique: active assignments only
    op.create_index(
        "uq_waiter_sector_active",
        "waiter_sector_assignments",
        ["user_id", "sector_id"],
        unique=True,
        postgresql_where=sa.text("unassigned_at IS NULL"),
    )

    # ── 28. promotions (FK → tenants) ────────────────────────────────────
    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Integer, nullable=False),
        sa.Column("min_order_cents", sa.Integer, nullable=True),
        sa.Column("max_discount_cents", sa.Integer, nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("discount_value > 0", name="ck_promotions_discount_positive"),
    )

    # ── 29. promotion_products (FK → promotions, products) ───────────────
    op.create_table(
        "promotion_products",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("promotion_id", sa.Integer, sa.ForeignKey("promotions.id"), nullable=False, index=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False, index=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("promotion_id", "product_id", name="uq_promotion_products_promo_product"),
    )

    # ── 30. badges (FK → tenants) ────────────────────────────────────────
    op.create_table(
        "badges",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_badges_tenant_name"),
    )

    # ── 31. seals (FK → tenants) ─────────────────────────────────────────
    op.create_table(
        "seals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_seals_tenant_name"),
    )

    # ── 32. recipes (FK → products) ──────────────────────────────────────
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False, unique=True),
        sa.Column("yield_quantity", sa.Numeric(10, 3), nullable=False, server_default="1"),
        sa.Column("yield_unit", sa.String(50), nullable=False, server_default="porcion"),
        sa.Column("total_cost_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text, nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )

    # ── 33. recipe_ingredients (FK → recipes, ingredients) ───────────────
    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("recipe_id", sa.Integer, sa.ForeignKey("recipes.id"), nullable=False, index=True),
        sa.Column("ingredient_id", sa.Integer, sa.ForeignKey("ingredients.id"), nullable=False, index=True),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("recipe_id", "ingredient_id", name="uq_recipe_ingredients_recipe_ingredient"),
    )

    # ── 34. recipe_steps (FK → recipes) ──────────────────────────────────
    op.create_table(
        "recipe_steps",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("recipe_id", sa.Integer, sa.ForeignKey("recipes.id"), nullable=False, index=True),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("instruction", sa.Text, nullable=False),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("deleted_by", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("recipe_id", "step_number", name="uq_recipe_steps_recipe_step"),
    )


def downgrade() -> None:
    # Drop tables in reverse FK dependency order
    op.drop_table("recipe_steps")
    op.drop_table("recipe_ingredients")
    op.drop_table("recipes")
    op.drop_table("seals")
    op.drop_table("badges")
    op.drop_table("promotion_products")
    op.drop_table("promotions")
    op.drop_index("uq_waiter_sector_active", table_name="waiter_sector_assignments")
    op.drop_table("waiter_sector_assignments")
    op.drop_index("ix_service_calls_table_status", table_name="service_calls")
    op.drop_table("service_calls")
    op.drop_table("payments")
    op.drop_table("allocations")
    op.drop_table("charges")
    op.drop_table("checks")
    op.drop_index("ix_kitchen_tickets_station_status", table_name="kitchen_tickets")
    op.drop_table("kitchen_tickets")
    op.drop_index("ix_round_items_status", table_name="round_items")
    op.drop_table("round_items")
    op.drop_table("rounds")
    op.drop_index("uq_diners_session_seat", table_name="diners")
    op.drop_table("diners")
    op.drop_index("ix_table_sessions_table_status", table_name="table_sessions")
    op.drop_table("table_sessions")
    op.drop_table("tables")
    op.drop_table("sectors")
    op.drop_table("sub_ingredients")
    op.drop_table("ingredients")
    op.drop_table("ingredient_groups")
    op.drop_table("product_allergens")
    op.drop_table("branch_products")
    op.drop_table("products")
    op.drop_table("subcategories")
    op.drop_table("categories")
    op.drop_table("cuisine_types")
    op.drop_table("texture_profiles")
    op.drop_table("flavor_profiles")
    op.drop_table("cooking_methods")
    op.drop_table("allergens")
    op.drop_table("user_branch_roles")
    op.drop_table("users")
    op.drop_table("branches")
    op.drop_table("tenants")

    op.execute("DROP EXTENSION IF EXISTS vector")
