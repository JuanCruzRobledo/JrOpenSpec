import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import { CrossReactionList } from '@/components/product-detail/CrossReactionList';
import type { ProductAllergenDetail } from '@/types/product-detail';

interface AllergenEntryProps {
  allergen: ProductAllergenDetail;
}

/**
 * Single allergen entry with traffic-light coloring.
 *
 * Presence type → color scheme:
 * - contains   → red   (bg-allergen-contains-bg / border / text)
 * - may_contain → amber
 * - free        → green
 *
 * Colors come from @theme CSS custom properties in index.css.
 */
export function AllergenEntry({ allergen }: AllergenEntryProps) {
  const { t } = useTranslation('allergens');

  const presenceStyles: Record<string, string> = {
    contains: 'bg-allergen-contains-bg border border-allergen-contains-border text-allergen-contains-text',
    may_contain: 'bg-allergen-may-contain-bg border border-allergen-may-contain-border text-allergen-may-contain-text',
    free: 'bg-allergen-free-bg border border-allergen-free-border text-allergen-free-text',
  };

  const presenceStyle = presenceStyles[allergen.presence] ?? presenceStyles['contains'];

  return (
    <li className={cn('rounded-lg p-2.5', presenceStyle)}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-0.5 min-w-0">
          <span className="text-sm font-semibold leading-tight">
            {allergen.allergenName}
          </span>
          <span className="text-xs opacity-80">
            {t(`presence.${allergen.presence}`)}
          </span>
        </div>

        {/* Presence type badge */}
        <span className="flex-shrink-0 rounded-full border border-current/30 px-2 py-0.5 text-[10px] font-medium opacity-90">
          {t(`legend.${allergen.presence}`)}
        </span>
      </div>

      {/* Cross-reactions — collapsible */}
      {allergen.crossReactions.length > 0 && (
        <CrossReactionList crossReactions={allergen.crossReactions} />
      )}
    </li>
  );
}
