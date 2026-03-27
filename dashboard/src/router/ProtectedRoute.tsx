import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth.store';
import { ROUTES } from '@/router/routes';

interface Props {}

/**
 * Auth guard — redirects to /login if not authenticated.
 * Wraps all protected routes.
 */
export function ProtectedRoute(_props: Props) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const token = useAuthStore((s) => s.token);

  if (!isAuthenticated || !token) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  return <Outlet />;
}
