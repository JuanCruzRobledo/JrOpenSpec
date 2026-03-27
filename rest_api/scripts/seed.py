"""Idempotent seed script for development environment.

Creates sample data: tenant, branch, sectors, tables, users, allergens,
profiles, categories, subcategories, products, branch_products, product_allergens,
dietary profiles, badges, seals, cross-reactions, ingredients.

Usage:
    # As module
    python -m rest_api.scripts.seed

    # As import
    from rest_api.scripts.seed import run_seed
    await run_seed()
"""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

from passlib.context import CryptContext
from shared.infrastructure.db import async_session_factory
from shared.models.catalog.allergen import Allergen
from shared.models.catalog.allergen_cross_reaction import AllergenCrossReaction
from shared.models.catalog.branch_product import BranchProduct
from shared.models.catalog.category import Category
from shared.models.catalog.dietary_profile import DietaryProfile
from shared.models.catalog.product import Product
from shared.models.catalog.product_allergen import ProductAllergen
from shared.models.catalog.product_badge import ProductBadge
from shared.models.catalog.product_cooking_method import ProductCookingMethod
from shared.models.catalog.product_dietary_profile import ProductDietaryProfile
from shared.models.catalog.product_ingredient import ProductIngredient
from shared.models.catalog.product_seal import ProductSeal
from shared.models.catalog.subcategory import Subcategory
from shared.models.core.branch import Branch
from shared.models.core.tenant import Tenant
from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
from shared.models.marketing.badge import Badge
from shared.models.marketing.seal import Seal
from shared.models.profiles.cooking_method import CookingMethod
from shared.models.profiles.cuisine_type import CuisineType
from shared.models.profiles.flavor_profile import FlavorProfile
from shared.models.profiles.texture_profile import TextureProfile
from shared.models.room.sector import Sector
from shared.models.room.table import Table
from sqlalchemy import select

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_PASSWORD = "TestPassword123!"


# ── Helper ──────────────────────────────────────────────────────────────


async def _get_or_create(session, model, filters: dict, defaults: dict | None = None):
    """Return existing row or create new one. Idempotent."""
    stmt = select(model)
    for col, val in filters.items():
        stmt = stmt.where(getattr(model, col) == val)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    if instance is not None:
        return instance, False

    data = {**filters, **(defaults or {})}
    instance = model(**data)
    session.add(instance)
    return instance, True


# ── Seed functions ──────────────────────────────────────────────────────


async def _seed_tenant(session) -> Tenant:
    logger.info("Seeding tenant...")
    tenant, created = await _get_or_create(
        session,
        Tenant,
        {"slug": "buen-sabor"},
        {
            "name": "Buen Sabor",
            "description": "Restaurante de comida argentina con las mejores pastas, carnes y postres.",
            "banner_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200",
            "phone": "+54 261 555-0000",
            "email": "info@buensabor.com",
            "address": "Mendoza, Argentina",
        },
    )
    if created:
        await session.flush()
        logger.info("  Created tenant: Buen Sabor")
    else:
        logger.info("  Tenant already exists, skipping")
    return tenant


async def _seed_branch(session, tenant: Tenant) -> Branch:
    logger.info("Seeding branch...")
    branch, created = await _get_or_create(
        session,
        Branch,
        {"tenant_id": tenant.id, "slug": "sede-central"},
        {
            "name": "Sede Central",
            "address": "Av. San Martín 1234, Mendoza",
            "phone": "+54 261 555-0100",
            "email": "central@buensabor.com",
            "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=600",
            "opening_time": "11:30",
            "closing_time": "00:00",
            "display_order": 0,
            "latitude": -32.8895,
            "longitude": -68.8458,
        },
    )
    if created:
        await session.flush()
        logger.info("  Created branch: Sede Central")
    else:
        logger.info("  Branch already exists, skipping")
    return branch


async def _seed_sectors(session, branch: Branch) -> dict[str, Sector]:
    logger.info("Seeding sectors...")
    sector_defs = [
        {"name": "Salón Principal", "display_order": 0},
        {"name": "Terraza", "display_order": 1},
        {"name": "Barra", "display_order": 2},
    ]
    sectors = {}
    for s in sector_defs:
        sector, created = await _get_or_create(
            session,
            Sector,
            {"branch_id": branch.id, "name": s["name"]},
            {"display_order": s["display_order"]},
        )
        sectors[s["name"]] = sector
        if created:
            logger.info("  Created sector: %s", s["name"])
    await session.flush()
    return sectors


async def _seed_tables(session, sectors: dict[str, Sector]) -> None:
    logger.info("Seeding tables...")
    table_defs = []

    # Salon Principal: tables 1-10
    salon = sectors["Salón Principal"]
    for i in range(1, 11):
        table_defs.append({"sector_id": salon.id, "number": str(i), "capacity": 4})

    # Terraza: tables T1-T6
    terraza = sectors["Terraza"]
    for i in range(1, 7):
        table_defs.append({"sector_id": terraza.id, "number": f"T{i}", "capacity": 6})

    # Barra: tables B1-B4
    barra = sectors["Barra"]
    for i in range(1, 5):
        table_defs.append({"sector_id": barra.id, "number": f"B{i}", "capacity": 2})

    for t in table_defs:
        _, created = await _get_or_create(
            session,
            Table,
            {"sector_id": t["sector_id"], "number": t["number"]},
            {"capacity": t["capacity"]},
        )
        if created:
            logger.info("  Created table: %s", t["number"])
    await session.flush()


