/**
 * BranchGuard tests — S7.
 * Verifies that the guard blocks navigation when no branch is selected
 * and renders the child outlet when a branch is selected.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route, Outlet } from 'react-router-dom';
import { BranchGuard } from '@/router/BranchGuard';
import { useBranchStore } from '@/stores/branch.store';

// ---------------------------------------------------------------------------
// Mock the branch store
// ---------------------------------------------------------------------------
vi.mock('@/stores/branch.store', () => ({
  useBranchStore: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Helper: wrap BranchGuard inside a MemoryRouter since it uses <Outlet />
// ---------------------------------------------------------------------------
function renderGuard(selectedBranchId: number | null) {
  vi.mocked(useBranchStore).mockImplementation((selector: (s: { selectedBranchId: number | null }) => unknown) =>
    selector({ selectedBranchId }),
  );

  return render(
    <MemoryRouter initialEntries={['/protected']}>
      <Routes>
        <Route element={<BranchGuard />}>
          <Route
            path="/protected"
            element={<div data-testid="protected-content">Protected content</div>}
          />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('S7 — BranchGuard blocks access without a selected branch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows branch selection prompt when selectedBranchId is null', () => {
    renderGuard(null);

    expect(screen.getByText(/selecciona una sucursal/i)).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('renders child route content when a branch is selected', () => {
    renderGuard(42);

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByText(/selecciona una sucursal/i)).not.toBeInTheDocument();
  });
});
