import { useTranslation } from 'react-i18next';
import { AllergenEntry } from '@/components/product-detail/AllergenEntry';
import type { ProductAllergenDetail } from '@/types/product-detail';

interface AllergenListProps {
  allergens: ProductAllergenDetail[];
}

/**
 * Full allergen list section for product detail.
 * Groups by presence type (contains first, then may_contain, then free).
 */
export function AllergenList({ allergens }: AllergenListProps) {
  const { t } = useTranslation('menu');

  if (allergens.length === 0) {
    return (
      <p className="text-sm italic text-text-tertiary">{t('detail.noAllergens')}</p>
    );
  }

  // Sort: contains → may_contain → free
  const presenceOrder: Record<string, number> = { contains: 0, may_contain: 1, free: 2 };
  const sorted = [...allergens].sort(
    (a, b) => (presenceOrder[a.presence] ?? 3) - (presenceOrder[b.presence] ?? 3)
  );

  return (
    <ul className="flex flex-col gap-2" aria-label={t('detail.allergens')}>
      {sorted.map((allergen) => (
        <AllergenEntry key={allergen.allergenId} allergen={allergen} />
      ))}
    </ul>
  );
}
