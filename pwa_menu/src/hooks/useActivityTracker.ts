import { useEffect, useRef } from 'react';
import {
  useSessionStore,
  selectUpdateActivityAction,
  selectHasSession,
} from '@/stores/session.store';

/** Minimum interval between activity writes — throttle to 1 write per 60 seconds */
const THROTTLE_MS = 60_000;

/**
 * Listens to user activity events (touchstart, scroll, click, keydown) and
 * writes to the session store's lastActivity at most once every 60 seconds.
 *
 * Only active when a session exists. Cleans up all listeners on unmount.
 * Mount this hook inside MenuLayout — it should run for the entire menu session.
 */
export function useActivityTracker(): void {
  const hasSession = useSessionStore(selectHasSession);
  const updateActivity = useSessionStore(selectUpdateActivityAction);

  // Track last write time in a ref — no re-render needed
  const lastWriteRef = useRef<number>(0);

  useEffect(() => {
    if (!hasSession) return;

    function handleActivity(): void {
      const now = Date.now();
      if (now - lastWriteRef.current >= THROTTLE_MS) {
        lastWriteRef.current = now;
        updateActivity();
      }
    }

    const events: Array<keyof WindowEventMap> = [
      'touchstart',
      'scroll',
      'click',
      'keydown',
    ];

    events.forEach((event) => {
      window.addEventListener(event, handleActivity, { passive: true });
    });

    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity);
      });
    };
  }, [hasSession, updateActivity]);
}
