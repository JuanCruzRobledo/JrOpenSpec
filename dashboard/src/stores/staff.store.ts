/**
 * Staff store — manages staff list, search, role filter, and pagination.
 *
 * NEVER destructure: use individual selectors always.
 */
import { create } from 'zustand';
import { staffService } from '@/services/staff.service';
import { logger } from '@/lib/logger';
import type { Staff, StaffCreate, StaffUpdate } from '@/types/staff';
import type { PaginationMeta } from '@/types/api';

const EMPTY_ARRAY: Staff[] = [];
const DEFAULT_PAGE = 1;
const DEFAULT_LIMIT = 20;

interface StaffState {
  staff: Staff[];
  isLoading: boolean;
  error: string | null;
  meta: PaginationMeta | null;
  searchQuery: string;
  roleFilter: string | null;
  page: number;
  limit: number;

  fetchStaff: (page?: number, limit?: number) => Promise<void>;
  createStaff: (data: StaffCreate) => Promise<Staff>;
  updateStaff: (id: number, data: StaffUpdate) => Promise<Staff>;
  removeStaff: (id: number) => Promise<void>;
  setSearchQuery: (query: string) => void;
  setRoleFilter: (role: string | null) => void;
  setPage: (page: number) => void;
  clearStaff: () => void;
}

export const useStaffStore = create<StaffState>()((set, get) => ({
  staff: EMPTY_ARRAY,
  isLoading: false,
  error: null,
  meta: null,
  searchQuery: '',
  roleFilter: null,
  page: DEFAULT_PAGE,
  limit: DEFAULT_LIMIT,

  fetchStaff: async (page?: number, limit?: number) => {
    const currentPage = page ?? get().page;
    const currentLimit = limit ?? get().limit;
    set({ isLoading: true, error: null });
    try {
      const res = await staffService.list({
        page: currentPage,
        limit: currentLimit,
      });
      set({
        staff: res.data,
        meta: res.meta,
        page: currentPage,
        isLoading: false,
      });
    } catch (err) {
      logger.error('Failed to fetch staff', err);
      set({ error: 'Error al cargar personal', isLoading: false });
    }
  },

  createStaff: async (data) => {
    const member = await staffService.create(data);
    set((s) => ({ staff: [...s.staff, member] }));
    return member;
  },

  updateStaff: async (id, data) => {
    const updated = await staffService.update(id, data);
    set((s) => ({
      staff: s.staff.map((m) => (m.id === id ? updated : m)),
    }));
    return updated;
  },

  removeStaff: async (id) => {
    await staffService.remove(id);
    set((s) => ({
      staff: s.staff.filter((m) => m.id !== id),
    }));
  },

  setSearchQuery: (query) => set({ searchQuery: query, page: DEFAULT_PAGE }),
  setRoleFilter: (role) => set({ roleFilter: role, page: DEFAULT_PAGE }),
  setPage: (page) => set({ page }),
  clearStaff: () =>
    set({
      staff: EMPTY_ARRAY,
      meta: null,
      error: null,
      searchQuery: '',
      roleFilter: null,
      page: DEFAULT_PAGE,
    }),
}));

// Selectors — use these, never destructure the store
export const selectStaff = (s: StaffState) => s.staff;
export const selectStaffLoading = (s: StaffState) => s.isLoading;
export const selectStaffError = (s: StaffState) => s.error;
export const selectStaffMeta = (s: StaffState) => s.meta;
export const selectSearchQuery = (s: StaffState) => s.searchQuery;
export const selectRoleFilter = (s: StaffState) => s.roleFilter;
export const selectStaffPage = (s: StaffState) => s.page;

/** Returns staff filtered by search query and role filter (client-side). */
export const selectFilteredStaff = (s: StaffState): Staff[] => {
  let filtered = s.staff;

  if (s.searchQuery) {
    const query = s.searchQuery.toLowerCase();
    filtered = filtered.filter(
      (m) =>
        m.nombre_completo.toLowerCase().includes(query) ||
        m.email.toLowerCase().includes(query),
    );
  }

  if (s.roleFilter !== null) {
    filtered = filtered.filter((m) => m.rol === s.roleFilter);
  }

  return filtered;
};
