/**
 * Types for the allergen catalog — fetched once per session from the backend.
 * Used to build the bidirectional cross-reaction map for very_strict filtering.
 */

export interface AllergenCatalogItem {
  readonly id: string;
  readonly slug: string;
  readonly name: string;
  /** Array of allergen slugs that cross-react with this allergen */
  readonly crossReacts: CrossReactionItem[];
}

export interface CrossReactionItem {
  readonly allergenId: string;
  readonly allergenSlug: string;
  readonly allergenName: string;
  readonly riskLevel: 'low' | 'medium' | 'high';
}
