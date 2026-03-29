import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import {
  useSessionStore,
  selectDisplayName,
  selectAvatarColor,
  selectBranchName,
  selectTableName,
} from '@/stores/session.store';
import {
  useFilterStore,
  selectActiveFilterCount,
} from '@/stores/filter.store';
import {
  useUiStore,
  selectOpenFilterDrawerAction,
} from '@/stores/ui.store';
import { LanguageSelector } from '@/components/layout/LanguageSelector';

/**
 * Sticky header for the menu page.
 * Shows branch name, table, user avatar, language selector, and filter toggle.
 * Filter button displays a badge count when filters are active.
 */
export function MenuHeader() {
  const { t } = useTranslation('common');

  const displayName = useSessionStore(selectDisplayName);
  const avatarColor = useSessionStore(selectAvatarColor);
  const branchName = useSessionStore(selectBranchName);
  const tableName = useSessionStore(selectTableName);
  const activeFilterCount = useFilterStore(selectActiveFilterCount);
  const openFilterDrawer = useUiStore(selectOpenFilterDrawerAction);

  // First char of name for the avatar — fallback to "?" when name is empty
  const avatarInitial = displayName ? displayName.charAt(0).toUpperCase() : '?';

  return (
    <header
      className={cn(
        'sticky top-0 z-40 w-full',
        'bg-surface-bg/90 backdrop-blur-sm',
        'border-b border-surface-border'
      )}
    >
      <div className="flex items-center gap-3 px-4 py-3">
        {/* Branch + table info */}
        <div className="min-w-0 flex-1">
          {branchName && (
            <p className="truncate text-sm font-semibold text-surface-text leading-tight">
              {branchName}
            </p>
          )}
          {tableName && (
            <p className="truncate text-xs text-text-secondary leading-tight">
              {t('header.table')}: {tableName}
            </p>
          )}
        </div>

        {/* Language selector */}
        <LanguageSelector />

        {/* Filter toggle button */}
        <button
          type="button"
          aria-label={
            activeFilterCount > 0
              ? t('header.filtersActive', { count: activeFilterCount })
              : t('header.filters')
          }
          onClick={openFilterDrawer}
          className={cn(
            'relative flex h-11 w-11 items-center justify-center rounded-full',
            'bg-surface-muted text-surface-text',
            'transition-colors duration-150',
            'hover:bg-surface-card',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2'
          )}
        >
          {/* Filter icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="h-5 w-5"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M2.628 1.601C5.028 1.206 7.49 1 10 1s4.973.206 7.372.601a.75.75 0 0 1 .628.74v2.288a2.25 2.25 0 0 1-.659 1.59l-4.682 4.683a2.25 2.25 0 0 0-.659 1.59v3.037c0 .684-.31 1.33-.844 1.757l-1.937 1.55A.75.75 0 0 1 8 18.25v-5.757a2.25 2.25 0 0 0-.659-1.591L2.659 6.22A2.25 2.25 0 0 1 2 4.629V2.34a.75.75 0 0 1 .628-.74Z"
              clipRule="evenodd"
            />
          </svg>

          {/* Active filter count badge */}
          {activeFilterCount > 0 && (
            <span
              aria-hidden="true"
              className={cn(
                'absolute -top-1 -right-1',
                'flex h-5 w-5 items-center justify-center',
                'rounded-full bg-accent text-white text-[10px] font-bold leading-none'
              )}
            >
              {activeFilterCount > 9 ? '9+' : activeFilterCount}
            </span>
          )}
        </button>

        {/* User avatar */}
        <div
          role="img"
          aria-label={t('header.userAvatar', {
            name: displayName || t('anonymous'),
          })}
          style={{ backgroundColor: avatarColor || '#f97316' }}
          className={cn(
            'flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full',
            'text-sm font-bold text-white select-none'
          )}
        >
          <span aria-hidden="true">{avatarInitial}</span>
        </div>
      </div>
    </header>
  );
}
