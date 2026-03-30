/**
 * CategoriesPage tests — S13 (CRUD modal open) and S14/S15 (filter + delete).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import CategoriesPage from '../CategoriesPage';
import type { Category } from '@/types/category';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const mockCategories: Category[] = [
  {
    id: 1,
    nombre: 'Entradas',
    icono: '🥗',
    imagen_url: null,
    orden: 1,
    estado: 'activo',
    es_home: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    nombre: 'Home',
    icono: null,
    imagen_url: null,
    orden: 0,
    estado: 'activo',
    es_home: true, // should be filtered out
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
    items: mockCategories,
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

vi.mock('@/hooks/useBranch', () => ({
  useBranch: () => ({ selectedBranchId: 1 }),
}));

vi.mock('@/hooks/useConfirm', () => ({
  useConfirm: () => vi.fn().mockResolvedValue(true),
}));

vi.mock('@/services/category.service', () => ({
  categoryService: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));

vi.mock('@/utils/helpContent', () => ({
  helpContent: { categories: { title: 'Help', sections: [] } },
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
      <CategoriesPage />
    </MemoryRouter>,
  );
}

describe('S13 — CategoriesPage opens create modal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Crear categoria button', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /crear categoria/i })).toBeInTheDocument();
  });

  it('opens create modal on button click', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /crear categoria/i }));

    expect(screen.getByRole('heading', { name: /crear categoria/i })).toBeInTheDocument();
  });
});

describe('S14 — CategoriesPage filters out es_home categories', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows non-home categories in the table', () => {
    renderPage();
    expect(screen.getByText('Entradas')).toBeInTheDocument();
  });

  it('hides categories with es_home=true', () => {
    renderPage();
    // "Home" category should NOT appear in the table cells (though "Home" text might appear in heading)
    const tableCells = screen.queryAllByRole('cell');
    const homeCell = tableCells.find((cell) => cell.textContent === 'Home');
    expect(homeCell).toBeUndefined();
  });
});

describe('S15 — CategoriesPage delete triggers confirm then remove', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls crud.remove after user confirms deletion', async () => {
    const user = userEvent.setup();
    renderPage();

    const deleteBtns = screen.getAllByRole('button', { name: /eliminar/i });
    await user.click(deleteBtns[0]);

    await waitFor(() => {
      expect(mockRemove).toHaveBeenCalled();
    });
  });
});
