/**
 * Branch store — tracks the selected branch and available branches list.
 * Only selectedBranchId is persisted to localStorage.
 *
 * NEVER destructure: use individual selectors always.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { branchService } from '@/services/branch.service';
import { logger } from '@/lib/logger';
import type { Branch } from '@/types/branch';

interface BranchState {
  selectedBranchId: number | null;
  branches: Branch[];
  isLoading: boolean;
  selectBranch: (id: number) => void;
  fetchBranches: () => Promise<void>;
  clearBranches: () => void;
}

export const useBranchStore = create<BranchState>()(
  persist(
    (set) => ({
      selectedBranchId: null,
      branches: [],
      isLoading: false,

      selectBranch: (id: number) => set({ selectedBranchId: id }),

      fetchBranches: async () => {
        set({ isLoading: true });
        try {
          const res = await branchService.list({ page: 1, limit: 100 });
          set({ branches: res.data, isLoading: false });
        } catch (err) {
          logger.error('Failed to fetch branches', err);
          set({ isLoading: false });
        }
      },

      clearBranches: () =>
        set({ branches: [], selectedBranchId: null }),
    }),
    {
      name: 'buen-sabor-branch',
      partialize: (s) => ({ selectedBranchId: s.selectedBranchId }),
    },
  ),
);
