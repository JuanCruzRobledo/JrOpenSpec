import { create } from 'zustand';
import { TOAST_DURATION_MS, TOAST_MAX, INSTALL_BANNER_DISMISSED_KEY, INSTALL_BANNER_COOLDOWN_MS } from '@/config/constants';

// ---------------------------------------------------------------------------
// Toast types
// ---------------------------------------------------------------------------

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  readonly id: string;
  readonly message: string;
  readonly variant: ToastVariant;
  /** Unix timestamp when this toast should be auto-removed */
  readonly expiresAt: number;
}

// ---------------------------------------------------------------------------
// State & Actions interface
// NOT persisted — UI state is ephemeral
// ---------------------------------------------------------------------------

interface UiStoreState {
  filterDrawerOpen: boolean;
  installBannerVisible: boolean;
  toasts: Toast[];

  // Filter drawer actions
  openFilterDrawer: () => void;
  closeFilterDrawer: () => void;

  // Install banner actions
  /**
   * Shows the install banner if:
   * 1. It was never dismissed, OR
   * 2. The dismiss cooldown (7 days) has elapsed
   */
  showInstallBanner: () => void;
  /** Dismisses banner and records timestamp in localStorage */
  hideInstallBanner: () => void;

  // Toast actions
  /**
   * Adds a toast. Auto-removes after TOAST_DURATION_MS.
   * Enforces max 5 toasts — oldest is removed when limit is exceeded.
   */
  addToast: (message: string, variant?: ToastVariant) => void;
  removeToast: (id: string) => void;
}

// ---------------------------------------------------------------------------
// Store creation — NOT persisted
// ---------------------------------------------------------------------------

const useUiStore = create<UiStoreState>()((set, get) => ({
  filterDrawerOpen: false,
  installBannerVisible: false,
  toasts: [],

  openFilterDrawer() {
    set({ filterDrawerOpen: true });
  },

  closeFilterDrawer() {
    set({ filterDrawerOpen: false });
  },

  showInstallBanner() {
    try {
      const raw = localStorage.getItem(INSTALL_BANNER_DISMISSED_KEY);
      if (raw) {
        const dismissedAt = parseInt(raw, 10);
        if (!isNaN(dismissedAt) && Date.now() - dismissedAt < INSTALL_BANNER_COOLDOWN_MS) {
          // Still within cooldown — do not show
          return;
        }
      }
    } catch {
      // localStorage unavailable — show anyway
    }
    set({ installBannerVisible: true });
  },

  hideInstallBanner() {
    try {
      localStorage.setItem(INSTALL_BANNER_DISMISSED_KEY, String(Date.now()));
    } catch {
      // Ignore storage errors
    }
    set({ installBannerVisible: false });
  },

  addToast(message, variant = 'info') {
    // crypto.randomUUID() requires a secure context (HTTPS/localhost).
    // Fallback for LAN testing over plain HTTP.
    const id = typeof crypto?.randomUUID === 'function'
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2) + Date.now().toString(36);
    const expiresAt = Date.now() + TOAST_DURATION_MS;
    const toast: Toast = { id, message, variant, expiresAt };

    set((state) => {
      // Enforce max 5 toasts — drop oldest when at capacity
      const existing = state.toasts.length >= TOAST_MAX
        ? state.toasts.slice(-(TOAST_MAX - 1))
        : state.toasts;
      return { toasts: [...existing, toast] };
    });

    // Schedule auto-removal
    setTimeout(() => {
      get().removeToast(id);
    }, TOAST_DURATION_MS);
  },

  removeToast(id) {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },
}));

// ---------------------------------------------------------------------------
// Individual selectors
// ---------------------------------------------------------------------------

export const selectFilterDrawerOpen = (s: UiStoreState) => s.filterDrawerOpen;
export const selectInstallBannerVisible = (s: UiStoreState) => s.installBannerVisible;
export const selectToasts = (s: UiStoreState) => s.toasts;

// Action selectors
export const selectOpenFilterDrawerAction = (s: UiStoreState) => s.openFilterDrawer;
export const selectCloseFilterDrawerAction = (s: UiStoreState) => s.closeFilterDrawer;
export const selectShowInstallBannerAction = (s: UiStoreState) => s.showInstallBanner;
export const selectHideInstallBannerAction = (s: UiStoreState) => s.hideInstallBanner;
export const selectAddToastAction = (s: UiStoreState) => s.addToast;
export const selectRemoveToastAction = (s: UiStoreState) => s.removeToast;

export { useUiStore };
