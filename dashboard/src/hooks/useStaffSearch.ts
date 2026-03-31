/**
 * useStaffSearch — hook for debounced search + role filter state.
 * Wraps staff store selectors with a debounced search handler.
 */
import { useEffect, useRef, useCallback } from 'react';
import { useShallow } from 'zustand/react/shallow';
import {
  useStaffStore,
  selectFilteredStaff,
  selectStaffLoading,
  selectStaffError,
  selectSearchQuery,
  selectRoleFilter,
  selectStaffMeta,
  selectStaffPage,
} from '@/stores/staff.store';

const DEBOUNCE_MS = 300;

export function useStaffSearch() {
  const filteredStaff = useStaffStore(useShallow(selectFilteredStaff));
  const isLoading = useStaffStore(selectStaffLoading);
  const error = useStaffStore(selectStaffError);
  const searchQuery = useStaffStore(selectSearchQuery);
  const roleFilter = useStaffStore(selectRoleFilter);
  const meta = useStaffStore(selectStaffMeta);
  const page = useStaffStore(selectStaffPage);

  const fetchStaff = useStaffStore((s) => s.fetchStaff);
  const setSearchQuery = useStaffStore((s) => s.setSearchQuery);
  const setRoleFilter = useStaffStore((s) => s.setRoleFilter);
  const setPage = useStaffStore((s) => s.setPage);

  // Debounced search
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearchChange = useCallback(
    (query: string) => {
      setSearchQuery(query);

      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      debounceRef.current = setTimeout(() => {
        // Search is client-side via selectFilteredStaff, but we could
        // add server-side search here if needed in the future.
      }, DEBOUNCE_MS);
    },
    [setSearchQuery],
  );

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  // Fetch on mount and page change
  useEffect(() => {
    fetchStaff(page);
  }, [page, fetchStaff]);

  const totalPages = meta ? Math.ceil(meta.total / meta.limit) : 1;

  return {
    staff: filteredStaff,
    isLoading,
    error,
    searchQuery,
    roleFilter,
    page,
    totalPages,
    handleSearchChange,
    setRoleFilter,
    setPage,
    refresh: fetchStaff,
  };
}
