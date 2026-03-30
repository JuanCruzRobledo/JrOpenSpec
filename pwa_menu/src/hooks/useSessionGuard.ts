import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  useSessionStore,
  selectHasSession,
  selectIsExpiredAction,
  selectClearAction,
  selectTableIdentifier,
} from '@/stores/session.store';
import { buildLandingPath, resolveRememberedLandingPath } from '@/lib/session-context';

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
  const tableIdentifier = useSessionStore(selectTableIdentifier);

  useEffect(() => {
    if (!hasSession) return;

    if (isExpired()) {
      const landingPath =
        params.tenant && params.branch && tableIdentifier
          ? buildLandingPath(params.tenant, params.branch, tableIdentifier)
          : resolveRememberedLandingPath(params.tenant, params.branch) ?? '/';

      clear();
      navigate(landingPath, { replace: true });
    }
  }, [hasSession, isExpired, clear, navigate, params, tableIdentifier]);
}
