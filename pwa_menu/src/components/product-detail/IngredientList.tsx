import { useTranslation } from 'react-i18next';
import type { Ingredient } from '@/types/product-detail';

interface IngredientListProps {
  ingredients: Ingredient[];
}

/**
 * Ordered ingredient list.
 * Format: "Name — quantity unit" with optional "(opcional)" badge.
 */
export function IngredientList({ ingredients }: IngredientListProps) {
  const { t } = useTranslation('menu');

  if (ingredients.length === 0) {
    return (
      <p className="text-sm italic text-text-tertiary">{t('detail.noIngredients')}</p>
    );
  }

  return (
    <ol className="flex flex-col gap-1.5" aria-label={t('detail.ingredients')}>
      {ingredients.map((ingredient) => (
        <li
          key={ingredient.id}
          className="flex items-baseline justify-between gap-2 text-sm text-surface-text"
        >
          <span className="flex items-baseline gap-1.5">
            <span>{ingredient.name}</span>
            {ingredient.isOptional && (
              <span className="text-xs text-text-tertiary italic">
                {t('detail.optional')}
              </span>
            )}
          </span>

          {/* Allergen hint dots — subtle */}
          {ingredient.allergenSlugs.length > 0 && (
            <span
              className="flex-shrink-0 text-[10px] text-text-tertiary"
              aria-hidden="true"
            >
              {ingredient.allergenSlugs.slice(0, 3).join(' · ')}
            </span>
          )}
        </li>
      ))}
    </ol>
  );
}
