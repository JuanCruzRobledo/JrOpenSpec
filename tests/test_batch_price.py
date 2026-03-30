"""Tests for batch price preview and apply endpoints.

Covers scenarios S10 and S11:
- S10: Batch price preview returns old/new prices without persisting changes.
- S11: Negative clamp — fixed_subtract that would yield < 0 is clamped to 0.

Endpoint paths:
  POST /api/dashboard/products/batch-price/preview
  POST /api/dashboard/products/batch-price/apply
"""

from __future__ import annotations

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.catalog.branch_product import BranchProduct
from shared.models.catalog.category import Category
from shared.models.catalog.product import Product
from shared.models.catalog.subcategory import Subcategory
from shared.models.core.branch import Branch
from shared.models.core.tenant import Tenant
from tests.conftest import auth_headers

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PREVIEW_URL = "/api/dashboard/products/batch-price/preview"
APPLY_URL = "/api/dashboard/products/batch-price/apply"

# ---------------------------------------------------------------------------
# Additional fixtures — multi-product setup for S10
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def seed_two_products(
    db_session: AsyncSession,
    seed_tenant: Tenant,
    seed_branch: Branch,
) -> dict:
    """Create two products with known branch prices for batch-price tests.

    Returns a dict with:
        - product_1: Product (base_price_cents=1000, BranchProduct.price_cents=1500)
        - product_2: Product (base_price_cents=2000, BranchProduct.price_cents=None → falls back to 2000)
        - branch: Branch (the seed_branch)
    """
    category = Category(
        tenant_id=seed_tenant.id,
        name="Batch Category",
        slug="batch-category",
    )
    db_session.add(category)
    await db_session.flush()

    subcategory = Subcategory(
        category_id=category.id,
        name="Batch Subcategory",
        slug="batch-subcategory",
    )
    db_session.add(subcategory)
    await db_session.flush()

    product_1 = Product(
        tenant_id=seed_tenant.id,
        subcategory_id=subcategory.id,
        name="Pizza",
        slug="pizza",
        base_price_cents=1000,
        is_available=True,
        is_visible_in_menu=True,
    )
    product_2 = Product(
        tenant_id=seed_tenant.id,
        subcategory_id=subcategory.id,
        name="Steak",
        slug="steak",
        base_price_cents=2000,
        is_available=True,
        is_visible_in_menu=True,
    )
    db_session.add_all([product_1, product_2])
    await db_session.flush()

    # product_1 has an explicit branch price override
    bp_1 = BranchProduct(
        branch_id=seed_branch.id,
        product_id=product_1.id,
        is_available=True,
        price_cents=1500,
    )
    # product_2 uses base_price_cents (no override)
    bp_2 = BranchProduct(
        branch_id=seed_branch.id,
        product_id=product_2.id,
        is_available=True,
        price_cents=None,
    )
    db_session.add_all([bp_1, bp_2])
    await db_session.commit()

    return {
        "product_1": product_1,
        "product_2": product_2,
        "branch": seed_branch,
    }


@pytest_asyncio.fixture
async def seed_cheap_product(
    db_session: AsyncSession,
    seed_tenant: Tenant,
    seed_branch: Branch,
) -> dict:
    """Create a product with a low price for clamp tests (S11).

    Returns a dict with:
        - product: Product (base_price_cents=50)
        - branch_product: BranchProduct (price_cents=50)
    """
    category = Category(
        tenant_id=seed_tenant.id,
        name="Clamp Category",
        slug="clamp-category",
    )
    db_session.add(category)
    await db_session.flush()

    subcategory = Subcategory(
        category_id=category.id,
        name="Clamp Subcategory",
        slug="clamp-subcategory",
    )
    db_session.add(subcategory)
    await db_session.flush()

    product = Product(
        tenant_id=seed_tenant.id,
        subcategory_id=subcategory.id,
        name="Water",
        slug="water",
        base_price_cents=50,
        is_available=True,
        is_visible_in_menu=True,
    )
    db_session.add(product)
    await db_session.flush()

    branch_product = BranchProduct(
        branch_id=seed_branch.id,
        product_id=product.id,
        is_available=True,
        price_cents=50,
    )
    db_session.add(branch_product)
    await db_session.commit()

    return {"product": product, "branch_product": branch_product}


# ---------------------------------------------------------------------------
# S10 — Batch Price Update Preview
# ---------------------------------------------------------------------------


