/**
 * Auth store — manages access token (in memory), refresh via HttpOnly cookie.
 *
 * KEY DECISIONS:
 * - Refresh token is HttpOnly cookie — we never see or store it.
 * - Proactive refresh at TOKEN_REFRESH_MARGIN_MS before expiry.
 * - BroadcastChannel for cross-tab logout, storage events as fallback.
 * - NEVER destructure this store in components — use individual selectors.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authService } from '@/services/auth.service';
import { TOKEN_REFRESH_MARGIN_MS } from '@/config/constants';
import { logger } from '@/lib/logger';
import type { UserProfile } from '@/types/auth';

interface AuthState {
  token: string | null;
  expiresAt: number | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
  setUser: (user: UserProfile) => void;
  _scheduleRefresh: () => void;
  _broadcastLogout: () => void;
}

const CHANNEL_NAME = 'buen-sabor-auth';
const STORAGE_KEY = 'buen-sabor-auth';

// JWT default expiry — 15 minutes (900 seconds)
const DEFAULT_TOKEN_LIFETIME_MS = 900_000;

let refreshTimeoutId: ReturnType<typeof setTimeout> | null = null;
let broadcastChannel: BroadcastChannel | null = null;

try {
  broadcastChannel = new BroadcastChannel(CHANNEL_NAME);
} catch {
  // BroadcastChannel not supported — fallback to storage events
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      expiresAt: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const res = await authService.login({ email, password });
          const expiresAt = Date.now() + DEFAULT_TOKEN_LIFETIME_MS;

          set({
            token: res.access_token,
            expiresAt,
            isAuthenticated: true,
            isLoading: false,
          });

          // Fetch user profile with the new token
          try {
            const user = await authService.getMe(res.access_token);
            set({ user });
          } catch {
            logger.warn('Failed to fetch user profile after login');
          }

          get()._scheduleRefresh();
        } catch (err) {
          set({ isLoading: false });
          throw err;
        }
      },

      logout: () => {
        if (refreshTimeoutId) {
          clearTimeout(refreshTimeoutId);
          refreshTimeoutId = null;
        }

        const currentToken = get().token;
        if (currentToken) {
          // Fire and forget — don't block logout on API call
          authService.logout(currentToken).catch(() => {
            logger.debug('Logout API call failed (token may already be expired)');
          });
        }

        set({
          token: null,
          expiresAt: null,
          user: null,
          isAuthenticated: false,
        });

        get()._broadcastLogout();
      },

      refreshAuth: async () => {
        try {
          const res = await authService.refresh();
          const expiresAt = Date.now() + DEFAULT_TOKEN_LIFETIME_MS;

          set({
            token: res.access_token,
            expiresAt,
            isAuthenticated: true,
          });

          get()._scheduleRefresh();
        } catch {
          logger.warn('Token refresh failed');
          get().logout();
        }
      },

      setUser: (user: UserProfile) => set({ user }),

      _scheduleRefresh: () => {
        if (refreshTimeoutId) {
          clearTimeout(refreshTimeoutId);
        }

        const expiresAt = get().expiresAt;
        if (!expiresAt) return;

        const refreshIn = expiresAt - Date.now() - TOKEN_REFRESH_MARGIN_MS;

        if (refreshIn <= 0) {
          // Token is about to expire or already expired — refresh immediately
          get().refreshAuth();
          return;
        }

        refreshTimeoutId = setTimeout(() => {
          get().refreshAuth();
        }, refreshIn);
      },

      _broadcastLogout: () => {
        try {
          broadcastChannel?.postMessage({ type: 'LOGOUT' });
        } catch {
          // BroadcastChannel may be closed
        }
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (s) => ({
        token: s.token,
        expiresAt: s.expiresAt,
        user: s.user,
      }),
      onRehydrateStorage: () => {
        return (state: AuthState | undefined) => {
          if (state?.token && state?.expiresAt) {
            if (Date.now() < state.expiresAt) {
              state.isAuthenticated = true;
              state._scheduleRefresh();
            } else {
              // Token expired — try to refresh
              state.refreshAuth();
            }
          }
        };
      },
    },
  ),
);

// Cross-tab logout via BroadcastChannel
broadcastChannel?.addEventListener('message', (event: MessageEvent) => {
  if (event.data?.type === 'LOGOUT') {
    // Clear state without broadcasting again (to avoid loop)
    if (refreshTimeoutId) {
      clearTimeout(refreshTimeoutId);
      refreshTimeoutId = null;
    }
    useAuthStore.setState({
      token: null,
      expiresAt: null,
      user: null,
      isAuthenticated: false,
    });
  }
});

// Fallback: storage event listener for browsers without BroadcastChannel
if (!broadcastChannel) {
  window.addEventListener('storage', (event: StorageEvent) => {
    if (event.key === STORAGE_KEY && event.newValue) {
      try {
        const parsed = JSON.parse(event.newValue) as { state?: { token?: string | null } };
        if (!parsed.state?.token) {
          useAuthStore.setState({
            token: null,
            expiresAt: null,
            user: null,
            isAuthenticated: false,
          });
        }
      } catch {
        // Ignore parse errors
      }
    }
  });
}
