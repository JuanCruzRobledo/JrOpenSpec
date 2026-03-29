import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Pill/banner that appears when the device goes offline.
 *
 * Listens to the native `online` and `offline` window events, initialised
 * from `navigator.onLine` so SSR/hydration is safe.
 *
 * Hard Stop Rules:
 * - All strings via t().
 * - Never blocks the UI — non-intrusive pill at the top of the viewport.
 *
 * Mount once in App.tsx outside the router.
 */
export function OfflineIndicator() {
  const { t } = useTranslation('common');
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  useEffect(() => {
    function handleOnline() {
      setIsOnline(true);
    }
    function handleOffline() {
      setIsOnline(false);
    }

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline) {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="assertive"
      aria-atomic="true"
      className="fixed left-1/2 top-4 z-50 -translate-x-1/2 flex items-center gap-2 rounded-full border border-warning/40 bg-warning/10 px-4 py-2 text-sm font-medium text-warning shadow-md"
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
        <line x1="1" y1="1" x2="23" y2="23" />
        <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
        <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
        <path d="M10.71 5.05A16 16 0 0 1 22.56 9" />
        <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
        <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
        <line x1="12" y1="20" x2="12.01" y2="20" />
      </svg>
      <span>{t('offline.message')}</span>
    </div>
  );
}
