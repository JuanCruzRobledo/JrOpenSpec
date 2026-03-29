import { useTranslation } from 'react-i18next';
import { useSWUpdate } from '@/hooks/useSWUpdate';

/**
 * Persistent update notification that appears when a new service worker version
 * is waiting to activate.
 *
 * Hard Stop Rules:
 * - Does NOT auto-dismiss — user must explicitly consent to the update.
 * - Does NOT force-reload without user interaction.
 * - All strings via t().
 *
 * Mount once in App.tsx outside the router so it survives route transitions.
 */
export function UpdateToast() {
  const { t } = useTranslation('common');
  const { needsUpdate, applyUpdate } = useSWUpdate();

  if (!needsUpdate) {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="fixed bottom-20 left-1/2 z-50 -translate-x-1/2 flex items-center gap-3 rounded-lg border border-border-default bg-bg-surface px-4 py-3 shadow-xl"
    >
      <span className="text-sm text-text-primary">
        {t('swUpdate.message')}
      </span>
      <button
        type="button"
        onClick={applyUpdate}
        className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-accent/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
      >
        {t('swUpdate.action')}
      </button>
    </div>
  );
}
