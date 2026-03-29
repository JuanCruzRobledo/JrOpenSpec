import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/Button';
import {
  useFilterStore,
  selectActiveFilterCount,
  selectClearAllAction,
} from '@/stores/filter.store';

/**
 * "Clear all filters" button — only visible when at least one filter is active.
 */
export function ClearFiltersButton() {
  const { t } = useTranslation('filters');
  const activeFilterCount = useFilterStore(selectActiveFilterCount);
  const clearAll = useFilterStore(selectClearAllAction);

  if (activeFilterCount === 0) return null;

  return (
    <Button variant="ghost" size="sm" onClick={clearAll} className="w-full">
      {t('clearAll')} ({activeFilterCount})
    </Button>
  );
}
