/**
 * BranchSelector tests — S8 (renders branches list) and S9 (selection calls selectBranch).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BranchSelector } from '@/components/layout/BranchSelector';
import { useBranchStore } from '@/stores/branch.store';
import { useAuthStore } from '@/stores/auth.store';
import type { Branch } from '@/types/branch';

// ---------------------------------------------------------------------------
// Mock stores
// ---------------------------------------------------------------------------
vi.mock('@/stores/branch.store', () => ({
  useBranchStore: vi.fn(),
}));

vi.mock('@/stores/auth.store', () => ({
  useAuthStore: vi.fn(),
}));

// useShallow is used in BranchSelector — mock it to pass through
vi.mock('zustand/react/shallow', () => ({
  useShallow: (fn: unknown) => fn,
}));

// ---------------------------------------------------------------------------
// Test branches
// ---------------------------------------------------------------------------
const mockBranches: Branch[] = [
  {
    id: 1,
    nombre: 'Sucursal Centro',
    direccion: 'Av. Central 1',
    telefono: null,
    email: null,
    imagen_url: null,
    horario_apertura: '09:00',
    horario_cierre: '22:00',
    estado: 'activo',
    orden: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    nombre: 'Sucursal Norte',
    direccion: 'Av. Norte 200',
    telefono: null,
    email: null,
    imagen_url: null,
    horario_apertura: '10:00',
    horario_cierre: '23:00',
    estado: 'activo',
    orden: 2,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

function setupMocks({
  branches = mockBranches,
  selectedBranchId = null as number | null,
  isAuthenticated = true,
  isLoading = false,
} = {}) {
  const selectBranch = vi.fn();
  const fetchBranches = vi.fn();

  vi.mocked(useBranchStore).mockImplementation(
    (selector: (s: {
      branches: Branch[];
      selectedBranchId: number | null;
      selectBranch: typeof selectBranch;
      fetchBranches: typeof fetchBranches;
      isLoading: boolean;
    }) => unknown) =>
      selector({ branches, selectedBranchId, selectBranch, fetchBranches, isLoading }),
  );

  vi.mocked(useAuthStore).mockImplementation(
    (selector: (s: { isAuthenticated: boolean }) => unknown) =>
      selector({ isAuthenticated }),
  );

  return { selectBranch, fetchBranches };
}

describe('S8 — BranchSelector renders available branches', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders a select element with all branch options', () => {
    setupMocks();

    render(<BranchSelector />);

    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('Sucursal Centro')).toBeInTheDocument();
    expect(screen.getByText('Sucursal Norte')).toBeInTheDocument();
  });

  it('shows loading text when isLoading is true', () => {
    setupMocks({ isLoading: true });

    render(<BranchSelector />);

    expect(screen.getByText(/cargando/i)).toBeInTheDocument();
  });

  it('displays selectedBranchId as the current value', () => {
    setupMocks({ selectedBranchId: 1 });

    render(<BranchSelector />);

    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('1');
  });
});

describe('S9 — BranchSelector calls selectBranch on change', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls selectBranch with the chosen branch id when the value changes', async () => {
    const { selectBranch } = setupMocks({ selectedBranchId: null });
    const user = userEvent.setup();

    render(<BranchSelector />);

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '2');

    expect(selectBranch).toHaveBeenCalledWith(2);
  });
});
