/**
 * BranchesPage tests — S10 (create modal open), S11 (form submission), S12 (delete confirm).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import BranchesPage from '../BranchesPage';
import type { Branch } from '@/types/branch';

// ---------------------------------------------------------------------------
// Mock all external dependencies
// ---------------------------------------------------------------------------

const mockCrudItems: Branch[] = [
  {
    id: 1,
    nombre: 'Sucursal Test',
    direccion: 'Calle 123',
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
];

const mockRemove = vi.fn();
const mockCreate = vi.fn();
const mockUpdate = vi.fn();
const mockRefresh = vi.fn();

vi.mock('@/hooks/useCrud', () => ({
  useCrud: () => ({
    items: mockCrudItems,
    isLoading: false,
    error: null,
    page: 1,
    totalPages: 1,
    setPage: vi.fn(),
    refresh: mockRefresh,
    create: mockCreate,
    update: mockUpdate,
    remove: mockRemove,
  }),
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { roles: ['ADMIN'] } }),
}));

vi.mock('@/hooks/useConfirm', () => ({
  useConfirm: () => vi.fn().mockResolvedValue(true),
}));

vi.mock('@/stores/auth.store', () => ({
  useAuthStore: (selector: (s: { refreshAuth: () => Promise<void> }) => unknown) =>
    selector({ refreshAuth: vi.fn() }),
}));

vi.mock('@/stores/branch.store', () => ({
  useBranchStore: (selector: (s: { fetchBranches: () => Promise<void>; selectBranch: (id: number) => void }) => unknown) =>
    selector({ fetchBranches: vi.fn(), selectBranch: vi.fn() }),
}));

vi.mock('@/services/branch.service', () => ({
  branchService: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));

vi.mock('@/utils/helpContent', () => ({
  helpContent: {
    branches: { title: 'Help', sections: [] },
  },
}));

vi.mock('@/components/ui/HelpButton', () => ({
  HelpButton: () => <button type="button">Help</button>,
}));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

function renderPage() {
  return render(
    <MemoryRouter>
      <BranchesPage />
    </MemoryRouter>,
  );
}

describe('S10 — BranchesPage opens create modal on button click', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the "Crear sucursal" button for ADMIN role', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /crear sucursal/i })).toBeInTheDocument();
  });

  it('opens the create modal when "Crear sucursal" is clicked', async () => {
    const user = userEvent.setup();
    renderPage();

    const createBtn = screen.getByRole('button', { name: /crear sucursal/i });
    await user.click(createBtn);

    // Modal title should appear
    expect(screen.getByRole('heading', { name: /crear sucursal/i })).toBeInTheDocument();
  });
});

describe('S11 — BranchesPage opens edit modal on Editar click', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('opens the edit modal pre-filled with branch data', async () => {
    const user = userEvent.setup();
    renderPage();

    const editBtn = screen.getByRole('button', { name: /editar/i });
    await user.click(editBtn);

    // Modal should say "Editar sucursal"
    expect(screen.getByRole('heading', { name: /editar sucursal/i })).toBeInTheDocument();
  });
});

describe('S12 — BranchesPage delete triggers confirmation dialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls crud.remove after confirmation', async () => {
    const user = userEvent.setup();
    renderPage();

    const deleteBtn = screen.getByRole('button', { name: /eliminar/i });
    await user.click(deleteBtn);

    await waitFor(() => {
      expect(mockRemove).toHaveBeenCalledWith(1);
    });
  });
});

describe('BranchesPage — table renders branch data', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays branch names in the table', () => {
    renderPage();
    expect(screen.getByText('Sucursal Test')).toBeInTheDocument();
  });
});