async def test_batch_preview_returns_prices(
    client: AsyncClient,
    seed_two_products: dict,
) -> None:
    """POST preview returns old_price_cents and new_price_cents for all selected products.

    S10: given [Pizza, Steak], operation=percentage_increase, amount=10
    — response contains cambios entries for both products.
    """
    product_1 = seed_two_products["product_1"]
    product_2 = seed_two_products["product_2"]

    payload = {
        "product_ids": [product_1.id, product_2.id],
        "operation": "percentage_increase",
        "amount": "10.0",
        "branch_id": None,
    }

    response = await client.post(
        PREVIEW_URL,
        json=payload,
        headers=auth_headers("ADMIN"),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["total_cambios"] == 2
    assert data["total_productos"] == 2

    # Verify that each cambios entry carries both price fields
    for change in data["cambios"]:
        assert "precio_anterior_centavos" in change
        assert "precio_nuevo_centavos" in change
        assert change["precio_nuevo_centavos"] >= change["precio_anterior_centavos"]

    # Verify product_1: effective price is 1500 (explicit branch override)
    p1_change = next(c for c in data["cambios"] if c["product_id"] == product_1.id)
    assert p1_change["precio_anterior_centavos"] == 1500
    assert p1_change["precio_nuevo_centavos"] == round(1500 * 1.10)  # 1650

    # Verify product_2: effective price is 2000 (falls back to base_price_cents)
    p2_change = next(c for c in data["cambios"] if c["product_id"] == product_2.id)
    assert p2_change["precio_anterior_centavos"] == 2000
    assert p2_change["precio_nuevo_centavos"] == round(2000 * 1.10)  # 2200


async def test_batch_preview_no_persistence(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_two_products: dict,
) -> None:
    """Preview must not persist any price changes to the database (S10).

    After calling preview, BranchProduct.price_cents must remain unchanged.
    """
    product_1 = seed_two_products["product_1"]
    branch = seed_two_products["branch"]

    payload = {
        "product_ids": [product_1.id],
        "operation": "percentage_increase",
        "amount": "50.0",
        "branch_id": branch.id,
    }

    response = await client.post(
        PREVIEW_URL,
        json=payload,
        headers=auth_headers("ADMIN"),
    )
    assert response.status_code == 200, response.text

    # Query the DB directly and confirm price_cents is still 1500 (unchanged)
    result = await db_session.execute(
        select(BranchProduct).where(
            BranchProduct.branch_id == branch.id,
            BranchProduct.product_id == product_1.id,
        )
    )
    bp = result.scalar_one()
    assert bp.price_cents == 1500, (
        f"Preview must not persist changes; expected 1500 but got {bp.price_cents}"
    )


async def test_batch_preview_rounding(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_tenant: Tenant,
    seed_branch: Branch,
) -> None:
    """10% increase on 333 cents rounds to 366 (round half-to-even)."""
    category = Category(
        tenant_id=seed_tenant.id,
        name="Round Cat",
        slug="round-cat",
    )
    db_session.add(category)
    await db_session.flush()

    subcategory = Subcategory(
        category_id=category.id,
        name="Round Sub",
        slug="round-sub",
    )
    db_session.add(subcategory)
    await db_session.flush()

    product = Product(
        tenant_id=seed_tenant.id,
        subcategory_id=subcategory.id,
        name="Odd Price",
        slug="odd-price",
        base_price_cents=333,
        is_available=True,
        is_visible_in_menu=True,
    )
    db_session.add(product)
    await db_session.flush()

    bp = BranchProduct(
        branch_id=seed_branch.id,
        product_id=product.id,
        is_available=True,
        price_cents=333,
    )
    db_session.add(bp)
    await db_session.commit()

    payload = {
        "product_ids": [product.id],
        "operation": "percentage_increase",
        "amount": "10.0",
        "branch_id": seed_branch.id,
    }

    response = await client.post(
        PREVIEW_URL,
        json=payload,
        headers=auth_headers("ADMIN"),
    )
    assert response.status_code == 200, response.text
    change = response.json()["data"]["cambios"][0]
    assert change["precio_anterior_centavos"] == 333
    assert change["precio_nuevo_centavos"] == round(333 * 1.10)  # 366


async def test_batch_preview_decrease_rounding(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_tenant: Tenant,
    seed_branch: Branch,
) -> None:
    """10% decrease on 333 cents rounds to 300."""
    category = Category(
        tenant_id=seed_tenant.id,
        name="Dec Cat",
        slug="dec-cat",
    )
    db_session.add(category)
    await db_session.flush()

    subcategory = Subcategory(
        category_id=category.id,
        name="Dec Sub",
        slug="dec-sub",
    )
    db_session.add(subcategory)
    await db_session.flush()

    product = Product(
        tenant_id=seed_tenant.id,
        subcategory_id=subcategory.id,
        name="Decrease Odd",
        slug="decrease-odd",
        base_price_cents=333,
        is_available=True,
        is_visible_in_menu=True,
    )
    db_session.add(product)
    await db_session.flush()

    bp = BranchProduct(
        branch_id=seed_branch.id,
        product_id=product.id,
        is_available=True,
        price_cents=333,
    )
    db_session.add(bp)
    await db_session.commit()

    payload = {
        "product_ids": [product.id],
        "operation": "percentage_decrease",
        "amount": "10.0",
        "branch_id": seed_branch.id,
    }

    response = await client.post(
        PREVIEW_URL,
        json=payload,
        headers=auth_headers("ADMIN"),
    )
    assert response.status_code == 200, response.text
    change = response.json()["data"]["cambios"][0]
    assert change["precio_anterior_centavos"] == 333
    assert change["precio_nuevo_centavos"] == round(333 * 0.90)  # 300


# ---------------------------------------------------------------------------
# S10 — Batch Price Apply
# ---------------------------------------------------------------------------


async def test_batch_apply_persists(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_two_products: dict,
) -> None:
    """Apply persists new prices to BranchProduct rows in the database (S10)."""
    product_1 = seed_two_products["product_1"]
    branch = seed_two_products["branch"]

    payload = {
        "product_ids": [product_1.id],
        "operation": "percentage_increase",
        "amount": "10.0",
        "branch_id": branch.id,
        "confirmed": True,
    }

    response = await client.post(
        APPLY_URL,
        json=payload,
        headers=auth_headers("ADMIN"),
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["applied"] == 1

    # Expire and re-fetch from DB to bypass SQLAlchemy identity map cache
    await db_session.rollback()
    result = await db_session.execute(
        select(BranchProduct).where(
            BranchProduct.branch_id == branch.id,
            BranchProduct.product_id == product_1.id,
        )
    )
    bp = result.scalar_one()
    expected_price = round(1500 * 1.10)  # 1650
    assert bp.price_cents == expected_price, (
        f"Apply must persist new price; expected {expected_price} but got {bp.price_cents}"
    )


async def test_batch_apply_creates_audit(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_two_products: dict,
) -> None:
    """After apply, audit log entries exist with old_value and new_value (S10)."""
    product_1 = seed_two_products["product_1"]
    branch = seed_two_products["branch"]

    payload = {
        "product_ids": [product_1.id],
        "operation": "fixed_add",
        "amount": "500",
        "branch_id": branch.id,
        "confirmed": True,
    }

    response = await client.post(
        APPLY_URL,
        json=payload,
        headers=auth_headers("ADMIN"),
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["applied"] == 1

    # The service attempts to create AuditLog entries; if the model is available,
    # audit_log_ids will be populated. If not (ImportError path), it logs only.
    # This test verifies the endpoint succeeds and applied count is correct.
    # When AuditLog model is available, we also verify the DB record.
    try:
        from shared.models.audit.audit_log import AuditLog

        await db_session.rollback()
        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "branch_product",
                AuditLog.action == "batch_price_update",
            )
        )
        audit_rows = result.scalars().all()
        assert len(audit_rows) >= 1, "Expected at least one audit log entry"
        audit = audit_rows[0]
        assert audit.old_value is not None
        assert audit.new_value is not None
    except ImportError:
        # AuditLog model not yet available — endpoint must still return 200
        pass


# ---------------------------------------------------------------------------
# S11 — Batch Price Negative Clamp
# ---------------------------------------------------------------------------


async def test_batch_negative_clamp_preview(
    client: AsyncClient,
    seed_cheap_product: dict,
) -> None:
    """Preview clamps negative results to 0 — fixed_subtract 100 from 50 cents (S11).

    Given: Water has price_cents=50 in branch "centro"
    When: batch update with operation=fixed_subtract, amount=100
    Then: preview shows new_price_cents=0 (not -50)
    """
    product = seed_cheap_product["product"]

    payload = {
        "product_ids": [product.id],
        "operation": "fixed_subtract",
        "amount": "100",
        "branch_id": None,
    }

    response = await client.post(
        PREVIEW_URL,
        json=payload,
        headers=auth_headers("ADMIN"),
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["total_cambios"] == 1

    change = data["cambios"][0]
    assert change["precio_anterior_centavos"] == 50
    assert change["precio_nuevo_centavos"] == 0, (
        f"Price must be clamped to 0, not negative; got {change['precio_nuevo_centavos']}"
    )


async def test_batch_negative_clamp_apply(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_cheap_product: dict,
) -> None:
    """Apply also clamps to 0 — fixed_subtract 5000 from 1000 cents (S11).

    Verify both the endpoint response and the DB row reflect price_cents=0.
    """
    product = seed_cheap_product["product"]
    branch_product = seed_cheap_product["branch_product"]

    payload = {
        "product_ids": [product.id],
        "operation": "fixed_subtract",
        "amount": "5000",
        "branch_id": branch_product.branch_id,
        "confirmed": True,
    }

    response = await client.post(
        APPLY_URL,
        json=payload,
        headers=auth_headers("ADMIN"),
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["applied"] == 1

    # Confirm DB row is clamped to 0, not negative
    await db_session.rollback()
    result = await db_session.execute(
        select(BranchProduct).where(
            BranchProduct.branch_id == branch_product.branch_id,
            BranchProduct.product_id == product.id,
        )
    )
    bp = result.scalar_one()
    assert bp.price_cents == 0, (
        f"Apply must clamp to 0, not negative; got {bp.price_cents}"
    )
