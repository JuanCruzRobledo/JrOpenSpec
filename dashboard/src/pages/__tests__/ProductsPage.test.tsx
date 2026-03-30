/**
 * ProductsPage tests — S18 (product list), S19 (price display in pesos), S20 (batch price modal).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ProductsPage from '../ProductsPage';
import type { Product } from '@/types/product';
import type { Category } from '@/types/category';
import type { Subcategory } from '@/types/subcategory';

// ---------------------------------------------------------------------------
// Mock data — prices in CENTS
// ---------------------------------------------------------------------------
const mockProducts: Product[] = [
  {
    id: 1,
    nombre: 'Milanesa napolitana',
    descripcion: 'Con jamon y queso',
    categoria_id: 1,
    categoria_nombre: 'Principales',
    subcategoria_id: null,
    subcategoria_nombre: null,
    precio: 125_50, // 125.50 pesos
    imagen_url: null,
    destacado: true,
    popular: false,
    estado: 'activo',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    nombre: 'Empanadas x6',
    descripcion: null,
    categoria_id: 1,
    categoria_nombre: 'Entradas',
    subcategoria_id: null,
    subcategoria_nombre: null,
    precio: 80_00, // 80.00 pesos
    imagen_url: null,
    destacado: false,
    popular: true,
    estado: 'activo',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockCategories: Category[] = [];
const mockSubcategories: Subcategory[] = [];

const mockCreate = vi.fn();
const mockUpdate = vi.fn();
const mockRemove = vi.fn();
const mockRefresh = vi.fn();

vi.mock('@/hooks/useCrud', () => ({
  useCrud: () => ({
    items: mockProducts,
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
  useBranch: () => ({
    selectedBranchId: 1,
    branches: [{ id: 1, nombre: 'Sucursal Test' }],
    selectedBranch: { id: 1, nombre: 'Sucursal Test' },
    isLoading: false,
    selectBranch: () => {},
    fetchBranches: () => Promise.resolve(),
  }),
}));

vi.mock('@/hooks/useConfirm', () => ({
  useConfirm: () => vi.fn().mockResolvedValue(true),
}));

vi.mock('@/services/product.service', () => ({
  productService: { list: vi.fn(), create: vi.fn(), update: vi.fn(), remove: vi.fn() },
}));

vi.mock('@/services/category.service', () => ({
  categoryService: {
    // Inline — vi.mock factories are hoisted above const declarations
    list: vi.fn().mockResolvedValue({ data: [], meta: { page: 1, limit: 100, total: 0 } }),
  },
}));

vi.mock('@/services/subcategory.service', () => ({
  subcategoryService: {
    list: vi.fn().mockResolvedValue({ data: [], meta: { page: 1, limit: 200, total: 0 } }),
  },
}));

vi.mock('@/lib/logger', () => ({
  logger: { error: vi.fn(), warn: vi.fn(), debug: vi.fn(), info: vi.fn() },
}));

vi.mock('@/utils/helpContent', () => ({
  helpContent: { products: { title: 'Help', sections: [] } },
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
      <ProductsPage />
    </MemoryRouter>,
  );
}

describe('S18 — ProductsPage renders product list', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays product names in the table', () => {
    renderPage();
    expect(screen.getByText('Milanesa napolitana')).toBeInTheDocument();
    expect(screen.getByText('Empanadas x6')).toBeInTheDocument();
  });

  it('renders Crear producto button', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /crear producto/i })).toBeInTheDocument();
  });
});

describe('S19 — ProductsPage displays prices converted from cents to pesos', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows 125,50 for a product with precio=12550', () => {
    renderPage();
    // formatCurrency uses locale formatting — Intl.NumberFormat produces "125,50" in es-AR
    expect(screen.getByText(/125[.,]50/)).toBeInTheDocument();
  });

  it('shows 80,00 for a product with precio=8000', () => {
    renderPage();
    expect(screen.getByText(/80[.,]00/)).toBeInTheDocument();
  });
});

describe('S20 — ProductsPage batch price button appears after selecting products', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not show batch price button when no products are selected', () => {
    renderPage();
    // Button only appears when selectedIds.size > 0
    expect(screen.queryByRole('button', { name: /actualizar precios/i })).not.toBeInTheDocument();
  });

  it('shows batch price button after clicking select-all checkbox', async () => {
    const user = userEvent.setup();
    renderPage();

    // The "Seleccionar todos" label is next to the first checkbox (select-all)
    const selectAllLabel = screen.getByText(/seleccionar todos/i);
    // The checkbox is a sibling of the label text — find it via closest container
    const selectAllContainer = selectAllLabel.closest('div');
    const selectAllCheckbox = selectAllContainer?.querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(selectAllCheckbox).toBeTruthy();
    await user.click(selectAllCheckbox);

    expect(screen.getByRole('button', { name: /actualizar precios/i })).toBeInTheDocument();
  });
});
