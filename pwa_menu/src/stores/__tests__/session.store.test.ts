/**
 * Unit tests for session.store.ts
 * Uses getState/setState directly — no React rendering needed.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { useSessionStore } from '../session.store';
import { SESSION_INACTIVITY_MS } from '@/config/constants';
import type { SessionJoinResponse } from '@/types/session';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function resetStore() {
  useSessionStore.getState().clear();
}

function makeJoinResponse(): SessionJoinResponse {
  return {
    token: 'test-jwt-token',
    sessionId: 'session-abc-123',
    expiresAt: new Date(Date.now() + 28_800_000).toISOString(),
    branch: {
      id: 1,
      slug: 'branch-central',
      name: 'Sucursal Central',
    },
    table: {
      identifier: 'mesa-5',
      displayName: 'Mesa 5',
    },
  };
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeEach(() => {
  resetStore();
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  resetStore();
});

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

describe('useSessionStore — initial state', () => {
  it('starts with token null', () => {
    const { token } = useSessionStore.getState();
    expect(token).toBeNull();
  });

  it('starts with lastActivity null', () => {
    const { lastActivity } = useSessionStore.getState();
    expect(lastActivity).toBeNull();
  });

  it('starts with sessionId null', () => {
    const { sessionId } = useSessionStore.getState();
    expect(sessionId).toBeNull();
  });

  it('starts with no branch or table info', () => {
    const state = useSessionStore.getState();
    expect(state.branchSlug).toBeNull();
    expect(state.tableIdentifier).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// join() action
// ---------------------------------------------------------------------------

describe('useSessionStore — join()', () => {
  it('populates token from response', () => {
    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    const { token } = useSessionStore.getState();
    expect(token).toBe('test-jwt-token');
  });

  it('populates sessionId from response', () => {
    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    expect(useSessionStore.getState().sessionId).toBe('session-abc-123');
  });

  it('populates branch and table from response', () => {
    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    const state = useSessionStore.getState();
    expect(state.branchSlug).toBe('branch-central');
    expect(state.branchName).toBe('Sucursal Central');
    expect(state.tableIdentifier).toBe('mesa-5');
    expect(state.tableName).toBe('Mesa 5');
  });

  it('sets displayName and avatarColor', () => {
    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    const state = useSessionStore.getState();
    expect(state.displayName).toBe('Matias');
    expect(state.avatarColor).toBe('#F97316');
  });

  it('sets lastActivity to current time on join', () => {
    const now = 1_700_000_000_000;
    vi.setSystemTime(now);

    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    expect(useSessionStore.getState().lastActivity).toBe(now);
  });

  it('sets joinedAt as ISO string on join', () => {
    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    const { joinedAt } = useSessionStore.getState();
    expect(joinedAt).toBeTruthy();
    expect(() => new Date(joinedAt!)).not.toThrow();
  });

  it('uses empty string when displayName is blank', () => {
    const response = makeJoinResponse();
    useSessionStore.getState().join(response, '', '#F97316');

    expect(useSessionStore.getState().displayName).toBe('');
  });
});

// ---------------------------------------------------------------------------
// clear() action
// ---------------------------------------------------------------------------

describe('useSessionStore — clear()', () => {
  it('resets all fields to initial state after a join', () => {
    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');
    useSessionStore.getState().clear();

    const state = useSessionStore.getState();
    expect(state.token).toBeNull();
    expect(state.sessionId).toBeNull();
    expect(state.lastActivity).toBeNull();
    expect(state.branchSlug).toBeNull();
    expect(state.tableIdentifier).toBeNull();
    expect(state.displayName).toBe('');
  });
});

// ---------------------------------------------------------------------------
// updateActivity() action
// ---------------------------------------------------------------------------

describe('useSessionStore — updateActivity()', () => {
  it('updates lastActivity to current Date.now()', () => {
    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    const later = 1_700_000_060_000;
    vi.setSystemTime(later);

    useSessionStore.getState().updateActivity();

    expect(useSessionStore.getState().lastActivity).toBe(later);
  });
});

// ---------------------------------------------------------------------------
// isExpired() — S4 and S25
// ---------------------------------------------------------------------------

describe('useSessionStore — isExpired() (S4 + S25)', () => {
  it('returns false when no session exists (no token)', () => {
    // No join called — token is null
    const expired = useSessionStore.getState().isExpired();
    expect(expired).toBe(false);
  });

  it('returns false when lastActivity is null (no session)', () => {
    // Edge case: someone set token but not lastActivity (shouldn't happen normally)
    useSessionStore.setState({ token: 'some-token', lastActivity: null });
    const expired = useSessionStore.getState().isExpired();
    expect(expired).toBe(false);
  });

  it('S25: returns false when session is within the 8h window', () => {
    const startTime = 1_700_000_000_000;
    vi.setSystemTime(startTime);

    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    // Advance time by 7 hours (within 8h window)
    vi.setSystemTime(startTime + 7 * 60 * 60 * 1000);

    const expired = useSessionStore.getState().isExpired();
    expect(expired).toBe(false);
  });

  it('S4: returns true when inactivity exceeds 8 hours (SESSION_INACTIVITY_MS)', () => {
    const startTime = 1_700_000_000_000;
    vi.setSystemTime(startTime);

    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    // Advance time beyond the inactivity window
    vi.setSystemTime(startTime + SESSION_INACTIVITY_MS + 1);

    const expired = useSessionStore.getState().isExpired();
    expect(expired).toBe(true);
  });

  it('S4: is NOT expired exactly at SESSION_INACTIVITY_MS boundary', () => {
    const startTime = 1_700_000_000_000;
    vi.setSystemTime(startTime);

    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    // Exactly at the boundary — not yet expired (> not >=)
    vi.setSystemTime(startTime + SESSION_INACTIVITY_MS);

    const expired = useSessionStore.getState().isExpired();
    expect(expired).toBe(false);
  });

  it('S4: updateActivity resets the expiry window', () => {
    const startTime = 1_700_000_000_000;
    vi.setSystemTime(startTime);

    const response = makeJoinResponse();
    useSessionStore.getState().join(response, 'Matias', '#F97316');

    // Advance near expiry
    const nearExpiry = startTime + SESSION_INACTIVITY_MS - 1000;
    vi.setSystemTime(nearExpiry);

    // User is still active — update activity
    useSessionStore.getState().updateActivity();

    // Advance another 7 hours from last activity — should not be expired
    vi.setSystemTime(nearExpiry + 7 * 60 * 60 * 1000);

    const expired = useSessionStore.getState().isExpired();
    expect(expired).toBe(false);
  });
});
