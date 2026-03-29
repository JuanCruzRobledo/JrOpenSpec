import axios, { type AxiosInstance } from 'axios';
import { API_URL } from '@/config/constants';

/**
 * Axios API client for the pwa_menu.
 *
 * Auth strategy: simple HMAC session token (not JWT).
 * No refresh flow — 401/403 clears the session; SessionGuard handles redirect.
 *
 * The session token is injected lazily via request interceptor to avoid
 * circular import issues with the session store.
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// -----------------------------------------------------------------------
// Request interceptor — attach X-Session-Token from session store
// Imported lazily to break circular dependency: store → api-client → store
// -----------------------------------------------------------------------
apiClient.interceptors.request.use((config) => {
  // Dynamic import to avoid circular dependency at module evaluation time
  // This is intentionally synchronous-like: we read from localStorage directly
  // to avoid the store initialization order problem.
  try {
    const raw = localStorage.getItem('buen-sabor-session');
    if (raw) {
      const parsed = JSON.parse(raw) as { state?: { token?: string } };
      const token = parsed.state?.token;
      if (token) {
        config.headers['X-Session-Token'] = token;
      }
    }
  } catch {
    // Ignore parse errors — token simply won't be attached
  }
  return config;
});

// -----------------------------------------------------------------------
// Response interceptor — clear session on 401/403
// Redirect is NOT done here; SessionGuard observes the cleared store.
// -----------------------------------------------------------------------
apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      if (status === 401 || status === 403) {
        // Clear persisted session so SessionGuard redirects to landing
        try {
          localStorage.removeItem('buen-sabor-session');
        } catch {
          // Ignore storage errors
        }
      }
    }
    return Promise.reject(error);
  }
);

export { apiClient };
