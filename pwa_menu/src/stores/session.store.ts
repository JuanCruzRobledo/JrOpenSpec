import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SessionJoinResponse } from '@/types/session';
import { SESSION_INACTIVITY_MS } from '@/config/constants';

// ---------------------------------------------------------------------------
// State & Actions interface
// ---------------------------------------------------------------------------

interface SessionStoreState {
  // Session data
  token: string | null;
  sessionId: string | null;
  displayName: string;
  avatarColor: string;
  branchSlug: string | null;
  branchName: string | null;
  tableIdentifier: string | null;
  tableName: string | null;
  joinedAt: string | null;
  /** Unix timestamp (ms) of last user activity — sliding window expiry */
  lastActivity: number | null;

  // Actions
  /** Populate store from a successful join response */
  join: (response: SessionJoinResponse, displayName: string, avatarColor: string) => void;
  /** Clear all session data (logout / expiry) */
  clear: () => void;
  /** Update lastActivity to now — throttled by callers to avoid excess writes */
  updateActivity: () => void;
  /** Check if the 8-hour inactivity window has elapsed */
  isExpired: () => boolean;
}

const initialState: Omit<SessionStoreState, 'join' | 'clear' | 'updateActivity' | 'isExpired'> = {
  token: null,
  sessionId: null,
  displayName: '',
  avatarColor: '',
  branchSlug: null,
  branchName: null,
  tableIdentifier: null,
  tableName: null,
  joinedAt: null,
  lastActivity: null,
};

// ---------------------------------------------------------------------------
// Store creation — persisted to localStorage under 'buen-sabor-session'
// ---------------------------------------------------------------------------

const useSessionStore = create<SessionStoreState>()(
  persist(
    (set, get) => ({
      ...initialState,

      join(response, displayName, avatarColor) {
        set({
          token: response.token,
          sessionId: response.sessionId,
          displayName: displayName || '',
          avatarColor,
          branchSlug: response.branch.slug,
          branchName: response.branch.name,
          tableIdentifier: response.table.identifier,
          tableName: response.table.displayName,
          joinedAt: new Date().toISOString(),
          lastActivity: Date.now(),
        });
      },

      clear() {
        set({ ...initialState });
      },

      updateActivity() {
        set({ lastActivity: Date.now() });
      },

      isExpired() {
        const { lastActivity, token } = get();
        // No session → not expired (just empty)
        if (!token || lastActivity === null) return false;
        return Date.now() - lastActivity > SESSION_INACTIVITY_MS;
      },
    }),
    {
      name: 'buen-sabor-session',
      // Persist all fields — actions are excluded automatically by zustand/persist
    }
  )
);

// ---------------------------------------------------------------------------
// Individual selectors — NEVER destructure the store directly in components.
// Usage: const token = useSessionStore(selectSessionToken);
// ---------------------------------------------------------------------------

export const selectSessionToken = (s: SessionStoreState) => s.token;
export const selectSessionId = (s: SessionStoreState) => s.sessionId;
export const selectDisplayName = (s: SessionStoreState) => s.displayName;
export const selectAvatarColor = (s: SessionStoreState) => s.avatarColor;
export const selectBranchSlug = (s: SessionStoreState) => s.branchSlug;
export const selectBranchName = (s: SessionStoreState) => s.branchName;
export const selectTableIdentifier = (s: SessionStoreState) => s.tableIdentifier;
export const selectTableName = (s: SessionStoreState) => s.tableName;
export const selectJoinedAt = (s: SessionStoreState) => s.joinedAt;
export const selectLastActivity = (s: SessionStoreState) => s.lastActivity;
export const selectHasSession = (s: SessionStoreState) => s.token !== null;

// Action selectors — stable references, no re-render on state changes
export const selectJoinAction = (s: SessionStoreState) => s.join;
export const selectClearAction = (s: SessionStoreState) => s.clear;
export const selectUpdateActivityAction = (s: SessionStoreState) => s.updateActivity;
export const selectIsExpiredAction = (s: SessionStoreState) => s.isExpired;

export { useSessionStore };