async def _seed_users(session, tenant: Tenant, branch: Branch) -> None:
    logger.info("Seeding users...")
    hashed_pw = pwd_context.hash(DEFAULT_PASSWORD)

    user_defs = [
        {
            "email": "admin@buensabor.com",
            "first_name": "Admin",
            "last_name": "Principal",
            "is_superadmin": True,
            "role": "ADMIN",
        },
        {
            "email": "manager@buensabor.com",
            "first_name": "María",
            "last_name": "González",
            "is_superadmin": False,
            "role": "MANAGER",
        },
        {
            "email": "chef@buensabor.com",
            "first_name": "Carlos",
            "last_name": "Rodríguez",
            "is_superadmin": False,
            "role": "KITCHEN",
        },
        {
            "email": "waiter1@buensabor.com",
            "first_name": "Lucas",
            "last_name": "Fernández",
            "is_superadmin": False,
            "role": "WAITER",
        },
        {
            "email": "waiter2@buensabor.com",
            "first_name": "Ana",
            "last_name": "Martínez",
            "is_superadmin": False,
            "role": "WAITER",
        },
        {
            "email": "cashier@buensabor.com",
            "first_name": "Pablo",
            "last_name": "López",
            "is_superadmin": False,
            "role": "WAITER",
        },
    ]

    for u in user_defs:
        role = u.pop("role")
        user, created = await _get_or_create(
            session,
            User,
            {"email": u["email"]},
            {
                "tenant_id": tenant.id,
                "hashed_password": hashed_pw,
                "first_name": u["first_name"],
                "last_name": u["last_name"],
                "is_superadmin": u["is_superadmin"],
            },
        )
        if created:
            await session.flush()
            logger.info("  Created user: %s", u["email"])

        # Assign branch role
        _, role_created = await _get_or_create(
            session,
            UserBranchRole,
            {"user_id": user.id, "branch_id": branch.id, "role": role},
        )
        if role_created:
            logger.info("    Assigned role: %s", role)

    await session.flush()


async def _seed_allergens(session) -> dict[str, Allergen]:
    """Seed 14 EU mandatory allergens with correct codes per spec."""
    logger.info("Seeding allergens (14 EU)...")
    allergen_defs = [
        {"code": "gluten", "name": "Gluten", "description": "Cereales con gluten: trigo, centeno, cebada, avena, espelta, kamut", "icon": "wheat"},
        {"code": "dairy", "name": "Lácteos", "description": "Leche y derivados incluyendo lactosa y caseína", "icon": "milk"},
        {"code": "eggs", "name": "Huevos", "description": "Huevos y productos derivados", "icon": "egg"},
        {"code": "fish", "name": "Pescado", "description": "Pescado y productos derivados", "icon": "fish"},
        {"code": "crustaceans", "name": "Crustáceos", "description": "Crustáceos y productos derivados", "icon": "shrimp"},
        {"code": "tree_nuts", "name": "Frutos secos", "description": "Almendras, avellanas, nueces, anacardos, pecanas, pistachos, etc.", "icon": "nut"},
        {"code": "soy", "name": "Soja", "description": "Soja y productos derivados", "icon": "soybean"},
        {"code": "celery", "name": "Apio", "description": "Apio y productos derivados", "icon": "celery"},
        {"code": "mustard", "name": "Mostaza", "description": "Mostaza y productos derivados", "icon": "mustard"},
        {"code": "sesame", "name": "Sésamo", "description": "Granos de sésamo y productos derivados", "icon": "sesame"},
        {"code": "sulfites", "name": "Sulfitos", "description": "Dióxido de azufre y sulfitos (>10mg/kg)", "icon": "sulfite"},
        {"code": "lupins", "name": "Altramuces", "description": "Altramuces y productos derivados", "icon": "lupin"},
        {"code": "mollusks", "name": "Moluscos", "description": "Moluscos y productos derivados", "icon": "shell"},
        {"code": "peanuts", "name": "Cacahuetes", "description": "Cacahuetes/maní y productos derivados", "icon": "peanut"},
    ]
    allergens = {}
    for a in allergen_defs:
        allergen, created = await _get_or_create(
            session,
            Allergen,
            {"code": a["code"], "tenant_id": None},
            {
                "name": a["name"],
                "description": a["description"],
                "icon": a["icon"],
                "is_system": True,
            },
        )
        allergens[a["code"]] = allergen
        if created:
            logger.info("  Created allergen: %s (%s)", a["name"], a["code"])
    await session.flush()
    return allergens


