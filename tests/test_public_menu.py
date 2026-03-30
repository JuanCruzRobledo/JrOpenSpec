"""Tests for the public menu API — filtering, pricing, and rate limiting.

Covers spec scenarios:
  S6 — Dietary profile filtering (AND logic)
  S7 — Allergen-free filtering (excludes contains + may_contain, keeps free_of)
  S8 — Per-branch price override and fallback
  S13 — Rate limiting: 429 after 60 requests/minute
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.catalog.allergen import Allergen
from shared.models.catalog.branch_product import BranchProduct
from shared.models.catalog.category import Category
from shared.models.catalog.dietary_profile import DietaryProfile
from shared.models.catalog.product import Product
from shared.models.catalog.product_allergen import ProductAllergen
from shared.models.catalog.product_dietary_profile import ProductDietaryProfile
from shared.models.catalog.subcategory import Subcategory
from shared.models.core.branch import Branch
from shared.models.core.tenant import Tenant


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_product(
    db: AsyncSession,
    *,
    tenant_id: int,
    subcategory_id: int,
    name: str,
    slug: str,
    base_price_cents: int = 1000,
) -> Product:
    product = Product(
        tenant_id=tenant_id,
        subcategory_id=subcategory_id,
        name=name,
        slug=slug,
        base_price_cents=base_price_cents,
        is_available=True,
        is_visible_in_menu=True,
    )
    db.add(product)
    await db.flush()
    return product


async def _link_to_branch(
    db: AsyncSession,
    *,
    branch_id: int,
    product_id: int,
    price_cents: int | None = None,
    is_available: bool = True,
) -> BranchProduct:
    bp = BranchProduct(
        branch_id=branch_id,
        product_id=product_id,
        is_available=is_available,
        price_cents=price_cents,
    )
    db.add(bp)
    await db.flush()
    return bp


async def _assign_dietary(
    db: AsyncSession, *, product_id: int, dietary_profile_id: int
) -> ProductDietaryProfile:
    pdp = ProductDietaryProfile(
        product_id=product_id,
        dietary_profile_id=dietary_profile_id,
    )
    db.add(pdp)
    await db.flush()
    return pdp


async def _assign_allergen(
    db: AsyncSession,
    *,
    product_id: int,
    allergen_id: int,
    presence_type: str,
    risk_level: str = "low",
) -> ProductAllergen:
    pa = ProductAllergen(
        product_id=product_id,
        allergen_id=allergen_id,
        presence_type=presence_type,
        risk_level=risk_level,
    )
    db.add(pa)
    await db.flush()
    return pa


def _all_product_ids_in_menu(data: dict) -> list[int]:
    """Flatten all product IDs from all categories in a menu response."""
    ids = []
    for cat in data.get("categories", []):
        for p in cat.get("products", []):
            ids.append(int(p["id"]))
    return ids


# ---------------------------------------------------------------------------
# Shared sub-fixture: category + subcategory scaffold
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def menu_scaffold(db_session: AsyncSession, seed_tenant: Tenant, seed_branch: Branch):
    """Creates a category + subcategory used by all filtering tests.

    Returns a dict with keys: tenant, branch, subcategory_id.
    """
    category = Category(
        tenant_id=seed_tenant.id,
        name="Food",
        slug="food",
    )
    db_session.add(category)
    await db_session.flush()

    subcategory = Subcategory(
        category_id=category.id,
        name="Mains",
        slug="mains",
    )
    db_session.add(subcategory)
    await db_session.flush()

    return {
        "tenant": seed_tenant,
        "branch": seed_branch,
        "subcategory_id": subcategory.id,
    }


# ---------------------------------------------------------------------------
# S6 — Dietary Profile Filtering
# ---------------------------------------------------------------------------


async def test_dietary_filter_single(client: AsyncClient, db_session: AsyncSession, menu_scaffold):
    """S6: ?dietary=vegetarian returns only products with the vegetarian profile; excludes others."""
    tenant = menu_scaffold["tenant"]
    branch = menu_scaffold["branch"]
    sub_id = menu_scaffold["subcategory_id"]

    # Dietary profile
    veg = DietaryProfile(code="vegetarian", name="Vegetariano", is_system=True, tenant_id=None)
    db_session.add(veg)
    await db_session.flush()

    # Products
    pizza = await _create_product(db_session, tenant_id=tenant.id, subcategory_id=sub_id, name="Pizza", slug="pizza")
    steak = await _create_product(db_session, tenant_id=tenant.id, subcategory_id=sub_id, name="Steak", slug="steak")
    salad = await _create_product(db_session, tenant_id=tenant.id, subcategory_id=sub_id, name="Salad", slug="salad")

    # Link all products to branch
    await _link_to_branch(db_session, branch_id=branch.id, product_id=pizza.id)
    await _link_to_branch(db_session, branch_id=branch.id, product_id=steak.id)
    await _link_to_branch(db_session, branch_id=branch.id, product_id=salad.id)

    # Pizza and Salad are vegetarian; Steak is not
    await _assign_dietary(db_session, product_id=pizza.id, dietary_profile_id=veg.id)
    await _assign_dietary(db_session, product_id=salad.id, dietary_profile_id=veg.id)

    await db_session.commit()

    response = await client.get(f"/api/public/menu/{branch.slug}?dietary=vegetarian")
    assert response.status_code == 200

    product_ids = _all_product_ids_in_menu(response.json())
    assert pizza.id in product_ids, "Pizza (vegetarian) must appear"
    assert salad.id in product_ids, "Salad (vegetarian) must appear"
    assert steak.id not in product_ids, "Steak (non-vegetarian) must be excluded"


async def test_dietary_filter_multi(client: AsyncClient, db_session: AsyncSession, menu_scaffold):
    """S6: ?dietary=vegan,vegetarian returns only products matching BOTH profiles (AND logic)."""
    tenant = menu_scaffold["tenant"]
    branch = menu_scaffold["branch"]
    sub_id = menu_scaffold["subcategory_id"]

    # Dietary profiles
    veg = DietaryProfile(code="vegetarian", name="Vegetariano", is_system=True, tenant_id=None)
    vegan = DietaryProfile(code="vegan", name="Vegano", is_system=True, tenant_id=None)
    db_session.add_all([veg, vegan])
    await db_session.flush()

    # Products: Salad (both), Pizza (vegetarian only), Steak (neither)
    pizza = await _create_product(db_session, tenant_id=tenant.id, subcategory_id=sub_id, name="Pizza", slug="pizza-multi")
    steak = await _create_product(db_session, tenant_id=tenant.id, subcategory_id=sub_id, name="Steak", slug="steak-multi")
    salad = await _create_product(db_session, tenant_id=tenant.id, subcategory_id=sub_id, name="Salad", slug="salad-multi")

    await _link_to_branch(db_session, branch_id=branch.id, product_id=pizza.id)
    await _link_to_branch(db_session, branch_id=branch.id, product_id=steak.id)
    await _link_to_branch(db_session, branch_id=branch.id, product_id=salad.id)

    # Pizza: only vegetarian
    await _assign_dietary(db_session, product_id=pizza.id, dietary_profile_id=veg.id)
    # Salad: both vegan + vegetarian
    await _assign_dietary(db_session, product_id=salad.id, dietary_profile_id=veg.id)
    await _assign_dietary(db_session, product_id=salad.id, dietary_profile_id=vegan.id)

    await db_session.commit()

    response = await client.get(f"/api/public/menu/{branch.slug}?dietary=vegan,vegetarian")
    assert response.status_code == 200

    product_ids = _all_product_ids_in_menu(response.json())
    assert salad.id in product_ids, "Salad (vegan+vegetarian) must appear"
    assert pizza.id not in product_ids, "Pizza (only vegetarian, not vegan) must be excluded"
    assert steak.id not in product_ids, "Steak (neither) must be excluded"


# ---------------------------------------------------------------------------
# S7 — Allergen-Free Filtering
# ---------------------------------------------------------------------------


async def test_allergen_free_excludes_contains(client: AsyncClient, db_session: AsyncSession, menu_scaffold):
    """S7: ?allergen_free=gluten excludes products with gluten presence_type='contains'."""
    tenant = menu_scaffold["tenant"]
    branch = menu_scaffold["branch"]
    sub_id = menu_scaffold["subcategory_id"]

    gluten = Allergen(code="gluten", name="Gluten", is_system=True, tenant_id=None)
    db_session.add(gluten)
    await db_session.flush()

    pizza = await _create_product(db_session, tenant_id=tenant.id, subcategory_id=sub_id, name="Pizza", slug="pizza-af-c")
    await _link_to_branch(db_session, branch_id=branch.id, product_id=pizza.id)
    await _assign_allergen(db_session, product_id=pizza.id, allergen_id=gluten.id, presence_type="contains", risk_level="severe")

    await db_session.commit()

    response = await client.get(f"/api/public/menu/{branch.slug}?allergen_free=gluten")
    assert response.status_code == 200

    product_ids = _all_product_ids_in_menu(response.json())
    assert pizza.id not in product_ids, "Product with contains=gluten must be excluded"


async def test_allergen_free_excludes_may_contain(client: AsyncClient, db_session: AsyncSession, menu_scaffold):
    """S7: ?allergen_free=gluten also excludes products with gluten presence_type='may_contain'."""
    tenant = menu_scaffold["tenant"]
    branch = menu_scaffold["branch"]
    sub_id = menu_scaffold["subcategory_id"]

    gluten = Allergen(code="gluten", name="Gluten", is_system=True, tenant_id=None)
    db_session.add(gluten)
    await db_session.flush()

    burger = await _create_product(db_session, tenant_id=tenant.id, subcategory_id=sub_id, name="Burger", slug="burger-af-mc")
    await _link_to_branch(db_session, branch_id=branch.id, product_id=burger.id)
    await _assign_allergen(db_session, product_id=burger.id, allergen_id=gluten.id, presence_type="may_contain", risk_level="moderate")

    await db_session.commit()

    response = await client.get(f"/api/public/menu/{branch.slug}?allergen_free=gluten")
    assert response.status_code == 200

    product_ids = _all_product_ids_in_menu(response.json())
    assert burger.id not in product_ids, "Product with may_contain=gluten must be excluded"


async def test_allergen_free_keeps_free_of(client: AsyncClient, db_session: AsyncSession, menu_scaffold):
    """S7: ?allergen_free=gluten KEEPS products with gluten presence_type='free_of' (explicitly gluten-free)."""
    tenant = menu_scaffold["tenant"]
    branch = menu_scaffold["branch"]
    sub_id = menu_scaffold["subcategory_id"]

    gluten = Allergen(code="gluten", name="Gluten", is_system=True, tenant_id=None)
    db_session.add(gluten)
    await db_session.flush()

    salad = await _create_product(db_session, tenant_id=tenant.id, subcategory_id=sub_id, name="Salad", slug="salad-af-fo")
    await _link_to_branch(db_session, branch_id=branch.id, product_id=salad.id)
    # free_of must use risk_level=low (DB constraint)
    await _assign_allergen(db_session, product_id=salad.id, allergen_id=gluten.id, presence_type="free_of", risk_level="low")

    await db_session.commit()

    response = await client.get(f"/api/public/menu/{branch.slug}?allergen_free=gluten")
    assert response.status_code == 200

    product_ids = _all_product_ids_in_menu(response.json())
    assert salad.id in product_ids, "Product with free_of=gluten must be KEPT (it is explicitly gluten-free)"


# ---------------------------------------------------------------------------
# S8 — Per-Branch Pricing
# ---------------------------------------------------------------------------


async def test_branch_price_override(client: AsyncClient, db_session: AsyncSession, seed_product: Product, seed_branch: Branch):
    """S8: BranchProduct.price_cents overrides base_price_cents in the menu response."""
    # seed_product has base_price_cents=1000, BranchProduct.price_cents=None
    # Update the BranchProduct to have price_cents=1500
    result = await db_session.execute(
        select(BranchProduct).where(
            BranchProduct.product_id == seed_product.id,
            BranchProduct.branch_id == seed_branch.id,
        )
    )
    bp = result.scalar_one()
    bp.price_cents = 1500
    await db_session.commit()

    response = await client.get(f"/api/public/menu/{seed_branch.slug}")
    assert response.status_code == 200

    product_ids = _all_product_ids_in_menu(response.json())
    assert seed_product.id in product_ids

    # Find the product in the response and check its price
    for cat in response.json().get("categories", []):
        for p in cat.get("products", []):
            if p["id"] == seed_product.id:
                assert p["priceCents"] == 1500, f"Expected branch override price 1500, got {p['priceCents']}"
                return

    pytest.fail("Product not found in menu response")


async def test_branch_price_fallback(client: AsyncClient, db_session: AsyncSession, seed_product: Product, seed_branch: Branch):
    """S8: When BranchProduct.price_cents is NULL, response uses product.base_price_cents."""
    # Confirm seed_product has price_cents=None (set in fixture)
    result = await db_session.execute(
        select(BranchProduct).where(
            BranchProduct.product_id == seed_product.id,
            BranchProduct.branch_id == seed_branch.id,
        )
    )
    bp = result.scalar_one()
    assert bp.price_cents is None, "Fixture must have price_cents=None for this test"

    response = await client.get(f"/api/public/menu/{seed_branch.slug}")
    assert response.status_code == 200

    for cat in response.json().get("categories", []):
        for p in cat.get("products", []):
            if p["id"] == seed_product.id:
                assert p["priceCents"] == seed_product.base_price_cents, (
                    f"Expected fallback to base_price_cents={seed_product.base_price_cents}, "
                    f"got {p['priceCents']}"
                )
                return

    pytest.fail("Product not found in menu response")


# ---------------------------------------------------------------------------
# Cache-Control header
# ---------------------------------------------------------------------------


async def test_cache_control_header(client: AsyncClient, seed_branch: Branch, seed_product: Product):
    """Public menu response must include Cache-Control: public, max-age=300."""
    response = await client.get(f"/api/public/menu/{seed_branch.slug}")
    assert response.status_code == 200
    assert "cache-control" in response.headers
    assert response.headers["cache-control"] == "public, max-age=300"


# ---------------------------------------------------------------------------
# S13 — Rate Limiting
# ---------------------------------------------------------------------------


async def test_rate_limit_429(
    client: AsyncClient,
    enable_rate_limit,
    seed_branch: Branch,
    seed_product: Product,
):
    """S13: After 60 requests from the same IP, request #61 returns HTTP 429."""
    url = f"/api/public/menu/{seed_branch.slug}"

    # Fire 60 requests — all should succeed (2xx or cached)
    for i in range(60):
        response = await client.get(url)
        assert response.status_code != 429, f"Request #{i + 1} unexpectedly returned 429"

    # Request #61 must be rate-limited
    response = await client.get(url)
    assert response.status_code == 429, "Request #61 must return HTTP 429 Too Many Requests"


async def test_rate_limit_retry_after_header(
    client: AsyncClient,
    enable_rate_limit,
    seed_branch: Branch,
    seed_product: Product,
):
    """S13: The 429 response must include a non-empty Retry-After header."""
    url = f"/api/public/menu/{seed_branch.slug}"

    for _ in range(60):
        await client.get(url)

    response = await client.get(url)
    assert response.status_code == 429

    retry_after = response.headers.get("retry-after") or response.headers.get("Retry-After")
    assert retry_after is not None, "429 response must include Retry-After header"
    assert retry_after.strip() != "", "Retry-After header must not be empty"
