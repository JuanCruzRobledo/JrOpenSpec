import { useAuthStore } from '@/stores/auth.store';

/**
 * Convenience hook for auth — provides individual selectors.
 * Components should still use individual selectors for granular subscriptions.
 * This hook is for cases where you need multiple auth values together.
 */
export function useAuth() {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading = useAuthStore((s) => s.isLoading);
  const login = useAuthStore((s) => s.login);
  const logout = useAuthStore((s) => s.logout);

  return { token, user, isAuthenticated, isLoading, login, logout };
}