async def _seed_cross_reactions(session, allergens: dict[str, Allergen]) -> None:
    """Seed known allergen cross-reactions."""
    logger.info("Seeding allergen cross-reactions...")
    cross_reactions = [
        {
            "pair": ("gluten", "celery"),
            "description": "Sensibilidad cruzada por profilinas — proteínas comunes en cereales y apio",
            "severity": "low",
        },
        {
            "pair": ("dairy", "soy"),
            "description": "Proteínas de soja pueden causar reacción en alérgicos a caseína",
            "severity": "low",
        },
        {
            "pair": ("fish", "crustaceans"),
            "description": "Reactividad cruzada por parvalbúmina en pescado y tropomiosina en crustáceos",
            "severity": "moderate",
        },
        {
            "pair": ("peanuts", "tree_nuts"),
            "description": "Proteínas de almacenamiento similares entre maní y frutos secos",
            "severity": "moderate",
        },
        {
            "pair": ("peanuts", "soy"),
            "description": "Ambos son leguminosas con proteínas vicilina/legumina compartidas",
            "severity": "low",
        },
        {
            "pair": ("lupins", "peanuts"),
            "description": "Ambos son leguminosas con alta reactividad cruzada por conglutinas",
            "severity": "severe",
        },
    ]

    for cr in cross_reactions:
        code_a, code_b = cr["pair"]
        allergen_a = allergens.get(code_a)
        allergen_b = allergens.get(code_b)
        if not allergen_a or not allergen_b:
            continue

        # Enforce canonical ordering: allergen_id < related_allergen_id
        if allergen_a.id > allergen_b.id:
            allergen_a, allergen_b = allergen_b, allergen_a

        _, created = await _get_or_create(
            session,
            AllergenCrossReaction,
            {"allergen_id": allergen_a.id, "related_allergen_id": allergen_b.id},
            {
                "description": cr["description"],
                "severity": cr["severity"],
            },
        )
        if created:
            logger.info("  Created cross-reaction: %s <-> %s", code_a, code_b)
    await session.flush()


async def _seed_dietary_profiles(session) -> dict[str, DietaryProfile]:
    """Seed system dietary profiles."""
    logger.info("Seeding dietary profiles...")
    profile_defs = [
        {"code": "vegetarian", "name": "Vegetariano", "icon": "leaf", "description": "Sin carne ni pescado"},
        {"code": "vegan", "name": "Vegano", "icon": "sprout", "description": "Sin productos de origen animal"},
        {"code": "gluten_free", "name": "Sin gluten", "icon": "wheat-off", "description": "Apto para celíacos"},
        {"code": "dairy_free", "name": "Sin lácteos", "icon": "milk-off", "description": "Sin leche ni derivados"},
        {"code": "celiac_safe", "name": "Apto celíacos", "icon": "shield-check", "description": "Certificado sin TACC"},
        {"code": "keto", "name": "Keto", "icon": "flame", "description": "Bajo en carbohidratos, alto en grasas"},
        {"code": "low_sodium", "name": "Bajo sodio", "icon": "salt-off", "description": "Reducido en sal"},
    ]
    profiles = {}
    for p in profile_defs:
        profile, created = await _get_or_create(
            session,
            DietaryProfile,
            {"code": p["code"], "tenant_id": None},
            {
                "name": p["name"],
                "icon": p["icon"],
                "description": p["description"],
                "is_system": True,
            },
        )
        profiles[p["code"]] = profile
        if created:
            logger.info("  Created dietary profile: %s", p["name"])
    await session.flush()
    return profiles


async def _seed_cooking_methods(session, tenant: Tenant) -> dict[str, CookingMethod]:
    """Seed system cooking methods (10 per spec)."""
    logger.info("Seeding cooking methods...")
    method_defs = [
        {"code": "grill", "name": "Parrilla", "icon": "flame"},
        {"code": "oven", "name": "Horno", "icon": "oven"},
        {"code": "fryer", "name": "Fritura", "icon": "oil"},
        {"code": "steam", "name": "Vapor", "icon": "cloud"},
        {"code": "raw", "name": "Crudo", "icon": "leaf"},
        {"code": "sous_vide", "name": "Sous vide", "icon": "thermometer"},
        {"code": "smoke", "name": "Ahumado", "icon": "smoke"},
        {"code": "saute", "name": "Salteado", "icon": "pan"},
        {"code": "boil", "name": "Hervido", "icon": "pot"},
        {"code": "roast", "name": "Asado", "icon": "fire"},
    ]
    methods = {}
    for m in method_defs:
        method, created = await _get_or_create(
            session,
            CookingMethod,
            {"code": m["code"], "tenant_id": None},
            {
                "name": m["name"],
                "icon": m["icon"],
                "is_system": True,
            },
        )
        methods[m["name"]] = method
        if created:
            logger.info("  Created cooking method: %s (%s)", m["name"], m["code"])
    await session.flush()
    return methods


