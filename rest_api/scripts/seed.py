"""Idempotent seed script for development environment.

Creates sample data: tenant, branch, sectors, tables, users, allergens,
profiles, categories, subcategories, products, branch_products, product_allergens.

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

from passlib.context import CryptContext
from shared.infrastructure.db import async_session_factory
from shared.models.catalog.allergen import Allergen
from shared.models.catalog.branch_product import BranchProduct
from shared.models.catalog.category import Category
from shared.models.catalog.product import Product
from shared.models.catalog.product_allergen import ProductAllergen
from shared.models.catalog.subcategory import Subcategory
from shared.models.core.branch import Branch
from shared.models.core.tenant import Tenant
from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
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
    logger.info("Seeding allergens (14 EU)...")
    allergen_defs = [
        {"name": "Gluten", "code": "gluten"},
        {"name": "Crustaceans", "code": "crustaceans"},
        {"name": "Eggs", "code": "eggs"},
        {"name": "Fish", "code": "fish"},
        {"name": "Peanuts", "code": "peanuts"},
        {"name": "Soybeans", "code": "soybeans"},
        {"name": "Milk", "code": "milk"},
        {"name": "Tree Nuts", "code": "tree_nuts"},
        {"name": "Celery", "code": "celery"},
        {"name": "Mustard", "code": "mustard"},
        {"name": "Sesame", "code": "sesame"},
        {"name": "Sulphites", "code": "sulphites"},
        {"name": "Lupin", "code": "lupin"},
        {"name": "Molluscs", "code": "molluscs"},
    ]
    allergens = {}
    for a in allergen_defs:
        allergen, created = await _get_or_create(session, Allergen, {"code": a["code"]}, {"name": a["name"]})
        allergens[a["code"]] = allergen
        if created:
            logger.info("  Created allergen: %s", a["name"])
    await session.flush()
    return allergens


async def _seed_cooking_methods(session, tenant: Tenant) -> dict[str, CookingMethod]:
    logger.info("Seeding cooking methods...")
    names = ["A la parrilla", "Frito", "Al horno", "Hervido", "Salteado", "Crudo"]
    methods = {}
    for name in names:
        method, created = await _get_or_create(
            session, CookingMethod, {"tenant_id": tenant.id, "name": name}
        )
        methods[name] = method
        if created:
            logger.info("  Created cooking method: %s", name)
    await session.flush()
    return methods


async def _seed_flavor_profiles(session, tenant: Tenant) -> dict[str, FlavorProfile]:
    logger.info("Seeding flavor profiles...")
    names = ["Dulce", "Salado", "Ácido", "Amargo", "Umami", "Picante"]
    profiles = {}
    for name in names:
        profile, created = await _get_or_create(
            session, FlavorProfile, {"tenant_id": tenant.id, "name": name}
        )
        profiles[name] = profile
        if created:
            logger.info("  Created flavor profile: %s", name)
    await session.flush()
    return profiles


async def _seed_texture_profiles(session, tenant: Tenant) -> dict[str, TextureProfile]:
    logger.info("Seeding texture profiles...")
    names = ["Crocante", "Cremoso", "Suave", "Firme", "Esponjoso"]
    profiles = {}
    for name in names:
        profile, created = await _get_or_create(
            session, TextureProfile, {"tenant_id": tenant.id, "name": name}
        )
        profiles[name] = profile
        if created:
            logger.info("  Created texture profile: %s", name)
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


async def _seed_categories_and_products(
    session,
    tenant: Tenant,
    branch: Branch,
    allergens: dict[str, Allergen],
    cooking_methods: dict[str, CookingMethod],
    flavor_profiles: dict[str, FlavorProfile],
    texture_profiles: dict[str, TextureProfile],
    cuisine_types: dict[str, CuisineType],
) -> None:
    logger.info("Seeding categories, subcategories, products...")

    # Category → Subcategories → Products structure
    catalog = {
        "Entradas": {
            "slug": "entradas",
            "subcategories": {
                "Empanadas": {
                    "slug": "empanadas",
                    "products": [
                        {"name": "Empanada de Carne", "slug": "empanada-carne", "price": 850, "prep": 15,
                         "cooking": "Al horno", "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": ["gluten", "eggs"], "popular": True},
                        {"name": "Empanada de Jamón y Queso", "slug": "empanada-jamon-queso", "price": 850, "prep": 15,
                         "cooking": "Al horno", "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": ["gluten", "milk"]},
                        {"name": "Empanada de Verdura", "slug": "empanada-verdura", "price": 800, "prep": 15,
                         "cooking": "Al horno", "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": ["gluten"]},
                    ],
                },
                "Picadas": {
                    "slug": "picadas",
                    "products": [
                        {"name": "Picada para Dos", "slug": "picada-dos", "price": 3500, "prep": 10,
                         "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": ["milk", "gluten", "tree_nuts"]},
                        {"name": "Bruschetta Italiana", "slug": "bruschetta-italiana", "price": 2200, "prep": 12,
                         "cooking": "Al horno", "flavor": "Salado", "cuisine": "Italiana",
                         "allergens": ["gluten"]},
                        {"name": "Provoleta", "slug": "provoleta", "price": 2800, "prep": 8,
                         "cooking": "A la parrilla", "flavor": "Salado", "cuisine": "Argentina",
                         "allergens": ["milk"]},
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
                         "allergens": ["gluten", "eggs", "milk"]},
                        {"name": "Ravioles de Ricotta", "slug": "ravioles-ricotta", "price": 4500, "prep": 20,
                         "cooking": "Hervido", "flavor": "Salado", "texture": "Suave", "cuisine": "Italiana",
                         "allergens": ["gluten", "eggs", "milk"]},
                        {"name": "Spaghetti al Pesto", "slug": "spaghetti-pesto", "price": 4000, "prep": 18,
                         "cooking": "Hervido", "flavor": "Salado", "cuisine": "Italiana",
                         "allergens": ["gluten", "tree_nuts", "milk"]},
                    ],
                },
                "Carnes": {
                    "slug": "carnes",
                    "products": [
                        {"name": "Bife de Chorizo", "slug": "bife-chorizo", "price": 6500, "prep": 30,
                         "cooking": "A la parrilla", "flavor": "Umami", "texture": "Firme", "cuisine": "Argentina",
                         "featured": True, "popular": True},
                        {"name": "Asado de Tira", "slug": "asado-tira", "price": 5800, "prep": 45,
                         "cooking": "A la parrilla", "flavor": "Umami", "texture": "Firme", "cuisine": "Argentina"},
                        {"name": "Milanesa Napolitana", "slug": "milanesa-napolitana", "price": 5200, "prep": 25,
                         "cooking": "Frito", "flavor": "Salado", "texture": "Crocante", "cuisine": "Argentina",
                         "allergens": ["gluten", "eggs", "milk"], "featured": True, "popular": True},
                        {"name": "Pollo al Horno con Hierbas", "slug": "pollo-horno-hierbas", "price": 4800, "prep": 35,
                         "cooking": "Al horno", "flavor": "Salado", "cuisine": "Argentina"},
                    ],
                },
                "Pescados": {
                    "slug": "pescados",
                    "products": [
                        {"name": "Salmón Grillado", "slug": "salmon-grillado", "price": 7200, "prep": 20,
                         "cooking": "A la parrilla", "flavor": "Umami", "cuisine": "Francesa",
                         "allergens": ["fish"], "featured": True},
                        {"name": "Merluza al Limón", "slug": "merluza-limon", "price": 5500, "prep": 20,
                         "cooking": "Al horno", "flavor": "Ácido", "cuisine": "Argentina",
                         "allergens": ["fish"]},
                        {"name": "Ceviche", "slug": "ceviche", "price": 4800, "prep": 15,
                         "cooking": "Crudo", "flavor": "Ácido", "cuisine": "Mexicana",
                         "allergens": ["fish"]},
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
                         "allergens": ["gluten", "eggs", "milk"], "featured": True},
                        {"name": "Flan Casero", "slug": "flan-casero", "price": 2500, "prep": 5,
                         "flavor": "Dulce", "texture": "Cremoso", "cuisine": "Argentina",
                         "allergens": ["eggs", "milk"]},
                        {"name": "Brownie con Helado", "slug": "brownie-helado", "price": 3000, "prep": 8,
                         "cooking": "Al horno", "flavor": "Dulce", "texture": "Esponjoso", "cuisine": "Argentina",
                         "allergens": ["gluten", "eggs", "milk"]},
                    ],
                },
                "Helados y Frutas": {
                    "slug": "helados-frutas",
                    "products": [
                        {"name": "Helado Artesanal (3 bochas)", "slug": "helado-artesanal", "price": 2800, "prep": 3,
                         "flavor": "Dulce", "texture": "Cremoso", "cuisine": "Argentina",
                         "allergens": ["milk"]},
                        {"name": "Ensalada de Frutas", "slug": "ensalada-frutas", "price": 2200, "prep": 5,
                         "flavor": "Dulce", "cuisine": "Argentina"},
                        {"name": "Panqueque de Dulce de Leche", "slug": "panqueque-ddl", "price": 2600, "prep": 10,
                         "flavor": "Dulce", "texture": "Suave", "cuisine": "Argentina",
                         "allergens": ["gluten", "eggs", "milk"]},
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
                        {"name": "Agua Mineral 500ml", "slug": "agua-mineral", "price": 800, "prep": 1},
                        {"name": "Gaseosa Línea", "slug": "gaseosa-linea", "price": 1200, "prep": 1},
                        {"name": "Jugo Natural de Naranja", "slug": "jugo-naranja", "price": 1800, "prep": 5},
                        {"name": "Limonada", "slug": "limonada", "price": 1500, "prep": 5},
                    ],
                },
                "Con Alcohol": {
                    "slug": "con-alcohol",
                    "products": [
                        {"name": "Cerveza Artesanal Pinta", "slug": "cerveza-artesanal", "price": 2500, "prep": 2,
                         "allergens": ["gluten"]},
                        {"name": "Vino Malbec Copa", "slug": "vino-malbec-copa", "price": 2800, "prep": 2,
                         "allergens": ["sulphites"]},
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
                         "cooking": "Frito", "flavor": "Salado", "texture": "Crocante", "cuisine": "Argentina"},
                        {"name": "Puré de Papas", "slug": "pure-papas", "price": 1500, "prep": 15,
                         "cooking": "Hervido", "flavor": "Salado", "texture": "Cremoso", "cuisine": "Argentina",
                         "allergens": ["milk"]},
                        {"name": "Papas al Horno", "slug": "papas-horno", "price": 1600, "prep": 20,
                         "cooking": "Al horno", "flavor": "Salado", "cuisine": "Argentina"},
                    ],
                },
                "Ensaladas": {
                    "slug": "ensaladas",
                    "products": [
                        {"name": "Ensalada Mixta", "slug": "ensalada-mixta", "price": 1500, "prep": 5,
                         "cooking": "Crudo", "flavor": "Ácido", "cuisine": "Argentina"},
                        {"name": "Ensalada César", "slug": "ensalada-cesar", "price": 2200, "prep": 8,
                         "cooking": "Crudo", "flavor": "Salado", "cuisine": "Italiana",
                         "allergens": ["gluten", "eggs", "milk", "fish"]},
                        {"name": "Verduras Grilladas", "slug": "verduras-grilladas", "price": 1800, "prep": 15,
                         "cooking": "A la parrilla", "flavor": "Salado", "cuisine": "Argentina"},
                    ],
                },
            },
        },
    }

    # Icon mapping per category
    cat_icons = {
        "Entradas": "🥟",
        "Platos Principales": "🥩",
        "Postres": "🍰",
        "Bebidas": "🍷",
        "Guarniciones": "🥗",
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
                "is_home": display_order == 0,  # First category is home
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

                # Assign profile FKs if provided
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

                # Create ProductAllergen associations
                for allergen_code in p.get("allergens", []):
                    if allergen_code in allergens:
                        await _get_or_create(
                            session,
                            ProductAllergen,
                            {"product_id": product.id, "allergen_id": allergens[allergen_code].id},
                            {"severity": "contains"},
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
        cooking_methods = await _seed_cooking_methods(session, tenant)
        flavor_profiles = await _seed_flavor_profiles(session, tenant)
        texture_profiles = await _seed_texture_profiles(session, tenant)
        cuisine_types = await _seed_cuisine_types(session, tenant)
        await _seed_categories_and_products(
            session,
            tenant,
            branch,
            allergens,
            cooking_methods,
            flavor_profiles,
            texture_profiles,
            cuisine_types,
        )

    logger.info("=" * 60)
    logger.info("Seed data pipeline completed successfully!")
    logger.info("=" * 60)


# ── Standalone execution ────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    asyncio.run(run_seed())
