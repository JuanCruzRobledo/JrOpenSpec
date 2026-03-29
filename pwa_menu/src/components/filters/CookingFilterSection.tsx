import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useShallow } from 'zustand/react/shallow';
import { FilterChip } from '@/components/filters/FilterChip';
import {
  useFilterStore,
  selectSelectedCooking,
  selectToggleCookingAction,
} from '@/stores/filter.store';
import type { MenuCategory } from '@/types/menu';

interface CookingFilterSectionProps {
  /** Full (unfiltered) category tree for deduplication */
  categories: MenuCategory[];
}

/**
 * Cooking method filter chips.
 * Methods are deduped from all products across the entire menu.
 */
export function CookingFilterSection({ categories }: CookingFilterSectionProps) {
  const { t } = useTranslation('filters');

  // Deduplicate cooking method slugs from all products
  const methods = useMemo(() => {
    const seen = new Map<string, string>(); // slug → display name (slug for now)
    for (const category of categories) {
      for (const sub of category.subcategories) {
        for (const product of sub.products) {
          for (const slug of product.cookingMethodSlugs) {
            if (!seen.has(slug)) {
              seen.set(slug, slug);
            }
          }
        }
      }
    }
    return Array.from(seen.entries()).map(([slug, name]) => ({ slug, name }));
  }, [categories]);

  const selectedCooking = useFilterStore(useShallow((s) => s.selectedCooking));
  const toggleCooking = useFilterStore(selectToggleCookingAction);

  if (methods.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      <div>
        <p className="text-sm font-semibold text-surface-text">{t('cooking.title')}</p>
        <p className="mt-0.5 text-xs text-text-tertiary">{t('cooking.hint')}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {methods.map(({ slug, name }) => (
          <FilterChip
            key={slug}
            label={name}
            isSelected={selectedCooking.includes(slug)}
            onToggle={() => toggleCooking(slug)}
            ariaLabel={t('cooking.ariaLabel', { name })}
          />
        ))}
      </div>
    </div>
  );
}
