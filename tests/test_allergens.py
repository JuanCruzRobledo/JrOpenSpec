"""Tests for allergen seeding, system protection, and cross-reaction bidirectionality.

Covers scenarios S1, S2, S3 from the menu-domain-fixes spec:
- S1: 14 EU allergens exist as system allergens (is_system=True, tenant_id=None)
- S2: System allergens cannot be deleted or edited by tenants
- S3: Cross-reactions are bidirectional
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Import all models to ensure Base.metadata knows about all tables
import shared.models  # noqa: F401 — registers all models with metadata
from shared.models.catalog.allergen import Allergen
from shared.models.catalog.allergen_cross_reaction import AllergenCrossReaction
from shared.models.marketing.badge import Badge
from shared.models.marketing.seal import Seal
from shared.models.profiles.cooking_method import CookingMethod
from shared.models.catalog.dietary_profile import DietaryProfile

from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Seed helpers — replicate what migration 005 inserts, but directly into
# the SQLAlchemy session (the test DB uses create_all, not alembic upgrade).
# ---------------------------------------------------------------------------

_EU_14_ALLERGEN_CODES = {
    "gluten", "dairy", "eggs", "fish", "crustaceans",
    "tree_nuts", "soy", "celery", "mustard", "sesame",
    "sulfites", "lupins", "mollusks", "peanuts",
}

_EU_14_ALLERGENS = [
    ("gluten", "Gluten"),
    ("dairy", "Lácteos"),
    ("eggs", "Huevos"),
    ("fish", "Pescado"),
    ("crustaceans", "Crustáceos"),
    ("tree_nuts", "Frutos de cáscara"),
    ("soy", "Soja"),
    ("celery", "Apio"),
    ("mustard", "Mostaza"),
    ("sesame", "Sésamo"),
    ("sulfites", "Sulfitos"),
    ("lupins", "Altramuces"),
    ("mollusks", "Moluscos"),
    ("peanuts", "Maní"),
]

_DIETARY_PROFILE_CODES = [
    "vegetarian", "vegan", "gluten_free", "dairy_free",
    "celiac_safe", "keto", "low_sodium",
]

_COOKING_METHOD_CODES = [
    "grill", "oven", "fryer", "steam", "raw",
    "sous_vide", "smoke", "saute", "boil", "roast",
]

_BADGE_DATA = [
    ("new", "Nuevo", "#22C55E"),
    ("best_seller", "Más vendido", "#F59E0B"),
    ("chef_recommends", "Chef recomienda", "#8B5CF6"),
    ("on_sale", "Oferta", "#EF4444"),
]

_SEAL_DATA = [
    ("organic", "Orgánico", "#16A34A"),
    ("local", "Producto local", "#2563EB"),
    ("preservative_free", "Sin conservantes", "#D97706"),
    ("artisan", "Artesanal", "#9333EA"),
    ("sustainable", "Sustentable", "#059669"),
    ("fair_trade", "Comercio justo", "#0891B2"),
]

# Cross-reaction pairs: (code_a, code_b, severity)
_CROSS_REACTION_PAIRS = [
    ("gluten", "celery", "moderate"),
    ("dairy", "soy", "moderate"),
    ("peanuts", "tree_nuts", "severe"),
    ("peanuts", "soy", "moderate"),
    ("peanuts", "lupins", "severe"),
    ("fish", "crustaceans", "moderate"),
]


async def _seed_eu14_allergens(db: AsyncSession) -> dict[str, Allergen]:
    """Insert 14 EU system allergens; return code → Allergen mapping."""
    allergens: dict[str, Allergen] = {}
    for code, name in _EU_14_ALLERGENS:
        a = Allergen(code=code, name=name, is_system=True, tenant_id=None)
        db.add(a)
        allergens[code] = a
    await db.flush()
    return allergens


async def _seed_cross_reactions(
    db: AsyncSession, allergens: dict[str, Allergen]
) -> None:
    """Insert 6 canonical cross-reaction pairs."""
    for code_a, code_b, severity in _CROSS_REACTION_PAIRS:
        a_id = allergens[code_a].id
        b_id = allergens[code_b].id
        low_id, high_id = min(a_id, b_id), max(a_id, b_id)
        cr = AllergenCrossReaction(
            allergen_id=low_id,
            related_allergen_id=high_id,
            description=f"{code_a} cross-reacts with {code_b}",
            severity=severity,
        )
        db.add(cr)
    await db.flush()


async def _seed_dietary_profiles(db: AsyncSession) -> None:
    for code in _DIETARY_PROFILE_CODES:
        db.add(DietaryProfile(code=code, name=code.replace("_", " ").title(), is_system=True, tenant_id=None))
    await db.flush()


async def _seed_cooking_methods(db: AsyncSession) -> None:
    for code in _COOKING_METHOD_CODES:
        db.add(CookingMethod(code=code, name=code.replace("_", " ").title(), is_system=True, tenant_id=None))
    await db.flush()


async def _seed_badges(db: AsyncSession) -> None:
    for code, name, color in _BADGE_DATA:
        db.add(Badge(code=code, name=name, color=color, is_system=True, tenant_id=None))
    await db.flush()


async def _seed_seals(db: AsyncSession) -> None:
    for code, name, color in _SEAL_DATA:
        db.add(Seal(code=code, name=name, color=color, is_system=True, tenant_id=None))
    await db.flush()


# ---------------------------------------------------------------------------
# S1 — 14 EU system allergens are present
# ---------------------------------------------------------------------------


async def test_seed_allergens_count(db_session: AsyncSession) -> None:
    """After seeding, exactly 14 system allergens exist with tenant_id=None."""
    await _seed_eu14_allergens(db_session)
    await db_session.commit()

    count = (
        await db_session.execute(
            select(func.count()).where(
                Allergen.is_system.is_(True),
                Allergen.tenant_id.is_(None),
            )
        )
    ).scalar()

    assert count == 14


async def test_seed_allergen_codes(db_session: AsyncSession) -> None:
    """Seeded allergens have exactly the 14 EU-required codes."""
    await _seed_eu14_allergens(db_session)
    await db_session.commit()

    result = await db_session.execute(
        select(Allergen.code).where(
            Allergen.is_system.is_(True),
            Allergen.tenant_id.is_(None),
        )
    )
    codes = {row[0] for row in result.all()}

    assert codes == _EU_14_ALLERGEN_CODES


async def test_seed_cross_reactions_count(db_session: AsyncSession) -> None:
    """After seeding, exactly 6 cross-reaction pairs exist."""
    allergens = await _seed_eu14_allergens(db_session)
    await _seed_cross_reactions(db_session, allergens)
    await db_session.commit()

    count = (
        await db_session.execute(select(func.count()).select_from(AllergenCrossReaction))
    ).scalar()

    assert count == 6


async def test_seed_cross_reactions_pairs(db_session: AsyncSession) -> None:
    """All 6 canonical pairs are present, identified by allergen codes."""
    allergens = await _seed_eu14_allergens(db_session)
    await _seed_cross_reactions(db_session, allergens)
    await db_session.commit()

    result = await db_session.execute(
        select(AllergenCrossReaction.allergen_id, AllergenCrossReaction.related_allergen_id)
    )
    stored_pairs = {(row[0], row[1]) for row in result.all()}

    # Build expected pairs using seeded IDs
    for code_a, code_b, _ in _CROSS_REACTION_PAIRS:
        a_id = allergens[code_a].id
        b_id = allergens[code_b].id
        low_id, high_id = min(a_id, b_id), max(a_id, b_id)
        assert (low_id, high_id) in stored_pairs, (
            f"Expected pair ({code_a}, {code_b}) not found in cross-reactions"
        )


async def test_seed_dietary_profiles_count(db_session: AsyncSession) -> None:
    """Exactly 7 system dietary profiles are seeded."""
    await _seed_dietary_profiles(db_session)
    await db_session.commit()

    count = (
        await db_session.execute(
            select(func.count()).where(DietaryProfile.is_system.is_(True))
        )
    ).scalar()

    assert count == 7


async def test_seed_cooking_methods_count(db_session: AsyncSession) -> None:
    """Exactly 10 system cooking methods are seeded."""
    await _seed_cooking_methods(db_session)
    await db_session.commit()

    count = (
        await db_session.execute(
            select(func.count()).where(CookingMethod.is_system.is_(True))
        )
    ).scalar()

    assert count == 10


async def test_seed_badges_count(db_session: AsyncSession) -> None:
    """Exactly 4 system badges are seeded."""
    await _seed_badges(db_session)
    await db_session.commit()

    count = (
        await db_session.execute(
            select(func.count()).where(Badge.is_system.is_(True))
        )
    ).scalar()

    assert count == 4


async def test_seed_seals_count(db_session: AsyncSession) -> None:
    """Exactly 6 system seals are seeded."""
    await _seed_seals(db_session)
    await db_session.commit()

    count = (
        await db_session.execute(
            select(func.count()).where(Seal.is_system.is_(True))
        )
    ).scalar()

    assert count == 6


async def test_seed_idempotent(db_session: AsyncSession) -> None:
    """Inserting the seed data twice does not create duplicate rows."""
    # First insertion
    await _seed_eu14_allergens(db_session)
    await _seed_dietary_profiles(db_session)
    await _seed_cooking_methods(db_session)
    await _seed_badges(db_session)
    await _seed_seals(db_session)
    await db_session.commit()

    # Second insertion — use WHERE NOT EXISTS to mirror migration idempotency
    for code, name in _EU_14_ALLERGENS:
        existing = (
            await db_session.execute(
                select(func.count()).where(
                    Allergen.code == code, Allergen.is_system.is_(True)
                )
            )
        ).scalar()
        if existing == 0:
            db_session.add(Allergen(code=code, name=name, is_system=True, tenant_id=None))

    await db_session.commit()

    count = (
        await db_session.execute(
            select(func.count()).where(Allergen.is_system.is_(True))
        )
    ).scalar()

    assert count == 14, "Idempotent insert must not create duplicate allergens"


# ---------------------------------------------------------------------------
# S1 (API) — GET /api/dashboard/allergens returns allergens visible to tenant
# ---------------------------------------------------------------------------


async def test_create_custom_allergen(client: AsyncClient, seed_tenant) -> None:
    """Authenticated ADMIN can create a custom allergen; returns 201."""
    headers = auth_headers("ADMIN")
    payload = {
        "codigo": "shellfish",
        "nombre": "Mariscos",
        "descripcion": "Mariscos y derivados",
    }
    response = await client.post(
        "/api/dashboard/allergens/",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["codigo"] == "shellfish"
    assert data["es_sistema"] is False


# ---------------------------------------------------------------------------
# S2 — System allergens are immutable (cannot be deleted or edited)
# ---------------------------------------------------------------------------


async def test_system_allergen_cannot_be_deleted(
    client: AsyncClient, db_session: AsyncSession, seed_allergens
) -> None:
    """DELETE on a system allergen returns 403 (ForbiddenError from service)."""
    # seed_allergens contains is_system=True allergens
    system_allergen = seed_allergens[0]
    assert system_allergen.is_system is True

    headers = auth_headers("ADMIN")
    response = await client.delete(
        f"/api/dashboard/allergens/{system_allergen.id}",
        headers=headers,
    )
    assert response.status_code in (400, 403), (
        f"Expected 400 or 403 when deleting a system allergen, got {response.status_code}"
    )


async def test_system_allergen_cannot_be_edited(
    client: AsyncClient, db_session: AsyncSession, seed_allergens
) -> None:
    """PUT on a system allergen returns 403 (ForbiddenError from service)."""
    system_allergen = seed_allergens[0]
    assert system_allergen.is_system is True

    headers = auth_headers("ADMIN")
    response = await client.put(
        f"/api/dashboard/allergens/{system_allergen.id}",
        json={"nombre": "Nombre modificado"},
        headers=headers,
    )
    assert response.status_code in (400, 403), (
        f"Expected 400 or 403 when editing a system allergen, got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# S3 — Cross-reactions are bidirectional
# ---------------------------------------------------------------------------


async def test_cross_reaction_bidirectional(
    client: AsyncClient, db_session: AsyncSession, seed_allergens
) -> None:
    """A cross-reaction between A and B surfaces in both A's and B's lists."""
    # seed_allergens provides: gluten(0), dairy(1), peanuts(2), tree_nuts(3)
    peanuts = next(a for a in seed_allergens if a.code == "peanuts")
    tree_nuts = next(a for a in seed_allergens if a.code == "tree_nuts")

    # Create cross-reaction via dashboard API
    headers = auth_headers("ADMIN")
    low_id = min(peanuts.id, tree_nuts.id)
    high_id = max(peanuts.id, tree_nuts.id)

    # POST directly to the service-level endpoint
    cr_payload = {
        "related_allergen_id": tree_nuts.id,
        "descripcion": "Maní puede causar reacción cruzada con frutos de cáscara",
        "severidad": "severe",
    }
    create_resp = await client.post(
        f"/api/dashboard/allergens/{peanuts.id}/cross-reactions",
        json=cr_payload,
        headers=headers,
    )
    assert create_resp.status_code == 201, (
        f"Failed to create cross-reaction: {create_resp.text}"
    )

    # Query cross-reactions from peanuts' perspective → must include tree_nuts
    peanuts_resp = await client.get(
        f"/api/dashboard/allergens/{peanuts.id}/cross-reactions",
        headers=headers,
    )
    assert peanuts_resp.status_code == 200
    peanuts_cr_codes = [
        item["related_code"] for item in peanuts_resp.json()["data"]
    ]
    assert "tree_nuts" in peanuts_cr_codes, (
        f"tree_nuts not found in peanuts cross-reactions: {peanuts_cr_codes}"
    )

    # Query cross-reactions from tree_nuts' perspective → must include peanuts
    tree_nuts_resp = await client.get(
        f"/api/dashboard/allergens/{tree_nuts.id}/cross-reactions",
        headers=headers,
    )
    assert tree_nuts_resp.status_code == 200
    tree_nuts_cr_codes = [
        item["related_code"] for item in tree_nuts_resp.json()["data"]
    ]
    assert "peanuts" in tree_nuts_cr_codes, (
        f"peanuts not found in tree_nuts cross-reactions: {tree_nuts_cr_codes}"
    )
