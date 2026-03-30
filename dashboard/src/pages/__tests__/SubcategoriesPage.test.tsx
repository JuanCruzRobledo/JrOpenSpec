/**
 * SubcategoriesPage tests — S16 (CRUD modal) and S17 (category filter).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import SubcategoriesPage from '../SubcategoriesPage';
import type { Subcategory } from '@/types/subcategory';
import type { Category } from '@/types/category';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const mockSubcategories: Subcategory[] = [
  {
    id: 1,
    nombre: 'Ensaladas',
    imagen_url: null,
    categoria_id: 1,
    categoria_nombre: 'Entradas',
    orden: 1,
    estado: 'activo',
    productos_count: 3,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    nombre: 'Sopas',
    imagen_url: null,
    categoria_id: 2,
    categoria_nombre: 'Calientes',
    orden: 1,
    estado: 'activo',
    productos_count: 2,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockCategories: Category[] = [
  {
    id: 1,
    nombre: 'Entradas',
    icono: null,
    imagen_url: null,
    orden: 1,
    estado: 'activo',
    es_home: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockCreate = vi.fn();
const mockUpdate = vi.fn();
const mockRemove = vi.fn();
const mockRefresh = vi.fn();

vi.mock('@/hooks/useCrud', () => ({
  useCrud: () => ({
    items: mockSubcategories,
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

vi.mock('@/services/subcategory.service', () => ({
  subcategoryService: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));

vi.mock('@/services/category.service', () => ({
  categoryService: {
    // Inline mock data — vi.mock factories are hoisted above const declarations
    list: vi.fn().mockResolvedValue({
      data: [
        {
          id: 1,
          nombre: 'Entradas',
          icono: null,
          imagen_url: null,
          orden: 1,
          estado: 'activo',
          es_home: false,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
      meta: { page: 1, limit: 100, total: 1 },
    }),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));

vi.mock('@/lib/logger', () => ({
  logger: { error: vi.fn(), warn: vi.fn(), debug: vi.fn(), info: vi.fn() },
}));

vi.mock('@/utils/helpContent', () => ({
  helpContent: { subcategories: { title: 'Help', sections: [] } },
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
      <SubcategoriesPage />
    </MemoryRouter>,
  );
}

describe('S16 — SubcategoriesPage opens create modal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Crear subcategoria button', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /crear subcategor/i })).toBeInTheDocument();
  });

  it('opens modal on button click', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /crear subcategor/i }));

    expect(screen.getByRole('heading', { name: /crear subcategor/i })).toBeInTheDocument();
  });
});

describe('S17 — SubcategoriesPage shows all subcategories by default', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all subcategories in the table', () => {
    renderPage();
    expect(screen.getByText('Ensaladas')).toBeInTheDocument();
    expect(screen.getByText('Sopas')).toBeInTheDocument();
  });
});
