import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  useSessionStore,
  selectHasSession,
  selectIsExpiredAction,
  selectClearAction,
} from '@/stores/session.store';

/**
 * Guards routes that require an active session.
 * If the session is expired → clears store + redirects to the landing page.
 * If no session exists → does nothing (SessionGuard route component handles the redirect).
 *
 * Call this hook inside any protected layout/page.
 */
export function useSessionGuard(): void {
  const navigate = useNavigate();
  const params = useParams<{ tenant: string; branch: string; table: string }>();

  const hasSession = useSessionStore(selectHasSession);
  const isExpired = useSessionStore(selectIsExpiredAction);
  const clear = useSessionStore(selectClearAction);

  useEffect(() => {
    if (!hasSession) return;

    if (isExpired()) {
      clear();

      // Reconstruct the landing URL from current route params when available
      if (params.tenant && params.branch && params.table) {
        navigate(`/${params.tenant}/${params.branch}/mesa/${params.table}`, {
          replace: true,
        });
      } else {
        navigate('/', { replace: true });
      }
    }
  }, [hasSession, isExpired, clear, navigate, params]);
}
