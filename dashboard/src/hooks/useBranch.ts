import { useShallow } from 'zustand/react/shallow';
import { useBranchStore } from '@/stores/branch.store';

/**
 * Convenience hook for branch state.
 */
export function useBranch() {
  const branches = useBranchStore(useShallow((s) => s.branches));
  const selectedBranchId = useBranchStore((s) => s.selectedBranchId);
  const isLoading = useBranchStore((s) => s.isLoading);
  const selectBranch = useBranchStore((s) => s.selectBranch);
  const fetchBranches = useBranchStore((s) => s.fetchBranches);

  const selectedBranch = branches.find((b) => b.id === selectedBranchId) ?? null;

  return {
    branches,
    selectedBranchId,
    selectedBranch,
    isLoading,
    selectBranch,
    fetchBranches,
  };
}
