import { useState, useEffect, useCallback } from 'react';
import { useRegisterSW } from 'virtual:pwa-register/react';

interface UseSWUpdateResult {
  /** True when a new service worker version is waiting to activate */
  needsUpdate: boolean;
  /** Activates the waiting SW and reloads the page */
  applyUpdate: () => void;
}

/**
 * Detects when a new service worker version is available and provides
 * an imperative `applyUpdate()` function.
 *
 * The update is NEVER applied automatically — the UI must ask for user consent
 * (Hard Stop Rule: no force-reload without user consent).
 *
 * Integration: mount in App.tsx or a top-level layout, pass `needsUpdate` to
 * the UpdateToast component.
 */
export function useSWUpdate(): UseSWUpdateResult {
  const [needsUpdate, setNeedsUpdate] = useState(false);

  const { updateServiceWorker } = useRegisterSW({
    onNeedRefresh() {
      setNeedsUpdate(true);
    },
    onOfflineReady() {
      // App is cached and ready for offline use — no action needed
    },
  });

  const applyUpdate = useCallback(() => {
    // updateServiceWorker(true) sends SKIP_WAITING to the waiting SW
    // and reloads the page after activation
    void updateServiceWorker(true);
  }, [updateServiceWorker]);

  return { needsUpdate, applyUpdate };
}
