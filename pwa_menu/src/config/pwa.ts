/**
 * PWA runtime configuration helpers.
 * Complements vite.config.ts which handles build-time SW generation.
 */

/**
 * Checks whether the app is running in standalone PWA mode
 * (i.e., installed to home screen).
 */
export function isStandalonePWA(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    ('standalone' in window.navigator && (window.navigator as { standalone?: boolean }).standalone === true)
  );
}

/**
 * Checks if the browser supports the PWA install prompt.
 * Used by usePWAInstall hook to determine if the banner should be shown.
 */
export function supportsInstallPrompt(): boolean {
  return 'BeforeInstallPromptEvent' in window;
}