async def _seed_flavor_profiles(session, tenant: Tenant) -> dict[str, FlavorProfile]:
    logger.info("Seeding flavor profiles...")
    profile_defs = [
        {"code": "sweet", "name": "Dulce", "icon": "candy"},
        {"code": "salty", "name": "Salado", "icon": "salt"},
        {"code": "sour", "name": "Ácido", "icon": "lemon"},
        {"code": "bitter", "name": "Amargo", "icon": "coffee"},
        {"code": "umami", "name": "Umami", "icon": "soup"},
        {"code": "spicy", "name": "Picante", "icon": "pepper"},
    ]
    profiles = {}
    for p in profile_defs:
        profile, created = await _get_or_create(
            session,
            FlavorProfile,
            {"code": p["code"], "tenant_id": None},
            {
                "name": p["name"],
                "icon": p["icon"],
                "is_system": True,
            },
        )
        profiles[p["name"]] = profile
        if created:
            logger.info("  Created flavor profile: %s (%s)", p["name"], p["code"])
    await session.flush()
    return profiles


async def _seed_texture_profiles(session, tenant: Tenant) -> dict[str, TextureProfile]:
    logger.info("Seeding texture profiles...")
    profile_defs = [
        {"code": "crispy", "name": "Crocante", "icon": "cracker"},
        {"code": "creamy", "name": "Cremoso", "icon": "cream"},
        {"code": "crunchy", "name": "Crujiente", "icon": "chip"},
        {"code": "soft", "name": "Suave", "icon": "cloud"},
        {"code": "chewy", "name": "Chicloso", "icon": "candy"},
        {"code": "liquid", "name": "Líquido", "icon": "droplet"},
    ]
    profiles = {}
    for p in profile_defs:
        profile, created = await _get_or_create(
            session,
            TextureProfile,
            {"code": p["code"], "tenant_id": None},
            {
                "name": p["name"],
                "icon": p["icon"],
                "is_system": True,
            },
        )
        profiles[p["name"]] = profile
        if created:
            logger.info("  Created texture profile: %s (%s)", p["name"], p["code"])
    await session.flush()
    return profiles


async def _seed_cuisine_types(session, tenant: Tenant) -> dict[str, CuisineType]:
    logger.info("Seeding cuisine types...")
    names = ["Argentina", "Italiana", "Japonesa", "Mexicana", "Francesa"]
    types = {}
    for name in names:
        ctype, created = await _get_or_create(
            session, CuisineType, {"tenant_id": tenant.id, "name": name}
        )
        types[name] = ctype
        if created:
            logger.info("  Created cuisine type: %s", name)
    await session.flush()
    return types


async def _seed_badges(session) -> dict[str, Badge]:
    """Seed system badges per spec."""
    logger.info("Seeding badges...")
    badge_defs = [
        {"code": "new", "name": "Nuevo", "color": "#22C55E", "icon": "sparkles"},
        {"code": "best_seller", "name": "Más vendido", "color": "#F59E0B", "icon": "trending-up"},
        {"code": "chef_recommends", "name": "Chef recomienda", "color": "#8B5CF6", "icon": "chef-hat"},
        {"code": "on_sale", "name": "Oferta", "color": "#EF4444", "icon": "tag"},
    ]
    badges = {}
    for b in badge_defs:
        badge, created = await _get_or_create(
            session,
            Badge,
            {"code": b["code"], "tenant_id": None},
            {
                "name": b["name"],
                "color": b["color"],
                "icon": b["icon"],
                "is_system": True,
            },
        )
        badges[b["code"]] = badge
        if created:
            logger.info("  Created badge: %s (%s)", b["name"], b["code"])
    await session.flush()
    return badges


async def _seed_seals(session) -> dict[str, Seal]:
    """Seed system seals per spec."""
    logger.info("Seeding seals...")
    seal_defs = [
        {"code": "organic", "name": "Orgánico", "color": "#16A34A", "icon": "leaf"},
        {"code": "local", "name": "Producto local", "color": "#2563EB", "icon": "map-pin"},
        {"code": "preservative_free", "name": "Sin conservantes", "color": "#D97706", "icon": "shield"},
        {"code": "artisan", "name": "Artesanal", "color": "#9333EA", "icon": "hand"},
        {"code": "sustainable", "name": "Sustentable", "color": "#059669", "icon": "recycle"},
        {"code": "fair_trade", "name": "Comercio justo", "color": "#0891B2", "icon": "handshake"},
    ]
    seals = {}
    for s in seal_defs:
        seal, created = await _get_or_create(
            session,
            Seal,
            {"code": s["code"], "tenant_id": None},
            {
                "name": s["name"],
                "color": s["color"],
                "icon": s["icon"],
                "is_system": True,
            },
        )
        seals[s["code"]] = seal
        if created:
            logger.info("  Created seal: %s (%s)", s["name"], s["code"])
    await session.flush()
    return seals


