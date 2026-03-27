import { useEffect } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useBranchStore } from '@/stores/branch.store';
import { useAuthStore } from '@/stores/auth.store';

interface Props {}

export function BranchSelector(_props: Props) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const branches = useBranchStore(useShallow((s) => s.branches));
  const selectedBranchId = useBranchStore((s) => s.selectedBranchId);
  const selectBranch = useBranchStore((s) => s.selectBranch);
  const fetchBranches = useBranchStore((s) => s.fetchBranches);
  const isLoading = useBranchStore((s) => s.isLoading);

  useEffect(() => {
    if (isAuthenticated && branches.length === 0) {
      fetchBranches();
    }
  }, [isAuthenticated, branches.length, fetchBranches]);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = Number(e.target.value);
    if (val) selectBranch(val);
  };

  return (
    <select
      value={selectedBranchId ?? ''}
      onChange={handleChange}
      disabled={isLoading}
      className="h-9 rounded-lg border border-border-default bg-bg-surface px-3 text-sm text-text-primary focus:outline-none focus:border-border-focus focus:ring-1 focus:ring-border-focus appearance-none min-w-[180px]"
      aria-label="Seleccionar sucursal"
    >
      <option value="">
        {isLoading ? 'Cargando...' : 'Seleccionar sucursal'}
      </option>
      {branches.map((b) => (
        <option key={b.id} value={b.id}>
          {b.nombre}
        </option>
      ))}
    </select>
  );
}
