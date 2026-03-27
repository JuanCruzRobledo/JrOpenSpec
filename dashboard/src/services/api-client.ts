/**
 * Shared Axios instance for authenticated API calls.
 *
 * - Request interceptor: attaches Bearer token from auth store
 * - Response interceptor: handles 401 with single-refresh-promise pattern
 *   to prevent token refresh storms when multiple requests fail simultaneously.
 *
 * NOTE: The auth store is imported dynamically to break the circular dependency
 * at module evaluation time (api-client -> auth.store -> auth.service vs
 * api-client -> auth.store). The dynamic import is cached after first call.
 */
import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { API_URL } from '@/config/constants';
import { logger } from '@/lib/logger';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// Lazy accessor for auth store — breaks circular dependency at module load time
let _authStoreModule: typeof import('@/stores/auth.store') | null = null;

async function getAuthStore() {
  if (!_authStoreModule) {
    _authStoreModule = await import('@/stores/auth.store');
  }
  return _authStoreModule.useAuthStore;
}

// ------------------------------------------------------------------
// Token attachment (sync — uses cached module after first load)
// ------------------------------------------------------------------
apiClient.interceptors.request.use(async (config) => {
  const store = await getAuthStore();
  const token = store.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ------------------------------------------------------------------
// 401 handler — single refresh promise pattern
// ------------------------------------------------------------------
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string | null) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token)));
  failedQueue = [];
};

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
  _isLogout?: boolean;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableConfig | undefined;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    // Don't retry logout requests to avoid infinite loop
    if (originalRequest._isLogout) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Another request is already refreshing — queue this one
        return new Promise<string | null>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (token) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const store = await getAuthStore();
        await store.getState().refreshAuth();
        const newToken = store.getState().token;
        processQueue(null, newToken);
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        logger.warn('Token refresh failed, logging out');
        const store = await getAuthStore();
        store.getState().logout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);
