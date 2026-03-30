import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Outlet, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';
import { SessionGuard } from '../SessionGuard';
import { useSessionStore } from '@/stores/session.store';
import { LAST_TABLE_CONTEXT_KEY } from '@/lib/session-context';

function ProtectedLayout() {
  return (
    <div>
      <span>protected route</span>
      <Outlet />
    </div>
  );
}

function renderGuard(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/:tenant/:branch" element={<SessionGuard />}>
          <Route element={<ProtectedLayout />}>
            <Route index element={<div>menu page</div>} />
          </Route>
        </Route>
        <Route path="/:tenant/:branch/product/:productId" element={<SessionGuard />}>
          <Route element={<ProtectedLayout />}>
            <Route index element={<div>product page</div>} />
          </Route>
        </Route>
        <Route path="/:tenant/:branch/mesa/:table" element={<div>landing page</div>} />
        <Route path="/" element={<div>root page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  localStorage.clear();
  useSessionStore.getState().clear();
});

describe('SessionGuard', () => {
  it('redirects menu startup routes to the remembered landing path when there is no session', async () => {
    localStorage.setItem(
      LAST_TABLE_CONTEXT_KEY,
      JSON.stringify({ tenant: 'buen-sabor', branch: 'centro', table: '12' })
    );

    renderGuard('/buen-sabor/centro');

    await screen.findByText('landing page');
  });

  it('renders the protected outlet when the session exists', async () => {
    useSessionStore.setState({
      token: 'token-123',
      sessionId: 'session-123',
      displayName: 'Juani',
      avatarColor: '#F97316',
      branchSlug: 'centro',
      branchName: 'Buen Sabor Centro',
      tableIdentifier: '12',
      tableName: 'Mesa 12',
      joinedAt: '2026-03-30T12:00:00Z',
      lastActivity: Date.now(),
    });

    renderGuard('/buen-sabor/centro');

    await screen.findByText('menu page');
    expect(screen.queryByText('landing page')).not.toBeInTheDocument();
  });

  it('clears expired sessions and redirects product routes to the remembered landing path', async () => {
    localStorage.setItem(
      LAST_TABLE_CONTEXT_KEY,
      JSON.stringify({ tenant: 'buen-sabor', branch: 'centro', table: '12' })
    );

    useSessionStore.setState({
      token: 'token-123',
      sessionId: 'session-123',
      displayName: 'Juani',
      avatarColor: '#F97316',
      branchSlug: 'centro',
      branchName: 'Buen Sabor Centro',
      tableIdentifier: null,
      tableName: 'Mesa 12',
      joinedAt: '2026-03-30T12:00:00Z',
      lastActivity: Date.now() - 28_800_001,
    });

    renderGuard('/buen-sabor/centro/product/99');

    await screen.findByText('landing page');
    await waitFor(() => {
      expect(useSessionStore.getState().token).toBeNull();
    });
  });
});
