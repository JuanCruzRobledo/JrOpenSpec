import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import type { CrossReaction } from '@/types/product-detail';

interface CrossReactionListProps {
  crossReactions: CrossReaction[];
}

const riskColorMap: Record<CrossReaction['riskLevel'], string> = {
  low: 'text-success',
  medium: 'text-warning',
  high: 'text-error',
};

/**
 * Collapsible list of cross-reaction allergens.
 * Uses local toggle state with accessible button.
 */
export function CrossReactionList({ crossReactions }: CrossReactionListProps) {
  const { t } = useTranslation('allergens');
  const [isExpanded, setIsExpanded] = useState(false);

  const toggle = useCallback(() => setIsExpanded((v) => !v), []);

  if (crossReactions.length === 0) return null;

  return (
    <div className="mt-1 pl-2 border-l-2 border-surface-border">
      <button
        type="button"
        onClick={toggle}
        aria-expanded={isExpanded}
        className={cn(
          'flex items-center gap-1 text-xs text-text-tertiary',
          'hover:text-text-secondary transition-colors duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded'
        )}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 16 16"
          fill="currentColor"
          className={cn('h-3 w-3 transition-transform duration-150', isExpanded && 'rotate-90')}
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M6.22 4.22a.75.75 0 0 1 1.06 0l3.25 3.25a.75.75 0 0 1 0 1.06l-3.25 3.25a.75.75 0 0 1-1.06-1.06L8.94 8 6.22 5.28a.75.75 0 0 1 0-1.06Z"
            clipRule="evenodd"
          />
        </svg>
        {isExpanded ? t('crossReactions.collapse') : t('crossReactions.expand')}
        {' '}({crossReactions.length})
      </button>

      {isExpanded && (
        <ul className="mt-1.5 flex flex-col gap-1">
          {crossReactions.map((cr) => (
            <li
              key={cr.allergenId}
              className="flex items-center gap-2 text-xs text-text-secondary"
            >
              <span
                className={cn('font-medium', riskColorMap[cr.riskLevel])}
                aria-label={t(`riskLevel.${cr.riskLevel}`)}
              >
                ●
              </span>
              <span>{t('crossReactions.with', { allergen: cr.allergenName })}</span>
              <span className={cn('text-[10px]', riskColorMap[cr.riskLevel])}>
                {t(`riskLevel.${cr.riskLevel}`)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
