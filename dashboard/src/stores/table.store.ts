/**
 * Table store — manages table list, filters, and urgency-sorted views.
 *
 * NEVER destructure: use individual selectors always.
 */
import { create } from 'zustand';
import { tableService } from '@/services/table.service';
import { logger } from '@/lib/logger';
import type {
  Table,
  TableCreate,
  TableBatchCreate,
  TableUpdate,
  TableStatus,
  TableStatusUpdate,
} from '@/types/table';
import type { PaginationMeta } from '@/types/api';

const EMPTY_ARRAY: Table[] = [];

// Urgency scores for table status — higher = more urgent
const URGENCY_SCORES: Record<TableStatus, number> = {
  cuenta: 50,
  pedido_solicitado: 40,
  pedido_cumplido: 30,
  ocupada: 20,
  libre: 10,
  inactiva: 0,
};

interface TableState {
  tables: Table[];
  isLoading: boolean;
  error: string | null;
  meta: PaginationMeta | null;
  sectorFilter: number | null;
  statusFilter: TableStatus | null;

  fetchTables: (branchId: number, page?: number, limit?: number) => Promise<void>;
  createTable: (branchId: number, data: TableCreate) => Promise<Table>;
  createTableBatch: (branchId: number, data: TableBatchCreate) => Promise<Table[]>;
  updateTable: (branchId: number, id: number, data: TableUpdate) => Promise<Table>;
  updateTableStatus: (branchId: number, id: number, data: TableStatusUpdate) => Promise<Table>;
  removeTable: (branchId: number, id: number) => Promise<void>;
  setSectorFilter: (sectorId: number | null) => void;
  setStatusFilter: (status: TableStatus | null) => void;
  clearTables: () => void;
}

export const useTableStore = create<TableState>()((set) => ({
  tables: EMPTY_ARRAY,
  isLoading: false,
  error: null,
  meta: null,
  sectorFilter: null,
  statusFilter: null,

  fetchTables: async (branchId, page = 1, limit = 100) => {
    set({ isLoading: true, error: null });
    try {
      const res = await tableService.list(branchId, { page, limit });
      set({ tables: res.data, meta: res.meta, isLoading: false });
    } catch (err) {
      logger.error('Failed to fetch tables', err);
      set({ error: 'Error al cargar mesas', isLoading: false });
    }
  },

  createTable: async (branchId, data) => {
    const table = await tableService.create(branchId, data);
    set((s) => ({ tables: [...s.tables, table] }));
    return table;
  },

  createTableBatch: async (branchId, data) => {
    const tables = await tableService.createBatch(branchId, data);
    set((s) => ({ tables: [...s.tables, ...tables] }));
    return tables;
  },

  updateTable: async (branchId, id, data) => {
    const updated = await tableService.update(branchId, id, data);
    set((s) => ({
      tables: s.tables.map((t) => (t.id === id ? updated : t)),
    }));
    return updated;
  },

  updateTableStatus: async (branchId, id, data) => {
    const updated = await tableService.updateStatus(branchId, id, data);
    set((s) => ({
      tables: s.tables.map((t) => (t.id === id ? updated : t)),
    }));
    return updated;
  },

  removeTable: async (branchId, id) => {
    await tableService.remove(branchId, id);
    set((s) => ({
      tables: s.tables.filter((t) => t.id !== id),
    }));
  },

  setSectorFilter: (sectorId) => set({ sectorFilter: sectorId }),
  setStatusFilter: (status) => set({ statusFilter: status }),
  clearTables: () =>
    set({
      tables: EMPTY_ARRAY,
      meta: null,
      error: null,
      sectorFilter: null,
      statusFilter: null,
    }),
}));

// Selectors — use these, never destructure the store
export const selectTables = (s: TableState) => s.tables;
export const selectTablesLoading = (s: TableState) => s.isLoading;
export const selectTablesError = (s: TableState) => s.error;
export const selectTablesMeta = (s: TableState) => s.meta;
export const selectSectorFilter = (s: TableState) => s.sectorFilter;
export const selectStatusFilter = (s: TableState) => s.statusFilter;

/** Returns tables filtered by current sector and status, sorted by urgency (most urgent first). */
export const selectFilteredTablesByUrgency = (s: TableState): Table[] => {
  let filtered = s.tables;

  if (s.sectorFilter !== null) {
    filtered = filtered.filter((t) => t.sector_id === s.sectorFilter);
  }

  if (s.statusFilter !== null) {
    filtered = filtered.filter((t) => t.estado === s.statusFilter);
  }

  return [...filtered].sort((a, b) => {
    const scoreDiff = URGENCY_SCORES[b.estado] - URGENCY_SCORES[a.estado];
    if (scoreDiff !== 0) return scoreDiff;
    // Secondary: oldest status_changed_at first (ascending)
    const timeA = a.status_changed_at ? new Date(a.status_changed_at).getTime() : 0;
    const timeB = b.status_changed_at ? new Date(b.status_changed_at).getTime() : 0;
    return timeA - timeB;
  });
};

/** Returns urgency score for a given table status. */
export const getUrgencyScore = (status: TableStatus): number =>
  URGENCY_SCORES[status];
