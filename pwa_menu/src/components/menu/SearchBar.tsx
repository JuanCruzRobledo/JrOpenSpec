import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import { DEBOUNCE_MS } from '@/config/constants';
import { useDebounce } from '@/hooks/useDebounce';
import {
  useFilterStore,
  selectSearchQuery,
  selectSetSearchQueryAction,
} from '@/stores/filter.store';

/**
 * Search bar connected to the filter store.
 *
 * Local state tracks the input value for immediate visual feedback.
 * The debounced value drives the store write (300ms delay).
 * When the store's searchQuery is cleared externally (e.g. "Clear filters"),
 * the local state syncs back to empty.
 */
export function SearchBar() {
  const { t } = useTranslation('menu');

  const storeQuery = useFilterStore(selectSearchQuery);
  const setSearchQuery = useFilterStore(selectSetSearchQueryAction);

  // Local state for immediate input responsiveness
  const [localValue, setLocalValue] = useState(storeQuery);

  // Sync local state when store is cleared from outside (e.g. clearAll)
  useEffect(() => {
    if (storeQuery === '' && localValue !== '') {
      setLocalValue('');
    }
  // We intentionally do NOT include localValue — only react to store becoming empty
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeQuery]);

  // Debounced version drives the store write
  const debouncedValue = useDebounce(localValue, DEBOUNCE_MS);

  useEffect(() => {
    setSearchQuery(debouncedValue);
  }, [debouncedValue, setSearchQuery]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setLocalValue(e.target.value);
    },
    []
  );

  const handleClear = useCallback(() => {
    setLocalValue('');
    // Also clear immediately (don't wait for debounce)
    setSearchQuery('');
  }, [setSearchQuery]);

  return (
    <div className="relative px-4 py-2">
      {/* Search icon */}
      <span
        className="pointer-events-none absolute left-7 top-1/2 -translate-y-1/2 text-text-tertiary"
        aria-hidden="true"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-4 w-4"
        >
          <path
            fillRule="evenodd"
            d="M9 3.5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11ZM2 9a7 7 0 1 1 12.452 4.391l3.328 3.329a.75.75 0 1 1-1.06 1.06l-3.329-3.328A7 7 0 0 1 2 9Z"
            clipRule="evenodd"
          />
        </svg>
      </span>

      <input
        type="search"
        value={localValue}
        onChange={handleChange}
        placeholder={t('search.placeholder')}
        aria-label={t('search.ariaLabel')}
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck="false"
        className={cn(
          'w-full rounded-xl py-3 pl-9 pr-10',
          'bg-surface-muted text-surface-text text-sm',
          'border border-surface-border',
          'placeholder:text-text-tertiary',
          'transition-colors duration-150',
          'focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
          // Remove default browser clear button on Chrome/Safari
          '[&::-webkit-search-cancel-button]:appearance-none'
        )}
      />

      {/* Custom clear button — only visible when there is input */}
      {localValue.length > 0 && (
        <button
          type="button"
          onClick={handleClear}
          aria-label={t('search.clearAriaLabel')}
          className={cn(
            'absolute right-7 top-1/2 -translate-y-1/2',
            'flex h-6 w-6 items-center justify-center rounded-full',
            'text-text-tertiary hover:text-surface-text hover:bg-surface-card',
            'transition-colors duration-150',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent'
          )}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="h-4 w-4"
            aria-hidden="true"
          >
            <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
          </svg>
        </button>
      )}
    </div>
  );
}
