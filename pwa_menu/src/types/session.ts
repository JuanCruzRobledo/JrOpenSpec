/**
 * Session types for the anonymous customer session flow.
 * QR → Landing → POST /api/sessions/join → Token stored in Zustand persist
 */

/** Request body for POST /api/sessions/join */
export interface SessionJoinRequest {
  branchSlug: string;
  tableIdentifier: string;
  displayName: string;
  avatarColor: string;
  locale: string;
}

/** Response body from POST /api/sessions/join */
export interface SessionJoinResponse {
  token: string;
  sessionId: string;
  expiresAt: string; // ISO 8601
  branch: {
    id: string;
    name: string;
    slug: string;
  };
  table: {
    identifier: string;
    displayName: string;
  };
}

/** State shape persisted in localStorage under 'buen-sabor-session' */
export interface SessionState {
  /** HMAC token sent as X-Table-Token header */
  token: string | null;
  /** UUID v4 session identifier */
  sessionId: string | null;
  displayName: string;
  avatarColor: string;
  branchSlug: string | null;
  branchName: string | null;
  tableIdentifier: string | null;
  tableName: string | null;
  /** ISO 8601 timestamp of session creation */
  joinedAt: string | null;
  /** Unix timestamp (ms) of last user activity — sliding window for 8h expiry */
  lastActivity: number | null;
}
