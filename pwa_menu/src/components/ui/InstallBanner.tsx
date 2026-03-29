import { useTranslation } from 'react-i18next';
import {
  useUiStore,
  selectInstallBannerVisible,
  selectHideInstallBannerAction,
} from '@/stores/ui.store';
import { usePWAInstall } from '@/hooks/usePWAInstall';

/**
 * Fixed banner prompting the user to install the PWA.
 *
 * Visibility is controlled by ui.store (installBannerVisible).
 * usePWAInstall captures the beforeinstallprompt event and triggers showInstallBanner
 * after a 30-second delay, respecting the 7-day dismiss cooldown.
 *
 * The actual install prompt is retrieved from window.__pwaInstallPrompt,
 * which usePWAInstall stores there when the browser fires beforeinstallprompt.
 *
 * Hard Stop Rules:
 * - All strings via t().
 * - Dismiss records timestamp so banner respects 7-day cooldown.
 *
 * Mount once in App.tsx outside the router.
 */
export function InstallBanner() {
  const { t } = useTranslation('common');

  // Activate the install prompt detection lifecycle
  usePWAInstall();

  const isVisible = useUiStore(selectInstallBannerVisible);
  const hideInstallBanner = useUiStore(selectHideInstallBannerAction);

  async function handleInstall() {
    const promptEvent = (window as Window & { __pwaInstallPrompt?: { prompt: () => Promise<void> } }).__pwaInstallPrompt;
    if (promptEvent) {
      await promptEvent.prompt();
    }
    hideInstallBanner();
  }

  if (!isVisible) {
    return null;
  }

  return (
    <div
      role="banner"
      className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-between gap-3 border-t border-border-default bg-bg-surface px-4 py-3 shadow-lg"
      style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 0.75rem)' }}
    >
      <p className="flex-1 text-sm text-text-primary">
        {t('installBanner.title')}
      </p>
      <div className="flex shrink-0 items-center gap-2">
        <button
          type="button"
          onClick={() => void handleInstall()}
          className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-accent/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
        >
          {t('installBanner.install')}
        </button>
        <button
          type="button"
          aria-label={t('installBanner.dismiss')}
          onClick={hideInstallBanner}
          className="flex h-8 w-8 items-center justify-center rounded-full text-text-secondary transition-colors hover:bg-bg-elevated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M18 6 6 18" />
            <path d="m6 6 12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
