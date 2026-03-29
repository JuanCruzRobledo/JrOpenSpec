import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useShallow } from 'zustand/react/shallow';
import { FilterChip } from '@/components/filters/FilterChip';
import {
  useFilterStore,
  selectSelectedDietary,
  selectToggleDietaryAction,
} from '@/stores/filter.store';
import type { MenuCategory } from '@/types/menu';

interface DietaryFilterSectionProps {
  /** Full (unfiltered) category tree for deduplication */
  categories: MenuCategory[];
}

/**
 * Dietary profile filter chips.
 * Profiles are deduped from all products across the entire menu.
 */
export function DietaryFilterSection({ categories }: DietaryFilterSectionProps) {
  const { t } = useTranslation('filters');

  // Deduplicate dietary profile slugs from all products
  const profiles = useMemo(() => {
    const seen = new Map<string, string>(); // slug → name
    for (const category of categories) {
      for (const sub of category.subcategories) {
        for (const product of sub.products) {
          for (const slug of product.dietaryProfileSlugs) {
            if (!seen.has(slug)) {
              seen.set(slug, slug); // name not available on MenuProduct — use slug
            }
          }
        }
      }
    }
    return Array.from(seen.entries()).map(([slug, name]) => ({ slug, name }));
  }, [categories]);

  const selectedDietary = useFilterStore(useShallow((s) => s.selectedDietary));
  const toggleDietary = useFilterStore(selectToggleDietaryAction);

  if (profiles.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      <div>
        <p className="text-sm font-semibold text-surface-text">{t('dietary.title')}</p>
        <p className="mt-0.5 text-xs text-text-tertiary">{t('dietary.hint')}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {profiles.map(({ slug, name }) => (
          <FilterChip
            key={slug}
            label={name}
            isSelected={selectedDietary.includes(slug)}
            onToggle={() => toggleDietary(slug)}
            ariaLabel={t('dietary.ariaLabel', { name })}
          />
        ))}
      </div>
    </div>
  );
}
