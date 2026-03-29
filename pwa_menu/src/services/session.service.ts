import { apiClient } from './api-client';
import type { SessionJoinRequest, SessionJoinResponse } from '@/types/session';
import type { ApiEnvelope } from '@/types/api';

/**
 * Joins an anonymous customer session.
 *
 * POST /api/sessions/join
 *
 * Called from the landing page after the user submits their name and color.
 * Returns the HMAC token and session metadata to be stored in the session store.
 *
 * @throws AxiosError with 404 if branch/table not found
 * @throws AxiosError with 409 if table is inactive
 * @throws AxiosError with 429 if rate-limited (60 req/min per IP)
 */
export async function joinSession(
  req: SessionJoinRequest
): Promise<SessionJoinResponse> {
  const response = await apiClient.post<ApiEnvelope<SessionJoinResponse>>(
    '/api/sessions/join',
    req
  );
  return response.data.data;
}
