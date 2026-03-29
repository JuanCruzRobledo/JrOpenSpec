import { useEffect } from 'react';
import {
  useUiStore,
  selectShowInstallBannerAction,
} from '@/stores/ui.store';
import { INSTALL_BANNER_DELAY_MS } from '@/config/constants';

// Extend the global interface for the non-standard BeforeInstallPromptEvent
interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
  prompt(): Promise<void>;
}

declare global {
  interface WindowEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent;
  }
}

/**
 * Handles the PWA install prompt lifecycle.
 *
 * - Captures the `beforeinstallprompt` event (Chrome/Android)
 * - After a 30-second delay, calls showInstallBanner (respects 7-day cooldown)
 * - The banner is managed via ui.store (installBannerVisible)
 *
 * Mount this hook once in the app shell or a top-level layout.
 */
export function usePWAInstall(): void {
  const showInstallBanner = useUiStore(selectShowInstallBannerAction);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;

    function handleBeforeInstallPrompt(event: BeforeInstallPromptEvent): void {
      // Prevent Chrome from showing its own mini-infobar immediately
      event.preventDefault();

      // Store the event so the banner button can trigger prompt() later
      // We store it on window for simplicity — the banner accesses it via the store
      // The ui.store manages visibility; the raw event is needed to call prompt()
      (window as Window & { __pwaInstallPrompt?: BeforeInstallPromptEvent }).__pwaInstallPrompt =
        event;

      // Show our custom banner after the delay, respecting the 7-day cooldown
      timer = setTimeout(() => {
        showInstallBanner();
      }, INSTALL_BANNER_DELAY_MS);
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      if (timer !== undefined) {
        clearTimeout(timer);
      }
    };
  }, [showInstallBanner]);
}
