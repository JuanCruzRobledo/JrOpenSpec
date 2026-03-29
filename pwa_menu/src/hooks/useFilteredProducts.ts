import { useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import type { MenuCategory } from '@/types/menu';
import { filterCategories } from '@/lib/filter-engine';
import {
  useFilterStore,
  selectSearchQuery,
  selectAllergenMode,
} from '@/stores/filter.store';
import {
  useAllergenCatalogStore,
  selectCrossReactionMap,
} from '@/stores/allergen-catalog.store';

/**
 * Memoized hook that applies filter-engine to the full category tree.
 *
 * Uses useShallow for the array-type selectors to avoid infinite re-renders.
 *
 * @param categories - Raw categories from menu store (pass null/undefined when loading)
 * @returns Filtered category tree (empty categories/subcategories removed)
 */
export function useFilteredProducts(
  categories: MenuCategory[] | null | undefined
): MenuCategory[] {
  const searchQuery = useFilterStore(selectSearchQuery);
  const allergenMode = useFilterStore(selectAllergenMode);

  // useShallow prevents re-renders when arrays have same contents but new references
  const selectedAllergens = useFilterStore(
    useShallow((s) => s.selectedAllergens)
  );
  const selectedDietary = useFilterStore(
    useShallow((s) => s.selectedDietary)
  );
  const selectedCooking = useFilterStore(
    useShallow((s) => s.selectedCooking)
  );

  const crossReactionMap = useAllergenCatalogStore(selectCrossReactionMap);

  return useMemo(() => {
    if (!categories) return [];

    return filterCategories(
      categories,
      searchQuery,
      { codes: selectedAllergens, mode: allergenMode },
      selectedDietary,
      selectedCooking,
      crossReactionMap
    );
  }, [
    categories,
    searchQuery,
    allergenMode,
    selectedAllergens,
    selectedDietary,
    selectedCooking,
    crossReactionMap,
  ]);
}
