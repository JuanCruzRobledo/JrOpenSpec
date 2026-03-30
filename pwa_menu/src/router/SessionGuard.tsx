import { Navigate, Outlet, useParams } from 'react-router-dom';
import { useSessionStore, selectHasSession } from '@/stores/session.store';
import { useSessionGuard } from '@/hooks/useSessionGuard';
import { buildLandingPath, resolveRememberedLandingPath } from '@/lib/session-context';

/**
 * Route wrapper that protects menu routes from unauthenticated access.
 *
 * - No session → redirects to the landing page for this table
 * - Expired session → useSessionGuard handles clear + redirect
 * - Valid session → renders <Outlet />
 */
export function SessionGuard() {
  const hasSession = useSessionStore(selectHasSession);
  const params = useParams<{ tenant: string; branch: string; table: string }>();

  // Activate expiry guard inside protected routes
  useSessionGuard();

  if (!hasSession) {
    const rememberedLandingPath = resolveRememberedLandingPath(
      params.tenant,
      params.branch
    );

    // Reconstruct landing URL from current route params when available
    if (params.tenant && params.branch && params.table) {
      return (
        <Navigate
          to={buildLandingPath(params.tenant, params.branch, params.table)}
          replace
        />
      );
    }

    if (rememberedLandingPath) {
      return <Navigate to={rememberedLandingPath} replace />;
    }

    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
