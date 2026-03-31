/**
 * useTableGrid — encapsulates table grid logic: fetch, filter, sort by urgency, polling.
 */
import { useEffect, useRef, useMemo, useState, useCallback } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useTableStore, selectFilteredTablesByUrgency } from '@/stores/table.store';
import { useSectorStore, selectSectors } from '@/stores/sector.store';
import { useBranch } from '@/hooks/useBranch';
import type { TableStatus } from '@/types/table';

const POLL_INTERVAL_MS = 15_000;

export function useTableGrid() {
  const { selectedBranchId } = useBranch();
  const branchId = selectedBranchId!;

  // Table store — individual selectors (never destructure)
  const fetchTables = useTableStore((s) => s.fetchTables);
  const isLoading = useTableStore((s) => s.isLoading);
  const error = useTableStore((s) => s.error);
  const sectorFilter = useTableStore((s) => s.sectorFilter);
  const statusFilter = useTableStore((s) => s.statusFilter);
  const setSectorFilter = useTableStore((s) => s.setSectorFilter);
  const setStatusFilter = useTableStore((s) => s.setStatusFilter);
  const filteredTables = useTableStore(useShallow(selectFilteredTablesByUrgency));

  // Sector store
  const fetchSectors = useSectorStore((s) => s.fetchSectors);
  const sectors = useSectorStore(useShallow(selectSectors));

  // Local search query (client-side filter on table code/number)
  const [searchQuery, setSearchQuery] = useState('');

  // Stable ref for branchId to avoid stale closures in interval
  const branchIdRef = useRef(branchId);
  branchIdRef.current = branchId;

  // Initial fetch
  useEffect(() => {
    fetchTables(branchId);
    fetchSectors(branchId);
  }, [branchId, fetchTables, fetchSectors]);

  // Polling
  useEffect(() => {
    const interval = setInterval(() => {
      fetchTables(branchIdRef.current);
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchTables]);

  // Client-side search filter on top of store's urgency-sorted filtered result
  const tables = useMemo(() => {
    if (!searchQuery) return filteredTables;
    const q = searchQuery.toLowerCase();
    return filteredTables.filter(
      (t) =>
        (t.codigo?.toLowerCase().includes(q) ?? false) ||
        String(t.numero).includes(q),
    );
  }, [filteredTables, searchQuery]);

  const refresh = useCallback(() => {
    fetchTables(branchId);
  }, [branchId, fetchTables]);

  return {
    tables,
    sectors,
    isLoading,
    error,
    sectorFilter,
    statusFilter,
    searchQuery,
    setSectorFilter,
    setStatusFilter: setStatusFilter as (status: TableStatus | null) => void,
    setSearchQuery,
    refresh,
  };
}