async def _seed_categories_and_products(
    session,
    tenant: Tenant,
    branch: Branch,
    allergens: dict[str, Allergen],
    cooking_methods: dict[str, CookingMethod],
    flavor_profiles: dict[str, FlavorProfile],
    texture_profiles: dict[str, TextureProfile],
    cuisine_types: dict[str, CuisineType],
    dietary_profiles: dict[str, DietaryProfile],
    badges: dict[str, Badge],
    seals: dict[str, Seal],
) -> None:
    logger.info("Seeding categories, subcategories, products...")

    # Category -> Subcategories -> Products structure
    catalog = {
        "Entradas": {
            "slug": "entradas",
            "subcategories": {
                "Empanadas": {
                    "slug": "empanadas",
                    "products": [
                        {"name": "Empanada de Carne", "slug": "empanada-carne", "price": 850, "prep": 15,
                         "cooking": "Horno", "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": [("gluten", "contains", "moderate"), ("eggs", "contains", "moderate")],
                         "popular": True, "dietary": ["vegetarian"],
                         "badges": ["new"], "seals": ["artisan"],
                         "flavors_array": ["salty", "umami"], "textures_array": ["crispy"]},
                        {"name": "Empanada de Jamón y Queso", "slug": "empanada-jamon-queso", "price": 850, "prep": 15,
                         "cooking": "Horno", "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": [("gluten", "contains", "moderate"), ("dairy", "contains", "moderate")]},
                        {"name": "Empanada de Verdura", "slug": "empanada-verdura", "price": 800, "prep": 15,
                         "cooking": "Horno", "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": [("gluten", "contains", "moderate")],
                         "dietary": ["vegetarian"]},
                    ],
                },
                "Picadas": {
                    "slug": "picadas",
                    "products": [
                        {"name": "Picada para Dos", "slug": "picada-dos", "price": 3500, "prep": 10,
                         "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": [("dairy", "contains", "moderate"), ("gluten", "contains", "moderate"), ("tree_nuts", "may_contain", "low")]},
                        {"name": "Bruschetta Italiana", "slug": "bruschetta-italiana", "price": 2200, "prep": 12,
                         "cooking": "Horno", "flavor": "Salado", "cuisine": "Italiana",
                         "allergens": [("gluten", "contains", "moderate")],
                         "dietary": ["vegetarian"],
                         "seals": ["artisan"]},
                        {"name": "Provoleta", "slug": "provoleta", "price": 2800, "prep": 8,
                         "cooking": "Parrilla", "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": [("dairy", "contains", "moderate")],
                         "dietary": ["vegetarian"],
                         "badges": ["chef_recommends"],
                         "seals": ["local"]},
                    ],
                },
            },
        },
        "Platos Principales": {
            "slug": "platos-principales",
            "subcategories": {
                "Pastas": {
                    "slug": "pastas",
                    "products": [
                        {"name": "Ñoquis con Salsa Bolognesa", "slug": "noquis-bolognesa", "price": 4200, "prep": 25,
                         "cooking": "Hervido", "flavor": "Umami", "texture": "Suave", "cuisine": "Italiana",
                         "allergens": [("gluten", "contains", "severe"), ("eggs", "contains", "moderate"), ("dairy", "contains", "moderate")],
                         "flavors_array": ["umami", "salty"], "textures_array": ["soft"]},
                        {"name": "Ravioles de Ricotta", "slug": "ravioles-ricotta", "price": 4500, "prep": 20,
                         "cooking": "Hervido", "flavor": "Salado", "texture": "Suave", "cuisine": "Italiana",
                         "allergens": [("gluten", "contains", "severe"), ("eggs", "contains", "moderate"), ("dairy", "contains", "moderate")],
                         "dietary": ["vegetarian"], "seals": ["artisan"]},
                        {"name": "Spaghetti al Pesto", "slug": "spaghetti-pesto", "price": 4000, "prep": 18,
                         "cooking": "Hervido", "flavor": "Salado", "cuisine": "Italiana",
                         "allergens": [("gluten", "contains", "severe"), ("tree_nuts", "contains", "moderate"), ("dairy", "contains", "moderate")],
                         "dietary": ["vegetarian"]},
                    ],
                },
                "Carnes": {
                    "slug": "carnes",
                    "products": [
                        {"name": "Bife de Chorizo", "slug": "bife-chorizo", "price": 6500, "prep": 30,
                         "cooking": "Parrilla", "flavor": "Umami", "texture": "Suave", "cuisine": "Argentina",
                         "featured": True, "popular": True, "dietary": ["gluten_free", "dairy_free"],
                         "badges": ["chef_recommends", "best_seller"],
                         "flavors_array": ["umami", "salty"], "textures_array": ["soft"],
                         "ingredients": [
                             {"name": "Bife de chorizo", "quantity": Decimal("400.000"), "unit": "g", "sort_order": 0},
                             {"name": "Sal gruesa", "quantity": Decimal("5.000"), "unit": "g", "sort_order": 1},
                             {"name": "Chimichurri", "quantity": Decimal("2.000"), "unit": "tbsp", "sort_order": 2, "is_optional": True},
                         ]},
                        {"name": "Asado de Tira", "slug": "asado-tira", "price": 5800, "prep": 45,
                         "cooking": "Parrilla", "flavor": "Umami", "texture": "Suave", "cuisine": "Argentina",
                         "dietary": ["gluten_free", "dairy_free"],
                         "seals": ["local"]},
                        {"name": "Milanesa Napolitana", "slug": "milanesa-napolitana", "price": 5200, "prep": 25,
                         "cooking": "Fritura", "flavor": "Salado", "texture": "Crocante", "cuisine": "Argentina",
                         "allergens": [("gluten", "contains", "severe"), ("eggs", "contains", "moderate"), ("dairy", "contains", "moderate")],
                         "featured": True, "popular": True,
                         "badges": ["best_seller"],
                         "flavors_array": ["salty", "umami"], "textures_array": ["crispy", "soft"],
                         "ingredients": [
                             {"name": "Nalga de ternera", "quantity": Decimal("300.000"), "unit": "g", "sort_order": 0},
                             {"name": "Pan rallado", "quantity": Decimal("100.000"), "unit": "g", "sort_order": 1},
                             {"name": "Huevos", "quantity": Decimal("2.000"), "unit": "unit", "sort_order": 2},
                             {"name": "Salsa de tomate", "quantity": Decimal("80.000"), "unit": "ml", "sort_order": 3},
                             {"name": "Mozzarella", "quantity": Decimal("100.000"), "unit": "g", "sort_order": 4},
                             {"name": "Jamón cocido", "quantity": Decimal("50.000"), "unit": "g", "sort_order": 5},
                         ]},
                        {"name": "Pollo al Horno con Hierbas", "slug": "pollo-horno-hierbas", "price": 4800, "prep": 35,
                         "cooking": "Horno", "flavor": "Salado", "cuisine": "Argentina",
                         "dietary": ["gluten_free", "dairy_free"]},
                    ],
                },
                "Pescados": {
                    "slug": "pescados",
                    "products": [
                        {"name": "Salmón Grillado", "slug": "salmon-grillado", "price": 7200, "prep": 20,
                         "cooking": "Parrilla", "flavor": "Umami", "cuisine": "Francesa",
                         "allergens": [("fish", "contains", "severe")],
                         "featured": True, "dietary": ["gluten_free", "dairy_free"],
                         "badges": ["chef_recommends"],
                         "seals": ["sustainable"]},
                        {"name": "Merluza al Limón", "slug": "merluza-limon", "price": 5500, "prep": 20,
                         "cooking": "Horno", "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": [("fish", "contains", "severe")]},
                        {"name": "Ceviche", "slug": "ceviche", "price": 4800, "prep": 15,
                         "cooking": "Crudo", "flavor": "Salado", "cuisine": "Mexicana",
                         "allergens": [("fish", "contains", "severe")],
                         "dietary": ["gluten_free", "dairy_free"]},
                    ],
                },
            },
        },
        "Postres": {
            "slug": "postres",
            "subcategories": {
                "Dulces Clásicos": {
                    "slug": "dulces-clasicos",
                    "products": [
                        {"name": "Tiramisú", "slug": "tiramisu", "price": 3200, "prep": 10,
                         "flavor": "Dulce", "texture": "Cremoso", "cuisine": "Italiana",
                         "allergens": [("gluten", "contains", "moderate"), ("eggs", "contains", "moderate"), ("dairy", "contains", "moderate")],
                         "featured": True,
                         "seals": ["artisan"],
                         "flavors_array": ["sweet", "bitter"], "textures_array": ["creamy", "soft"]},
                        {"name": "Flan Casero", "slug": "flan-casero", "price": 2500, "prep": 5,
                         "flavor": "Dulce", "texture": "Cremoso", "cuisine": "Argentina",
                         "allergens": [("eggs", "contains", "moderate"), ("dairy", "contains", "moderate")],
                         "dietary": ["gluten_free"]},
                        {"name": "Brownie con Helado", "slug": "brownie-helado", "price": 3000, "prep": 8,
                         "cooking": "Horno", "flavor": "Dulce", "texture": "Cremoso", "cuisine": "Argentina",
                         "allergens": [("gluten", "contains", "moderate"), ("eggs", "contains", "moderate"), ("dairy", "contains", "moderate")]},
                    ],
                },
                "Helados y Frutas": {
                    "slug": "helados-frutas",
                    "products": [
                        {"name": "Helado Artesanal (3 bochas)", "slug": "helado-artesanal", "price": 2800, "prep": 3,
                         "flavor": "Dulce", "texture": "Cremoso", "cuisine": "Argentina",
                         "allergens": [("dairy", "contains", "moderate")],
                         "seals": ["artisan"]},
                        {"name": "Ensalada de Frutas", "slug": "ensalada-frutas", "price": 2200, "prep": 5,
                         "flavor": "Dulce", "cuisine": "Argentina",
                         "dietary": ["vegan", "gluten_free", "dairy_free"]},
                        {"name": "Panqueque de Dulce de Leche", "slug": "panqueque-ddl", "price": 2600, "prep": 10,
                         "flavor": "Dulce", "texture": "Suave", "cuisine": "Argentina",
                         "allergens": [("gluten", "contains", "moderate"), ("eggs", "contains", "moderate"), ("dairy", "contains", "moderate")]},
                    ],
                },
            },
        },
        "Bebidas": {
            "slug": "bebidas",
            "subcategories": {
                "Sin Alcohol": {
                    "slug": "sin-alcohol",
                    "products": [
                        {"name": "Agua Mineral 500ml", "slug": "agua-mineral", "price": 800, "prep": 1,
                         "dietary": ["vegan", "gluten_free", "dairy_free"]},
                        {"name": "Gaseosa Línea", "slug": "gaseosa-linea", "price": 1200, "prep": 1},
                        {"name": "Jugo Natural de Naranja", "slug": "jugo-naranja", "price": 1800, "prep": 5,
                         "dietary": ["vegan", "gluten_free", "dairy_free"]},
                        {"name": "Limonada", "slug": "limonada", "price": 1500, "prep": 5,
                         "dietary": ["vegan", "gluten_free", "dairy_free"]},
                    ],
                },
                "Con Alcohol": {
                    "slug": "con-alcohol",
                    "products": [
                        {"name": "Cerveza Artesanal Pinta", "slug": "cerveza-artesanal", "price": 2500, "prep": 2,
                         "allergens": [("gluten", "contains", "moderate")],
                         "seals": ["local"]},
                        {"name": "Vino Malbec Copa", "slug": "vino-malbec-copa", "price": 2800, "prep": 2,
                         "allergens": [("sulfites", "contains", "low")],
                         "seals": ["local"]},
                        {"name": "Fernet con Coca", "slug": "fernet-coca", "price": 2200, "prep": 3},
                    ],
                },
            },
        },
        "Guarniciones": {
            "slug": "guarniciones",
            "subcategories": {
                "Papas": {
                    "slug": "papas",
                    "products": [
                        {"name": "Papas Fritas", "slug": "papas-fritas", "price": 1800, "prep": 12,
                         "cooking": "Fritura", "flavor": "Salado", "texture": "Crocante", "cuisine": "Argentina",
                         "dietary": ["vegan", "gluten_free", "dairy_free"],
                         "flavors_array": ["salty"], "textures_array": ["crispy", "crunchy"]},
                        {"name": "Puré de Papas", "slug": "pure-papas", "price": 1500, "prep": 15,
                         "cooking": "Hervido", "flavor": "Salado", "texture": "Cremoso", "cuisine": "Argentina",
                         "allergens": [("dairy", "contains", "low")],
                         "dietary": ["vegetarian", "gluten_free"]},
                        {"name": "Papas al Horno", "slug": "papas-horno", "price": 1600, "prep": 20,
                         "cooking": "Horno", "flavor": "Salado", "cuisine": "Argentina",
                         "dietary": ["vegan", "gluten_free", "dairy_free"]},
                    ],
                },
                "Ensaladas": {
                    "slug": "ensaladas",
                    "products": [
                        {"name": "Ensalada Mixta", "slug": "ensalada-mixta", "price": 1500, "prep": 5,
                         "cooking": "Crudo", "flavor": "Salado", "cuisine": "Argentina",
                         "dietary": ["vegan", "gluten_free", "dairy_free"]},
                        {"name": "Ensalada César", "slug": "ensalada-cesar", "price": 2200, "prep": 8,
                         "cooking": "Crudo", "flavor": "Salado", "cuisine": "Italiana",
                         "allergens": [("gluten", "contains", "moderate"), ("eggs", "contains", "moderate"), ("dairy", "contains", "moderate"), ("fish", "may_contain", "low")]},
                        {"name": "Verduras Grilladas", "slug": "verduras-grilladas", "price": 1800, "prep": 15,
                         "cooking": "Parrilla", "flavor": "Salado", "cuisine": "Argentina",
                         "dietary": ["vegan", "gluten_free", "dairy_free"],
                         "seals": ["organic"]},
                    ],
                },
            },
        },
    }

    # Icon mapping per category
    cat_icons = {
        "Entradas": "utensils",
        "Platos Principales": "beef",
        "Postres": "cake",
        "Bebidas": "wine",
        "Guarniciones": "salad",
    }

    for display_order, (cat_name, cat_data) in enumerate(catalog.items()):
        category, cat_created = await _get_or_create(
            session,
            Category,
            {"tenant_id": tenant.id, "slug": cat_data["slug"]},
            {
                "name": cat_name,
                "branch_id": branch.id,
                "icon": cat_icons.get(cat_name),
                "display_order": display_order,
                "is_home": display_order == 0,
            },
        )
        if cat_created:
            await session.flush()
            logger.info("  Created category: %s", cat_name)

        for sub_order, (sub_name, sub_data) in enumerate(cat_data["subcategories"].items()):
            subcategory, sub_created = await _get_or_create(
                session,
                Subcategory,
                {"category_id": category.id, "slug": sub_data["slug"]},
                {"name": sub_name, "display_order": sub_order},
            )
            if sub_created:
                await session.flush()
                logger.info("    Created subcategory: %s", sub_name)

            for p in sub_data["products"]:
                product_defaults = {
                    "name": p["name"],
                    "base_price_cents": p["price"],
                    "prep_time_minutes": p.get("prep"),
                    "subcategory_id": subcategory.id,
                    "is_featured": p.get("featured", False),
                    "is_popular": p.get("popular", False),
                }

                # ARRAY columns for flavor/texture
                if "flavors_array" in p:
                    product_defaults["flavor_profiles_array"] = p["flavors_array"]
                if "textures_array" in p:
                    product_defaults["texture_profiles_array"] = p["textures_array"]

                # Assign legacy FK profiles if provided
                if "cooking" in p and p["cooking"] in cooking_methods:
                    product_defaults["cooking_method_id"] = cooking_methods[p["cooking"]].id
                if "flavor" in p and p["flavor"] in flavor_profiles:
                    product_defaults["flavor_profile_id"] = flavor_profiles[p["flavor"]].id
                if "texture" in p and p["texture"] in texture_profiles:
                    product_defaults["texture_profile_id"] = texture_profiles[p["texture"]].id
                if "cuisine" in p and p["cuisine"] in cuisine_types:
                    product_defaults["cuisine_type_id"] = cuisine_types[p["cuisine"]].id

                product, prod_created = await _get_or_create(
                    session,
                    Product,
                    {"tenant_id": tenant.id, "slug": p["slug"]},
                    product_defaults,
                )
                if prod_created:
                    await session.flush()
                    logger.info("      Created product: %s ($%.2f)", p["name"], p["price"] / 100)

                # Create BranchProduct (make product available in branch)
                await _get_or_create(
                    session,
                    BranchProduct,
                    {"branch_id": branch.id, "product_id": product.id},
                )

                # Create ProductAllergen associations (new format with presence_type + risk_level)
                for allergen_entry in p.get("allergens", []):
                    if isinstance(allergen_entry, tuple):
                        allergen_code, presence_type, risk_level = allergen_entry
                    else:
                        allergen_code = allergen_entry
                        presence_type = "contains"
                        risk_level = "moderate"

                    if allergen_code in allergens:
                        await _get_or_create(
                            session,
                            ProductAllergen,
                            {"product_id": product.id, "allergen_id": allergens[allergen_code].id},
                            {"presence_type": presence_type, "risk_level": risk_level},
                        )

                # Create ProductCookingMethod junction
                if "cooking" in p and p["cooking"] in cooking_methods:
                    await _get_or_create(
                        session,
                        ProductCookingMethod,
                        {"product_id": product.id, "cooking_method_id": cooking_methods[p["cooking"]].id},
                    )

                # Create ProductDietaryProfile junctions
                for dp_code in p.get("dietary", []):
                    if dp_code in dietary_profiles:
                        await _get_or_create(
                            session,
                            ProductDietaryProfile,
                            {"product_id": product.id, "dietary_profile_id": dietary_profiles[dp_code].id},
                        )

                # Create ProductBadge junctions
                for badge_idx, badge_code in enumerate(p.get("badges", [])):
                    if badge_code in badges:
                        await _get_or_create(
                            session,
                            ProductBadge,
                            {"product_id": product.id, "badge_id": badges[badge_code].id},
                            {"sort_order": badge_idx},
                        )

                # Create ProductSeal junctions
                for seal_idx, seal_code in enumerate(p.get("seals", [])):
                    if seal_code in seals:
                        await _get_or_create(
                            session,
                            ProductSeal,
                            {"product_id": product.id, "seal_id": seals[seal_code].id},
                            {"sort_order": seal_idx},
                        )

                # Create ProductIngredient entries
                for ing in p.get("ingredients", []):
                    await _get_or_create(
                        session,
                        ProductIngredient,
                        {"product_id": product.id, "sort_order": ing["sort_order"]},
                        {
                            "name": ing["name"],
                            "quantity": ing["quantity"],
                            "unit": ing["unit"],
                            "is_optional": ing.get("is_optional", False),
                        },
                    )

    await session.flush()


