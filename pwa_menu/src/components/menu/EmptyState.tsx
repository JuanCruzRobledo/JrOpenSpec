import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/Button';
import {
  useFilterStore,
  selectActiveFilterCount,
  selectClearAllAction,
} from '@/stores/filter.store';

/**
 * Empty state shown when no products match current filters.
 * Shows a "Clear filters" button only when filters are active.
 */
export function EmptyState() {
  const { t } = useTranslation('menu');
  const activeFilterCount = useFilterStore(selectActiveFilterCount);
  const clearAll = useFilterStore(selectClearAllAction);

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center gap-4 py-16 px-4 text-center"
    >
      {/* Simple plate illustration */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 64 64"
        className="h-20 w-20 text-text-tertiary"
        aria-hidden="true"
        fill="none"
      >
        <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="2" />
        <circle cx="32" cy="32" r="16" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 3" />
        <path
          d="M24 28c0-4.418 3.582-8 8-8s8 3.582 8 8"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <line x1="32" y1="20" x2="32" y2="16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>

      <div>
        <p className="text-base font-semibold text-surface-text">
          {t('empty.title')}
        </p>
        <p className="mt-1 text-sm text-text-secondary">
          {t('empty.description')}
        </p>
      </div>

      {activeFilterCount > 0 && (
        <Button variant="ghost" size="sm" onClick={clearAll}>
          {t('empty.clearFilters')}
        </Button>
      )}
    </div>
  );
}
