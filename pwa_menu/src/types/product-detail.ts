/**
 * Types for the product detail API response.
 * Maps to GET /api/public/menu/{slug}/product/{id}
 *
 * This is the full product view including allergen details, cross-reactions,
 * dietary profiles, cooking methods, ingredients, and flavor/texture.
 */

/** Presence type for an allergen in a product */
export type AllergenPresence = 'contains' | 'may_contain' | 'free';
export type AllergenRiskLevel = 'low' | 'medium' | 'high';

export interface ProductDetail {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly description: string | null;
  readonly imageUrls: string[];
  /** Price in centavos — use formatPrice() for display */
  readonly priceCents: number;
  readonly isAvailable: boolean;
  readonly categoryName: string;
  readonly subcategoryName: string;
  readonly allergens: ProductAllergenDetail[];
  readonly dietaryProfiles: DietaryProfileInfo[];
  readonly cookingMethods: CookingMethodInfo[];
  readonly ingredients: Ingredient[];
  /** Flavor profile descriptors, e.g. ["dulce", "ácido"] */
  readonly flavorProfiles: string[];
  /** Texture descriptors, e.g. ["crujiente", "cremoso"] */
  readonly textureProfiles: string[];
  readonly preparationTime: number | null; // minutes
  readonly portionSize: string | null;
  readonly calories: number | null;
}

export interface ProductAllergenDetail {
  readonly allergenId: string;
  readonly allergenSlug: string;
  readonly allergenName: string;
  readonly icon?: string | null;
  readonly presence: AllergenPresence;
  readonly riskLevel?: AllergenRiskLevel;
  readonly notes?: string | null;
  readonly crossReactions: CrossReaction[];
}

export interface CrossReaction {
  readonly allergenId: string;
  readonly allergenSlug: string;
  readonly allergenName: string;
  /** Risk level for this cross-reaction */
  readonly riskLevel: AllergenRiskLevel;
}

export interface DietaryProfileInfo {
  readonly id: string;
  readonly slug: string;
  readonly name: string;
  readonly iconName: string | null;
}

export interface CookingMethodInfo {
  readonly id: string;
  readonly slug: string;
  readonly name: string;
}

export interface Ingredient {
  readonly id: string;
  readonly name: string;
  readonly isOptional: boolean;
  readonly quantity?: number | null;
  readonly unit?: string | null;
  readonly allergenSlugs: string[];
}
