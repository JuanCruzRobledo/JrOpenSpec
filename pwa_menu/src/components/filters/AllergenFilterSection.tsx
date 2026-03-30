import { useTranslation } from 'react-i18next';
import { useShallow } from 'zustand/react/shallow';
import { AllergenModeSelector } from '@/components/filters/AllergenModeSelector';
import { FilterChip } from '@/components/filters/FilterChip';
import {
  useFilterStore,
  selectToggleAllergenAction,
} from '@/stores/filter.store';
import {
  useAllergenCatalogStore,
  selectAllergenCatalog,
} from '@/stores/allergen-catalog.store';

/**
 * Allergen filter section: mode selector + allergen chips.
 * Reads allergen list from the catalog store (pre-fetched by MenuPage).
 */
export function AllergenFilterSection() {
  const { t } = useTranslation('filters');

  const catalog = useAllergenCatalogStore(selectAllergenCatalog);

  // useShallow to prevent re-renders when array contents are equal
  const selectedAllergens = useFilterStore(useShallow((s) => s.selectedAllergens));
  const toggleAllergen = useFilterStore(selectToggleAllergenAction);

  return (
    <div className="flex flex-col gap-4">
      {/* Title + hint */}
      <div>
        <p className="text-sm font-semibold text-surface-text">{t('allergens.title')}</p>
        <p className="mt-0.5 text-xs text-text-tertiary">{t('allergens.hint')}</p>
      </div>

      {/* Mode selector */}
      <AllergenModeSelector />

      {/* Allergen chips */}
      {catalog.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {catalog.map((allergen) => (
            <FilterChip
              key={allergen.slug}
              label={allergen.name}
              isSelected={selectedAllergens.includes(allergen.slug)}
              onToggle={() => toggleAllergen(allergen.slug)}
              ariaLabel={t('allergens.ariaLabel', { name: allergen.name })}
            />
          ))}
        </div>
      )}
    </div>
  );
}
