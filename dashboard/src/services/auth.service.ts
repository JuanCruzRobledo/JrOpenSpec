/**
 * Auth service — uses a DEDICATED axios instance (no interceptors)
 * to avoid circular dependency with the main api-client which depends on the auth store.
 *
 * The refresh token is an HttpOnly cookie managed by the browser.
 * We must use credentials: 'include' for refresh and logout requests.
 */
import axios from 'axios';
import { API_URL } from '@/config/constants';
import type { TokenResponse, UserProfile, LoginPayload } from '@/types/auth';

const authClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // send HttpOnly cookies
});

export const authService = {
  login: (payload: LoginPayload): Promise<TokenResponse> =>
    authClient
      .post<TokenResponse>('/auth/login', payload)
      .then((r) => r.data),

  /**
   * Refresh the access token.
   * The refresh token is sent automatically as an HttpOnly cookie.
   * No request body needed.
   */
  refresh: (): Promise<TokenResponse> =>
    authClient
      .post<TokenResponse>('/auth/refresh')
      .then((r) => r.data),

  /**
   * Logout — blacklist access token and clear refresh cookie.
   * Requires the current access token in the Authorization header.
   */
  logout: (accessToken: string): Promise<void> =>
    authClient
      .post('/auth/logout', null, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      .then(() => undefined),

  /** Get the current user's profile */
  getMe: (accessToken: string): Promise<UserProfile> =>
    authClient
      .get<UserProfile>('/auth/me', {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      .then((r) => r.data),
};
