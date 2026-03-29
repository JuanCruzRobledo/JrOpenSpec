import { create } from 'zustand';
import type { AllergenCatalogItem } from '@/types/allergen-catalog';
import type { ApiError } from '@/types/api';
import { ALLERGEN_CACHE_TTL_MS } from '@/config/constants';
import { getAllergenCatalog } from '@/services/allergen.service';

// ---------------------------------------------------------------------------
// State & Actions interface
// NOT persisted — re-fetched on each session
// ---------------------------------------------------------------------------

interface AllergenCatalogStoreState {
  catalog: AllergenCatalogItem[];
  /**
   * Bidirectional cross-reaction map.
   * Key: allergen slug → Value: array of allergen slugs that cross-react with it.
   *
   * "Bidirectional" means if A cross-reacts with B, the map contains:
   *   A → [..., B]
   *   B → [..., A]
   *
   * Used in very_strict filter mode to expand selected allergens.
   */
  crossReactionMap: Map<string, string[]>;
  fetchedAt: number | null;
  isLoading: boolean;
  error: ApiError | null;

  // Actions
  fetchCatalog: (tenantSlug: string) => Promise<void>;
  isStale: () => boolean;
}

// ---------------------------------------------------------------------------
// Helper — builds bidirectional cross-reaction map from catalog
// ---------------------------------------------------------------------------

function buildCrossReactionMap(catalog: AllergenCatalogItem[]): Map<string, string[]> {
  const map = new Map<string, string[]>();

  for (const allergen of catalog) {
    for (const cross of allergen.crossReacts) {
      // Forward: allergen → cross
      const existing = map.get(allergen.slug) ?? [];
      if (!existing.includes(cross.allergenSlug)) {
        map.set(allergen.slug, [...existing, cross.allergenSlug]);
      }

      // Reverse: cross → allergen (bidirectional)
      const reverse = map.get(cross.allergenSlug) ?? [];
      if (!reverse.includes(allergen.slug)) {
        map.set(cross.allergenSlug, [...reverse, allergen.slug]);
      }
    }
  }

  return map;
}

// ---------------------------------------------------------------------------
// Store creation — NOT persisted
// ---------------------------------------------------------------------------

const useAllergenCatalogStore = create<AllergenCatalogStoreState>()((set, get) => ({
  catalog: [],
  crossReactionMap: new Map(),
  fetchedAt: null,
  isLoading: false,
  error: null,

  isStale() {
    const { fetchedAt } = get();
    if (fetchedAt === null) return true;
    return Date.now() - fetchedAt > ALLERGEN_CACHE_TTL_MS;
  },

  async fetchCatalog(tenantSlug) {
    if (!get().isStale() && get().catalog.length > 0) return;
    set({ isLoading: true, error: null });
    try {
      const catalog = await getAllergenCatalog(tenantSlug);
      const crossReactionMap = buildCrossReactionMap(catalog);
      set({ catalog, crossReactionMap, fetchedAt: Date.now(), isLoading: false });
    } catch (err) {
      const apiError: ApiError = {
        status: 0,
        code: 'FETCH_ERROR',
        message: err instanceof Error ? err.message : 'Unknown error',
      };
      set({ isLoading: false, error: apiError });
    }
  },
}));

// ---------------------------------------------------------------------------
// Individual selectors
// ---------------------------------------------------------------------------

export const selectAllergenCatalog = (s: AllergenCatalogStoreState) => s.catalog;
export const selectCrossReactionMap = (s: AllergenCatalogStoreState) => s.crossReactionMap;
export const selectAllergenCatalogIsLoading = (s: AllergenCatalogStoreState) => s.isLoading;
export const selectAllergenCatalogError = (s: AllergenCatalogStoreState) => s.error;

// Action selectors
export const selectFetchCatalogAction = (s: AllergenCatalogStoreState) => s.fetchCatalog;

export { useAllergenCatalogStore };
