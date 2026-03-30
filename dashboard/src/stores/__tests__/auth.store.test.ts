/**
 * Auth store tests — S1 through S6 spec scenarios.
 * All network calls are mocked via vi.mock; no real HTTP.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAuthStore } from '../auth.store';
import type { TokenResponse, UserProfile } from '@/types/auth';

// ---------------------------------------------------------------------------
// Mock the auth service module — all functions replaced with vi.fn()
// ---------------------------------------------------------------------------
vi.mock('@/services/auth.service', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    getMe: vi.fn(),
  },
}));

// Mock BroadcastChannel — not available in jsdom
const mockPostMessage = vi.fn();
const mockAddEventListener = vi.fn();
const mockClose = vi.fn();

vi.stubGlobal(
  'BroadcastChannel',
  vi.fn().mockImplementation(() => ({
    postMessage: mockPostMessage,
    addEventListener: mockAddEventListener,
    removeEventListener: vi.fn(),
    close: mockClose,
  })),
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockToken: TokenResponse = { access_token: 'test-access-token', token_type: 'bearer' };

const mockUser: UserProfile = {
  id: 1,
  email: 'admin@test.com',
  first_name: 'Admin',
  last_name: 'User',
  tenant_id: 10,
  branch_ids: [1, 2],
  roles: ['ADMIN'],
  is_superadmin: false,
};

function resetStore() {
  useAuthStore.setState({
    token: null,
    expiresAt: null,
    user: null,
    isAuthenticated: false,
    isLoading: false,
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('S1 — Successful login stores token and user', () => {
  let authService: typeof import('@/services/auth.service').authService;

  beforeEach(async () => {
    resetStore();
    vi.clearAllMocks();
    vi.useFakeTimers();
    authService = (await import('@/services/auth.service')).authService;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('sets token, expiresAt, isAuthenticated=true on successful login', async () => {
    vi.mocked(authService.login).mockResolvedValue(mockToken);
    vi.mocked(authService.getMe).mockResolvedValue(mockUser);

    await useAuthStore.getState().login('admin@test.com', 'password123');

    const state = useAuthStore.getState();
    expect(state.token).toBe('test-access-token');
    expect(state.isAuthenticated).toBe(true);
    expect(state.expiresAt).toBeGreaterThan(Date.now());
    expect(state.isLoading).toBe(false);
  });

  it('fetches and stores user profile after successful login', async () => {
    vi.mocked(authService.login).mockResolvedValue(mockToken);
    vi.mocked(authService.getMe).mockResolvedValue(mockUser);

    await useAuthStore.getState().login('admin@test.com', 'password123');

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(authService.getMe).toHaveBeenCalledWith('test-access-token');
  });
});

describe('S2 — Failed login does not update state', () => {
  let authService: typeof import('@/services/auth.service').authService;

  beforeEach(async () => {
    resetStore();
    vi.clearAllMocks();
    authService = (await import('@/services/auth.service')).authService;
  });

  it('throws error and resets isLoading when login fails', async () => {
    vi.mocked(authService.login).mockRejectedValue(new Error('Invalid credentials'));

    await expect(useAuthStore.getState().login('bad@test.com', 'wrong')).rejects.toThrow(
      'Invalid credentials',
    );

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
  });
});

describe('S3 — Logout clears state', () => {
  let authService: typeof import('@/services/auth.service').authService;

  beforeEach(async () => {
    resetStore();
    vi.clearAllMocks();
    authService = (await import('@/services/auth.service')).authService;
  });

  it('clears token, user, and isAuthenticated on logout', async () => {
    // Set up authenticated state
    useAuthStore.setState({
      token: 'existing-token',
      expiresAt: Date.now() + 900_000,
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
    });

    vi.mocked(authService.logout).mockResolvedValue(undefined);

    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.expiresAt).toBeNull();
  });

  it('calls logout API with the current token', () => {
    useAuthStore.setState({
      token: 'existing-token',
      expiresAt: Date.now() + 900_000,
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
    });

    vi.mocked(authService.logout).mockResolvedValue(undefined);

    useAuthStore.getState().logout();

    expect(authService.logout).toHaveBeenCalledWith('existing-token');
  });
});

describe('S4 — Token refresh updates token in state', () => {
  let authService: typeof import('@/services/auth.service').authService;

  beforeEach(async () => {
    resetStore();
    vi.clearAllMocks();
    vi.useFakeTimers();
    authService = (await import('@/services/auth.service')).authService;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('replaces token and keeps isAuthenticated=true after successful refresh', async () => {
    useAuthStore.setState({
      token: 'old-token',
      expiresAt: Date.now() + 60_000,
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
    });

    const refreshed: TokenResponse = { access_token: 'refreshed-token', token_type: 'bearer' };
    vi.mocked(authService.refresh).mockResolvedValue(refreshed);
    vi.mocked(authService.getMe).mockResolvedValue(mockUser);

    await useAuthStore.getState().refreshAuth();

    const state = useAuthStore.getState();
    expect(state.token).toBe('refreshed-token');
    expect(state.isAuthenticated).toBe(true);
    expect(state.expiresAt).toBeGreaterThan(Date.now());
  });
});

describe('S5 — Failed refresh triggers logout', () => {
  let authService: typeof import('@/services/auth.service').authService;

  beforeEach(async () => {
    resetStore();
    vi.clearAllMocks();
    authService = (await import('@/services/auth.service')).authService;
  });

  it('clears auth state when refresh API call fails', async () => {
    useAuthStore.setState({
      token: 'old-token',
      expiresAt: Date.now() + 60_000,
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
    });

    vi.mocked(authService.refresh).mockRejectedValue(new Error('Refresh expired'));
    // logout() will call authService.logout internally
    vi.mocked(authService.logout).mockResolvedValue(undefined);

    await useAuthStore.getState().refreshAuth();

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });
});

describe('S6 — setUser updates user in state', () => {
  beforeEach(() => {
    resetStore();
    vi.clearAllMocks();
  });

  it('replaces the user object in state', () => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true });

    const updatedUser: UserProfile = { ...mockUser, email: 'updated@test.com' };
    useAuthStore.getState().setUser(updatedUser);

    expect(useAuthStore.getState().user?.email).toBe('updated@test.com');
  });
});
