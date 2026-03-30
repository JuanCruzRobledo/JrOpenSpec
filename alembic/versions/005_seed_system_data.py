"""Seed system catalog data: allergens, cross-reactions, dietary profiles, cooking methods, badges, seals.

All inserts are idempotent:
- allergens, dietary_profiles, cooking_methods, badges, seals use WHERE NOT EXISTS
  (ON CONFLICT cannot be used because NULL != NULL in PostgreSQL unique indexes)
- allergen_cross_reactions use ON CONFLICT DO NOTHING with LEAST/GREATEST to enforce
  the CHECK (allergen_id < related_allergen_id) constraint without hardcoding IDs

Revision ID: 005
Revises: 004
Create Date: 2026-03-30
"""

from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════════
    # 1. Allergens — 14 EU mandatory allergens
    # Uses WHERE NOT EXISTS because UNIQUE(code, tenant_id) with tenant_id IS NULL
    # cannot use ON CONFLICT — PostgreSQL treats NULL != NULL in unique indexes.
    # ═══════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'gluten', 'Gluten', 'Cereales con gluten: trigo, centeno, cebada, avena, espelta, kamut', 'wheat', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'gluten' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'dairy', 'Lácteos', 'Leche y derivados incluyendo lactosa y caseína', 'milk', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'dairy' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'eggs', 'Huevos', 'Huevos y productos derivados', 'egg', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'eggs' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'fish', 'Pescado', 'Pescado y productos derivados', 'fish', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'fish' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'crustaceans', 'Crustáceos', 'Crustáceos y productos derivados', 'shrimp', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'crustaceans' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'tree_nuts', 'Frutos secos', 'Almendras, avellanas, nueces, anacardos, pecanas, pistachos, etc.', 'nut', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'tree_nuts' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'soy', 'Soja', 'Soja y productos derivados', 'soybean', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'soy' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'celery', 'Apio', 'Apio y productos derivados', 'celery', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'celery' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'mustard', 'Mostaza', 'Mostaza y productos derivados', 'mustard', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'mustard' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'sesame', 'Sésamo', 'Granos de sésamo y productos derivados', 'sesame', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'sesame' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'sulfites', 'Sulfitos', 'Dióxido de azufre y sulfitos (>10mg/kg)', 'sulfite', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'sulfites' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'lupins', 'Altramuces', 'Altramuces y productos derivados', 'lupin', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'lupins' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'mollusks', 'Moluscos', 'Moluscos y productos derivados', 'shell', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'mollusks' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO allergens (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'peanuts', 'Cacahuetes', 'Cacahuetes/maní y productos derivados', 'peanut', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM allergens WHERE code = 'peanuts' AND is_system = TRUE)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # 2. Allergen cross-reactions — 6 known pairs
    # Uses LEAST/GREATEST subselects to enforce allergen_id < related_allergen_id
    # (required by CHECK constraint) without hardcoding IDs.
    # ON CONFLICT DO NOTHING is safe here because the unique key is (allergen_id, related_allergen_id)
    # and both columns are NOT NULL integers.
    # ═══════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO allergen_cross_reactions (allergen_id, related_allergen_id, description, severity, created_at)
        SELECT
            LEAST(a1.id, a2.id),
            GREATEST(a1.id, a2.id),
            'Sensibilidad cruzada por profilinas — proteínas comunes en cereales y apio',
            'moderate',
            NOW()
        FROM allergens a1, allergens a2
        WHERE a1.code = 'gluten' AND a1.is_system = TRUE
          AND a2.code = 'celery' AND a2.is_system = TRUE
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO allergen_cross_reactions (allergen_id, related_allergen_id, description, severity, created_at)
        SELECT
            LEAST(a1.id, a2.id),
            GREATEST(a1.id, a2.id),
            'Proteínas de soja pueden causar reacción en alérgicos a caseína',
            'moderate',
            NOW()
        FROM allergens a1, allergens a2
        WHERE a1.code = 'dairy' AND a1.is_system = TRUE
          AND a2.code = 'soy' AND a2.is_system = TRUE
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO allergen_cross_reactions (allergen_id, related_allergen_id, description, severity, created_at)
        SELECT
            LEAST(a1.id, a2.id),
            GREATEST(a1.id, a2.id),
            'Reactividad cruzada por parvalbúmina en pescado y tropomiosina en crustáceos',
            'moderate',
            NOW()
        FROM allergens a1, allergens a2
        WHERE a1.code = 'fish' AND a1.is_system = TRUE
          AND a2.code = 'crustaceans' AND a2.is_system = TRUE
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO allergen_cross_reactions (allergen_id, related_allergen_id, description, severity, created_at)
        SELECT
            LEAST(a1.id, a2.id),
            GREATEST(a1.id, a2.id),
            'Proteínas de almacenamiento similares entre maní y frutos secos',
            'severe',
            NOW()
        FROM allergens a1, allergens a2
        WHERE a1.code = 'peanuts' AND a1.is_system = TRUE
          AND a2.code = 'tree_nuts' AND a2.is_system = TRUE
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO allergen_cross_reactions (allergen_id, related_allergen_id, description, severity, created_at)
        SELECT
            LEAST(a1.id, a2.id),
            GREATEST(a1.id, a2.id),
            'Ambos son leguminosas con proteínas vicilina/legumina compartidas',
            'moderate',
            NOW()
        FROM allergens a1, allergens a2
        WHERE a1.code = 'peanuts' AND a1.is_system = TRUE
          AND a2.code = 'soy' AND a2.is_system = TRUE
        ON CONFLICT DO NOTHING
    """)

    op.execute("""
        INSERT INTO allergen_cross_reactions (allergen_id, related_allergen_id, description, severity, created_at)
        SELECT
            LEAST(a1.id, a2.id),
            GREATEST(a1.id, a2.id),
            'Ambos son leguminosas con alta reactividad cruzada por conglutinas',
            'severe',
            NOW()
        FROM allergens a1, allergens a2
        WHERE a1.code = 'lupins' AND a1.is_system = TRUE
          AND a2.code = 'peanuts' AND a2.is_system = TRUE
        ON CONFLICT DO NOTHING
    """)

    # ═══════════════════════════════════════════════════════════════════
    # 3. Dietary profiles — 7 system profiles
    # ═══════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO dietary_profiles (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'vegetarian', 'Vegetariano', 'Sin carne ni pescado', 'leaf', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM dietary_profiles WHERE code = 'vegetarian' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO dietary_profiles (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'vegan', 'Vegano', 'Sin productos de origen animal', 'sprout', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM dietary_profiles WHERE code = 'vegan' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO dietary_profiles (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'gluten_free', 'Sin gluten', 'Apto para celíacos', 'wheat-off', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM dietary_profiles WHERE code = 'gluten_free' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO dietary_profiles (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'dairy_free', 'Sin lácteos', 'Sin leche ni derivados', 'milk-off', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM dietary_profiles WHERE code = 'dairy_free' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO dietary_profiles (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'celiac_safe', 'Apto celíacos', 'Certificado sin TACC', 'shield-check', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM dietary_profiles WHERE code = 'celiac_safe' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO dietary_profiles (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'keto', 'Keto', 'Bajo en carbohidratos, alto en grasas', 'flame', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM dietary_profiles WHERE code = 'keto' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO dietary_profiles (code, name, description, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'low_sodium', 'Bajo sodio', 'Reducido en sal', 'salt-off', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM dietary_profiles WHERE code = 'low_sodium' AND is_system = TRUE)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # 4. Cooking methods — 10 system methods
    # ═══════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'grill', 'Parrilla', 'flame', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'grill' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'oven', 'Horno', 'oven', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'oven' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'fryer', 'Fritura', 'oil', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'fryer' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'steam', 'Vapor', 'cloud', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'steam' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'raw', 'Crudo', 'leaf', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'raw' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'sous_vide', 'Sous vide', 'thermometer', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'sous_vide' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'smoke', 'Ahumado', 'smoke', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'smoke' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'saute', 'Salteado', 'pan', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'saute' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'boil', 'Hervido', 'pot', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'boil' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO cooking_methods (code, name, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'roast', 'Asado', 'fire', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM cooking_methods WHERE code = 'roast' AND is_system = TRUE)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # 5. Badges — 4 system badges
    # ═══════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO badges (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'new', 'Nuevo', '#22C55E', 'sparkles', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM badges WHERE code = 'new' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO badges (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'best_seller', 'Más vendido', '#F59E0B', 'trending-up', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM badges WHERE code = 'best_seller' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO badges (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'chef_recommends', 'Chef recomienda', '#8B5CF6', 'chef-hat', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM badges WHERE code = 'chef_recommends' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO badges (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'on_sale', 'Oferta', '#EF4444', 'tag', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM badges WHERE code = 'on_sale' AND is_system = TRUE)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # 6. Seals — 6 system seals
    # ═══════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO seals (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'organic', 'Orgánico', '#16A34A', 'leaf', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM seals WHERE code = 'organic' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO seals (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'local', 'Producto local', '#2563EB', 'map-pin', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM seals WHERE code = 'local' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO seals (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'preservative_free', 'Sin conservantes', '#D97706', 'shield', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM seals WHERE code = 'preservative_free' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO seals (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'artisan', 'Artesanal', '#9333EA', 'hand', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM seals WHERE code = 'artisan' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO seals (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'sustainable', 'Sustentable', '#059669', 'recycle', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM seals WHERE code = 'sustainable' AND is_system = TRUE)
    """)

    op.execute("""
        INSERT INTO seals (code, name, color, icon, is_system, tenant_id, created_at, updated_at)
        SELECT 'fair_trade', 'Comercio justo', '#0891B2', 'handshake', TRUE, NULL, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM seals WHERE code = 'fair_trade' AND is_system = TRUE)
    """)


def downgrade() -> None:
    # Cross-reactions first — FK dependency on allergens
    op.execute("""
        DELETE FROM allergen_cross_reactions
        WHERE allergen_id IN (SELECT id FROM allergens WHERE is_system = TRUE)
    """)

    op.execute("DELETE FROM allergens WHERE is_system = TRUE")
    op.execute("DELETE FROM dietary_profiles WHERE is_system = TRUE")
    op.execute("DELETE FROM cooking_methods WHERE is_system = TRUE")
    op.execute("DELETE FROM badges WHERE is_system = TRUE")
    op.execute("DELETE FROM seals WHERE is_system = TRUE")
