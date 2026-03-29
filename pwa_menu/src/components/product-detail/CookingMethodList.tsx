import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import type { CookingMethodInfo } from '@/types/product-detail';

interface CookingMethodListProps {
  methods: CookingMethodInfo[];
}

/**
 * Cooking method chips.
 */
export function CookingMethodList({ methods }: CookingMethodListProps) {
  const { t } = useTranslation('menu');

  if (methods.length === 0) {
    return (
      <p className="text-sm italic text-text-tertiary">{t('detail.noCooking')}</p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2" aria-label={t('detail.cookingMethods')}>
      {methods.map((method) => (
        <span
          key={method.id}
          className={cn(
            'inline-flex items-center rounded-full px-3 py-1.5',
            'text-xs font-medium',
            'bg-info/10 border border-info/30 text-info'
          )}
        >
          {method.name}
        </span>
      ))}
    </div>
  );
}
