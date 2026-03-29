import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { MenuResponse } from '@/types/menu';
import type { ApiError } from '@/types/api';
import { CACHE_TTL_MS } from '@/config/constants';
import { getMenu } from '@/services/menu.service';

// ---------------------------------------------------------------------------
// State & Actions interface
// ---------------------------------------------------------------------------

interface MenuStoreState {
  data: MenuResponse | null;
  /** Unix timestamp (ms) when data was last fetched */
  fetchedAt: number | null;
  isLoading: boolean;
  /** True while a background revalidation is in progress (stale data is shown) */
  isBackgroundRefreshing: boolean;
  error: ApiError | null;

  // Actions
  fetchMenu: (slug: string) => Promise<void>;
  /**
   * Stale-while-revalidate: returns cached data immediately,
   * triggers background refresh if stale. Shows staleness indicator.
   */
  backgroundRefresh: (slug: string) => Promise<void>;
  isStale: () => boolean;
  clearMenu: () => void;
}

// ---------------------------------------------------------------------------
// Store creation — persisted to localStorage under 'buen-sabor-menu-cache'
// ---------------------------------------------------------------------------

const useMenuStore = create<MenuStoreState>()(
  persist(
    (set, get) => ({
      data: null,
      fetchedAt: null,
      isLoading: false,
      isBackgroundRefreshing: false,
      error: null,

      isStale() {
        const { fetchedAt } = get();
        if (fetchedAt === null) return true;
        return Date.now() - fetchedAt > CACHE_TTL_MS;
      },

      async fetchMenu(slug) {
        set({ isLoading: true, error: null });
        try {
          const data = await getMenu(slug);
          set({ data, fetchedAt: Date.now(), isLoading: false, error: null });
        } catch (err) {
          const apiError: ApiError = {
            status: 0,
            code: 'FETCH_ERROR',
            message: err instanceof Error ? err.message : 'Unknown error',
          };
          set({ isLoading: false, error: apiError });
        }
      },

      async backgroundRefresh(slug) {
        // Only refresh if stale and not already refreshing
        if (!get().isStale() || get().isBackgroundRefreshing) return;
        set({ isBackgroundRefreshing: true });
        try {
          const data = await getMenu(slug);
          set({ data, fetchedAt: Date.now(), isBackgroundRefreshing: false, error: null });
        } catch {
          // Background refresh failure is silent — stale data remains visible
          // The staleness indicator stays shown since fetchedAt is not updated
          set({ isBackgroundRefreshing: false });
        }
      },

      clearMenu() {
        set({ data: null, fetchedAt: null, isLoading: false, isBackgroundRefreshing: false, error: null });
      },
    }),
    {
      name: 'buen-sabor-menu-cache',
      // Only persist the data and fetchedAt — not loading/error states
      partialize: (state) => ({
        data: state.data,
        fetchedAt: state.fetchedAt,
      }),
    }
  )
);

// ---------------------------------------------------------------------------
// Individual selectors
// ---------------------------------------------------------------------------

export const selectMenuData = (s: MenuStoreState) => s.data;
export const selectMenuFetchedAt = (s: MenuStoreState) => s.fetchedAt;
export const selectMenuIsLoading = (s: MenuStoreState) => s.isLoading;
export const selectMenuIsBackgroundRefreshing = (s: MenuStoreState) => s.isBackgroundRefreshing;
export const selectMenuError = (s: MenuStoreState) => s.error;
export const selectMenuIsStale = (s: MenuStoreState) => s.isStale();

// Action selectors
export const selectFetchMenuAction = (s: MenuStoreState) => s.fetchMenu;
export const selectBackgroundRefreshAction = (s: MenuStoreState) => s.backgroundRefresh;
export const selectClearMenuAction = (s: MenuStoreState) => s.clearMenu;

export { useMenuStore };
