import { useEffect } from 'react';
import type { MenuResponse } from '@/types/menu';
import type { ApiError } from '@/types/api';
import {
  useMenuStore,
  selectMenuData,
  selectMenuIsLoading,
  selectMenuIsBackgroundRefreshing,
  selectMenuError,
  selectFetchMenuAction,
  selectBackgroundRefreshAction,
} from '@/stores/menu.store';

interface UseMenuDataResult {
  data: MenuResponse | null;
  isLoading: boolean;
  isBackgroundRefreshing: boolean;
  error: ApiError | null;
}

/**
 * Fetches and manages menu data for a given branch slug.
 *
 * Strategy: stale-while-revalidate
 * - No data: fetch immediately (blocking load)
 * - Data present + stale: return stale immediately + trigger background refresh
 * - Data present + fresh: return as-is, no fetch
 *
 * The caller is responsible for showing a staleness indicator when
 * isBackgroundRefreshing is true (Hard Stop Rule #1).
 */
export function useMenuData(slug: string | undefined): UseMenuDataResult {
  const data = useMenuStore(selectMenuData);
  const isLoading = useMenuStore(selectMenuIsLoading);
  const isBackgroundRefreshing = useMenuStore(selectMenuIsBackgroundRefreshing);
  const error = useMenuStore(selectMenuError);
  const fetchMenu = useMenuStore(selectFetchMenuAction);
  const backgroundRefresh = useMenuStore(selectBackgroundRefreshAction);

  useEffect(() => {
    if (!slug) return;

    // Read current store state directly to avoid stale closure — store actions
    // access their own internal state via get(), so calling them is always current.
    const { data: currentData, isStale } = useMenuStore.getState();

    if (!currentData || isStale()) {
      if (currentData) {
        // Stale data exists — background revalidate, show stale immediately
        void backgroundRefresh(slug);
      } else {
        // No data at all — blocking fetch
        void fetchMenu(slug);
      }
    }
  }, [slug, fetchMenu, backgroundRefresh]);

  return { data, isLoading, isBackgroundRefreshing, error };
}
