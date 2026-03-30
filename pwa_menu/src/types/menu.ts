/**
 * Types for the public menu API response.
 * Maps to GET /api/public/menu/{slug}
 *
 * IDs: backend BigInteger → frontend string (per CLAUDE.md conventions)
 * Prices: backend centavos integer → display via formatPrice()
 */

export interface MenuResponse {
  readonly branch: BranchInfo;
  readonly categories: MenuCategory[];
  /** ISO 8601 timestamp of when the backend generated this response */
  readonly generatedAt: string;
}

export interface BranchInfo {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly tenantSlug: string;
  readonly logoUrl: string | null;
  readonly address: string | null;
  readonly phone: string | null;
}

export interface MenuCategory {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly displayOrder: number;
  readonly subcategories: MenuSubcategory[];
}

export interface MenuSubcategory {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly displayOrder: number;
  readonly products: MenuProduct[];
}

export interface MenuProduct {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly description: string | null;
  readonly imageUrl: string | null;
  /** Price in centavos — use formatPrice() for display */
  readonly priceCents: number;
  readonly isAvailable: boolean;
  readonly badges: Badge[];
  readonly seals: Seal[];
  /** Top-level allergen slugs for quick filtering (no detail — use ProductDetail for full info) */
  readonly allergenSlugs: string[];
  /** Top-level may-contain allergen slugs for very_strict quick filtering */
  readonly mayContainSlugs: string[];
  /** Dietary profile slugs for quick filtering */
  readonly dietaryProfileSlugs: string[];
  /** Cooking method slugs for quick filtering */
  readonly cookingMethodSlugs: string[];
}

export interface Badge {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly colorHex: string;
  readonly iconName: string | null;
}

export interface Seal {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly imageUrl: string | null;
  readonly description: string | null;
}
