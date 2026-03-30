"""Focused integration tests for branch creation access propagation."""

import pytest
from sqlalchemy import select

from shared.models.catalog.category import Category
from shared.models.core.branch import Branch
from shared.models.core.tenant import Tenant
from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
from shared.security.jwt import create_access_token

pytestmark = pytest.mark.integration


async def _build_access_token_for_user(db_session, user: User) -> str:
    roles_result = await db_session.execute(
        select(UserBranchRole).where(
            UserBranchRole.user_id == user.id,
            UserBranchRole.is_active.is_(True),
        )
    )
    branch_roles = roles_result.scalars().all()
    branch_ids = sorted({branch_role.branch_id for branch_role in branch_roles})
    roles = sorted({branch_role.role for branch_role in branch_roles})
    token, _jti = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        branch_ids=branch_ids,
        roles=roles,
    )
    return token


class TestBranchCreationAccess:
    """Branch creation MUST grant creator access for branch-scoped CRUD."""

    async def test_create_branch_assigns_creator_and_requires_token_refresh_for_access(
        self,
        client,
        db_session,
    ):
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        db_session.add(tenant)
        await db_session.flush()

        existing_branch = Branch(
            tenant_id=tenant.id,
            name="Casa Central",
            slug="casa-central",
            opening_time="09:00",
            closing_time="23:00",
            is_open=True,
        )
        db_session.add(existing_branch)
        await db_session.flush()

        admin_user = User(
            tenant_id=tenant.id,
            email="admin@test.com",
            hashed_password="hashed-password",
            first_name="Ada",
            last_name="Admin",
            is_superadmin=False,
        )
        db_session.add(admin_user)
        await db_session.flush()

        db_session.add(
            UserBranchRole(
                user_id=admin_user.id,
                branch_id=existing_branch.id,
                role="ADMIN",
            )
        )
        await db_session.flush()

        stale_access_token = await _build_access_token_for_user(db_session, admin_user)
        auth_headers = {"Authorization": f"Bearer {stale_access_token}"}

        create_response = await client.post(
            "/api/v1/branches",
            json={"nombre": "Sucursal Norte", "direccion": "Av. Norte 123"},
            headers=auth_headers,
        )

        assert create_response.status_code == 201
        created_branch = create_response.json()["data"]
        created_branch_id = created_branch["id"]

        created_role_result = await db_session.execute(
            select(UserBranchRole).where(
                UserBranchRole.user_id == admin_user.id,
                UserBranchRole.branch_id == created_branch_id,
                UserBranchRole.role == "ADMIN",
                UserBranchRole.is_active.is_(True),
            )
        )
        assert created_role_result.scalar_one_or_none() is not None

        general_category_result = await db_session.execute(
            select(Category).where(
                Category.branch_id == created_branch_id,
                Category.name == "General",
                Category.deleted_at.is_(None),
            )
        )
        assert general_category_result.scalar_one_or_none() is not None

        stale_categories_response = await client.get(
            f"/api/v1/branches/{created_branch_id}/categories",
            headers=auth_headers,
        )
        assert stale_categories_response.status_code == 403

        refreshed_access_token = await _build_access_token_for_user(db_session, admin_user)
        refreshed_categories_response = await client.get(
            f"/api/v1/branches/{created_branch_id}/categories",
            headers={"Authorization": f"Bearer {refreshed_access_token}"},
        )

        assert refreshed_categories_response.status_code == 200
        payload = refreshed_categories_response.json()
        assert payload["meta"]["total"] == 1
        assert payload["data"][0]["nombre"] == "General"
