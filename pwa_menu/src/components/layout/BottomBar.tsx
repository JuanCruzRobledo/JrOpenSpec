import { useTranslation } from 'react-i18next';
import { useUiStore, selectAddToastAction } from '@/stores/ui.store';
import { BottomBarButton } from './BottomBarButton';

// ---------------------------------------------------------------------------
// Inline SVG icons — no external library import
// ---------------------------------------------------------------------------

function BellIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function ReceiptIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z" />
      <path d="M16 8H8" />
      <path d="M16 12H8" />
      <path d="M12 16H8" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// BottomBar
// ---------------------------------------------------------------------------

/**
 * Fixed bottom navigation bar with three feature FABs.
 *
 * All three actions (call waiter, history, bill) are "coming soon" —
 * each tap shows an info toast. The bar uses env(safe-area-inset-bottom)
 * so it sits above the system home bar on iOS/Android notch devices.
 *
 * Hard Stop Rule compliance:
 * - Every string is via t() — no hardcoded text.
 */
export function BottomBar() {
  const { t } = useTranslation('menu');
  const addToast = useUiStore(selectAddToastAction);

  function handleComingSoon() {
    addToast(t('bottomBar.comingSoon'), 'info');
  }

  return (
    <nav
      aria-label={t('bottomBar.ariaLabel')}
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-border-default bg-bg-surface"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <div className="flex items-center justify-center gap-8 py-3">
        <BottomBarButton
          labelKey="bottomBar.callWaiter"
          icon={<BellIcon />}
          onClick={handleComingSoon}
        />
        <BottomBarButton
          labelKey="bottomBar.history"
          icon={<ClockIcon />}
          onClick={handleComingSoon}
        />
        <BottomBarButton
          labelKey="bottomBar.myBill"
          icon={<ReceiptIcon />}
          onClick={handleComingSoon}
        />
      </div>
    </nav>
  );
}
