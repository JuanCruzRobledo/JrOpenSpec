import { useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import type { MenuCategory } from '@/types/menu';
import { summarizeCrossReactionHiddenProducts } from '@/lib/filter-engine';
import {
  useFilterStore,
  selectAllergenMode,
} from '@/stores/filter.store';
import {
  useAllergenCatalogStore,
  selectAllergenCatalog,
  selectCrossReactionMap,
} from '@/stores/allergen-catalog.store';

export function useCrossReactionFeedback(
  categories: MenuCategory[] | null | undefined
) {
  const allergenMode = useFilterStore(selectAllergenMode);
  const selectedAllergens = useFilterStore(useShallow((s) => s.selectedAllergens));
  const catalog = useAllergenCatalogStore(selectAllergenCatalog);
  const crossReactionMap = useAllergenCatalogStore(selectCrossReactionMap);

  return useMemo(() => {
    if (!categories || categories.length === 0) {
      return null;
    }

    return summarizeCrossReactionHiddenProducts(
      categories,
      { codes: selectedAllergens, mode: allergenMode },
      crossReactionMap,
      catalog
    );
  }, [categories, selectedAllergens, allergenMode, crossReactionMap, catalog]);
}
