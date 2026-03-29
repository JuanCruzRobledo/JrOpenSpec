/**
 * Filter state types for the allergen/dietary/cooking filter system.
 */

/**
 * Allergen filter mode:
 * - 'off': no allergen filtering active
 * - 'strict': hide products that CONTAIN selected allergens
 * - 'very_strict': hide products that CONTAIN or MAY_CONTAIN selected allergens
 *                  AND expand to cross-reactions
 */
export type AllergenMode = 'off' | 'strict' | 'very_strict';

export interface FilterState {
  /** Free text search query */
  searchQuery: string;
  /** How to apply allergen filters */
  allergenMode: AllergenMode;
  /** Allergen slugs the user has selected */
  selectedAllergens: string[];
  /** Dietary profile slugs selected (AND logic — product must match ALL) */
  selectedDietary: string[];
  /** Cooking method slugs selected (OR logic — product must match at least one) */
  selectedCooking: string[];
}
