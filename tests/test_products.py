"""Tests for product allergen assignment, free_of validation, branch exclusion,
badge assignment, and custom seal creation.

Covers scenarios S4, S5, S9, S14, S15 from the menu-domain spec.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.catalog.allergen import Allergen
from shared.models.catalog.branch_product import BranchProduct
from shared.models.catalog.product import Product
from shared.models.catalog.product_allergen import ProductAllergen
from shared.models.marketing.badge import Badge
from shared.models.marketing.seal import Seal

from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# S4: Product Allergen Assignment
# ---------------------------------------------------------------------------


async def test_create_product_with_allergen(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_product: Product,
    seed_allergens: list[Allergen],
) -> None:
    """S4 part 1: Assign allergen with presence_type='contains'; verify DB row created."""
    allergen = seed_allergens[0]  # gluten

    response = await client.put(
        f"/api/dashboard/products/{seed_product.id}/allergens",
        json=[
            {
                "allergen_id": allergen.id,
                "presence_type": "contains",
                "risk_level": "severe",
                "notes": None,
            }
        ],
        headers=auth_headers("ADMIN"),
    )

    assert response.status_code == 200

    # Verify the ProductAllergen row exists in DB
    result = await db_session.execute(
        select(ProductAllergen).where(
            ProductAllergen.product_id == seed_product.id,
            ProductAllergen.allergen_id == allergen.id,
        )
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.presence_type == "contains"
    assert row.risk_level == "severe"


async def test_allergen_appears_in_public_menu(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_product: Product,
    seed_allergens: list[Allergen],
    seed_branch,
) -> None:
    """S4 part 2: After assigning allergen with contains, public menu shows it in allergenSummary.contains."""
    allergen = seed_allergens[0]  # gluten

    # Assign allergen via dashboard API
    assign_resp = await client.put(
        f"/api/dashboard/products/{seed_product.id}/allergens",
        json=[
            {
                "allergen_id": allergen.id,
                "presence_type": "contains",
                "risk_level": "severe",
                "notes": None,
            }
        ],
        headers=auth_headers("ADMIN"),
    )
    assert assign_resp.status_code == 200

    # Fetch public menu for branch
    menu_resp = await client.get(f"/api/public/menu/{seed_branch.slug}")
    assert menu_resp.status_code == 200

    menu = menu_resp.json()
    all_products = [
        p
        for cat in menu.get("categories", [])
        for p in cat.get("products", [])
    ]
    product_data = next((p for p in all_products if int(p["id"]) == seed_product.id), None)
    assert product_data is not None, "Product not found in public menu"

    allergen_slugs = product_data.get("allergenSlugs", [])
    assert allergen.code in allergen_slugs, (
        f"Expected {allergen.code} in allergenSlugs, got {allergen_slugs}"
    )


# ---------------------------------------------------------------------------
# S5: Free-Of Validation
# ---------------------------------------------------------------------------


async def test_free_of_high_risk_rejected(
    client: AsyncClient,
    seed_product: Product,
    seed_allergens: list[Allergen],
) -> None:
    """S5: presence_type='free_of' with risk_level != 'low' must be rejected (422)."""
    allergen = seed_allergens[2]  # peanuts

    response = await client.put(
        f"/api/dashboard/products/{seed_product.id}/allergens",
        json=[
            {
                "allergen_id": allergen.id,
                "presence_type": "free_of",
                "risk_level": "severe",  # invalid combination
                "notes": None,
            }
        ],
        headers=auth_headers("ADMIN"),
    )

    assert response.status_code in (400, 422), (
        f"Expected 400 or 422 for free_of+severe, got {response.status_code}"
    )
    body = response.json()
    # Verify there is a meaningful error message (detail may be a list for 422)
    assert body.get("detail") is not None


async def test_free_of_low_risk_accepted(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_product: Product,
    seed_allergens: list[Allergen],
) -> None:
    """S5: presence_type='free_of' with risk_level='low' must succeed (200)."""
    allergen = seed_allergens[2]  # peanuts

    response = await client.put(
        f"/api/dashboard/products/{seed_product.id}/allergens",
        json=[
            {
                "allergen_id": allergen.id,
                "presence_type": "free_of",
                "risk_level": "low",  # valid combination
                "notes": None,
            }
        ],
        headers=auth_headers("ADMIN"),
    )

    assert response.status_code == 200

    # Confirm DB row has the correct values
    result = await db_session.execute(
        select(ProductAllergen).where(
            ProductAllergen.product_id == seed_product.id,
            ProductAllergen.allergen_id == allergen.id,
        )
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.presence_type == "free_of"
    assert row.risk_level == "low"


# ---------------------------------------------------------------------------
# S9: Branch Exclusion
# ---------------------------------------------------------------------------


async def test_inactive_product_excluded_from_menu(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_product: Product,
    seed_branch,
) -> None:
    """S9: Product with BranchProduct.is_active=False must not appear in public menu."""
    # Mark the BranchProduct as inactive
    result = await db_session.execute(
        select(BranchProduct).where(
            BranchProduct.product_id == seed_product.id,
            BranchProduct.branch_id == seed_branch.id,
        )
    )
    bp = result.scalar_one()
    bp.is_active = False
    await db_session.commit()

    # Fetch public menu and confirm the product is absent
    menu_resp = await client.get(f"/api/public/menu/{seed_branch.slug}")
    assert menu_resp.status_code == 200

    menu = menu_resp.json()
    all_product_ids = [
        int(p["id"])
        for cat in menu.get("categories", [])
        for p in cat.get("products", [])
    ]
    assert seed_product.id not in all_product_ids, (
        f"Inactive product {seed_product.id} should not appear in public menu"
    )


# ---------------------------------------------------------------------------
# S14: Badge Assignment
# ---------------------------------------------------------------------------


async def test_assign_badge_to_product(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_product: Product,
    seed_branch,
) -> None:
    """S14: Assign badge to product; public menu product detail shows the badge."""
    # Create a system badge directly in DB (seed_data would be from migration in prod;
    # here we create it manually since migration 005 may not have run in tests)
    badge = Badge(
        code="chef_recommends",
        name="Chef recomienda",
        color="#8B5CF6",
        icon="star",
        is_system=True,
        tenant_id=None,
    )
    db_session.add(badge)
    await db_session.commit()

    # Assign badge via dashboard API
    assign_resp = await client.put(
        f"/api/dashboard/products/{seed_product.id}/badges",
        json={"badges": [{"badge_id": badge.id, "sort_order": 0}]},
        headers=auth_headers("ADMIN"),
    )
    assert assign_resp.status_code == 200

    # Fetch product detail from public API
    detail_resp = await client.get(
        f"/api/public/menu/{seed_branch.slug}/product/{seed_product.id}"
    )
    assert detail_resp.status_code == 200

    product_detail = detail_resp.json()
    badges = product_detail.get("badges", [])
    badge_codes = [b["code"] for b in badges]
    assert "chef_recommends" in badge_codes, (
        f"Expected badge 'chef_recommends' in product.badges, got {badge_codes}"
    )


# ---------------------------------------------------------------------------
# S15: Custom Seal Creation and Assignment
# ---------------------------------------------------------------------------


async def test_assign_seal_to_product(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_product: Product,
    seed_branch,
    seed_tenant,
) -> None:
    """S15 part 1: Assign seal to product; public product detail shows the seal."""
    # Create a seal for this tenant
    seal = Seal(
        code="artisan",
        name="Artesanal",
        color="#9333EA",
        icon="hand",
        is_system=True,
        tenant_id=None,
    )
    db_session.add(seal)
    await db_session.commit()

    # Assign seal via dashboard API
    assign_resp = await client.put(
        f"/api/dashboard/products/{seed_product.id}/seals",
        json={"seals": [{"seal_id": seal.id, "sort_order": 0}]},
        headers=auth_headers("ADMIN"),
    )
    assert assign_resp.status_code == 200

    # Fetch product detail from public API
    detail_resp = await client.get(
        f"/api/public/menu/{seed_branch.slug}/product/{seed_product.id}"
    )
    assert detail_resp.status_code == 200

    product_detail = detail_resp.json()
    seals = product_detail.get("seals", [])
    seal_codes = [s["code"] for s in seals]
    assert "artisan" in seal_codes, (
        f"Expected seal 'artisan' in product.seals, got {seal_codes}"
    )


async def test_create_custom_seal(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_product: Product,
    seed_branch,
    seed_tenant,
) -> None:
    """S15 part 2: ADMIN can create a custom seal (is_system=False, tenant_id set).
    Returns 201. Custom seal can then be assigned to a product.
    """
    # Create custom seal via dashboard API
    create_resp = await client.post(
        "/api/dashboard/seals/",
        json={
            "code": "homemade",
            "name": "Casero",
            "color": "#F97316",
        },
        headers=auth_headers("ADMIN"),
    )
    assert create_resp.status_code == 201

    created = create_resp.json()["data"]
    assert created["code"] == "homemade"
    # Custom seals must not be system-level
    assert created.get("is_system") is False
    # tenant_id must be set (our ADMIN belongs to tenant_id=1 per TEST_USERS)
    assert created.get("tenant_id") is not None

    seal_id = created["id"]

    # Verify custom seal can be assigned to a product
    assign_resp = await client.put(
        f"/api/dashboard/products/{seed_product.id}/seals",
        json={"seals": [{"seal_id": seal_id, "sort_order": 0}]},
        headers=auth_headers("ADMIN"),
    )
    assert assign_resp.status_code == 200