# ── Main entry point ────────────────────────────────────────────────────


async def run_seed() -> None:
    """Execute the full seed pipeline. Idempotent — safe to call multiple times."""
    logger.info("=" * 60)
    logger.info("Starting seed data pipeline...")
    logger.info("=" * 60)

    async with async_session_factory() as session, session.begin():
        tenant = await _seed_tenant(session)
        branch = await _seed_branch(session, tenant)
        sectors = await _seed_sectors(session, branch)
        await _seed_tables(session, sectors)
        await _seed_users(session, tenant, branch)
        allergens = await _seed_allergens(session)
        await _seed_cross_reactions(session, allergens)
        dietary_profiles = await _seed_dietary_profiles(session)
        cooking_methods = await _seed_cooking_methods(session, tenant)
        flavor_profiles = await _seed_flavor_profiles(session, tenant)
        texture_profiles = await _seed_texture_profiles(session, tenant)
        cuisine_types = await _seed_cuisine_types(session, tenant)
        badges = await _seed_badges(session)
        seals = await _seed_seals(session)
        await _seed_categories_and_products(
            session,
            tenant,
            branch,
            allergens,
            cooking_methods,
            flavor_profiles,
            texture_profiles,
            cuisine_types,
            dietary_profiles,
            badges,
            seals,
        )

    logger.info("=" * 60)
    logger.info("Seed data pipeline completed successfully!")
    logger.info("=" * 60)


# ── Standalone execution ────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    asyncio.run(run_seed())
