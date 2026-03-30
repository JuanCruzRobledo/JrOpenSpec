import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import LandingPage from '../LandingPage';
import { useSessionStore } from '@/stores/session.store';
import { useUiStore } from '@/stores/ui.store';
import { LAST_TABLE_CONTEXT_KEY } from '@/lib/session-context';

const joinSessionMock = vi.fn();

vi.mock('@/services/session.service', () => ({
  joinSession: (...args: unknown[]) => joinSessionMock(...args),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, vars?: Record<string, string>) => {
      const translations: Record<string, string> = {
        'landing.anonymous': 'Anonimo',
        'landing.nameLabel': 'Tu nombre',
        'landing.namePlaceholder': 'Opcional',
        'landing.joinButton': 'Entrar',
        'landing.joining': 'Entrando...',
        'landing.title': `Bienvenido a ${vars?.branchName ?? ''}`.trim(),
        'landing.subtitle': `Mesa ${vars?.tableName ?? ''}`.trim(),
        'errors.invalidQR': 'QR invalido',
        'errors.joinFailed': 'No se pudo ingresar',
        'errors.branchNotFound': 'Sucursal o mesa no encontrada',
        'errors.tableInactive': 'Mesa inactiva',
      };

      return translations[key] ?? key;
    },
  }),
}));

vi.mock('@/i18n', () => ({
  default: {
    language: 'es',
    t: (key: string) => (key === 'app.name' ? 'Menu' : key),
  },
}));

function renderLanding(initialPath = '/buen-sabor/centro/mesa/12') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/:tenant/:branch/mesa/:table" element={<LandingPage />} />
        <Route path="/:tenant/:branch" element={<div>menu route</div>} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  localStorage.clear();
  joinSessionMock.mockReset();
  useSessionStore.getState().clear();
  useUiStore.setState({
    filterDrawerOpen: false,
    installBannerVisible: false,
    toasts: [],
  });
});

describe('LandingPage', () => {
  it('joins the session and navigates to the menu route', async () => {
    joinSessionMock.mockResolvedValue({
      token: 'token-123',
      sessionId: '2eeef7d8-20ae-4676-ba44-39758aee8be0',
      expiresAt: '2026-03-30T12:00:00Z',
      branch: { id: 1, name: 'Buen Sabor Centro', slug: 'centro' },
      table: { identifier: '12', displayName: 'Mesa 12' },
    });

    renderLanding();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText('Tu nombre'), 'Juani');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    await screen.findByText('menu route');

    expect(joinSessionMock).toHaveBeenCalledWith(
      expect.objectContaining({
        branchSlug: 'centro',
        tableIdentifier: '12',
        displayName: 'Juani',
        locale: 'es',
      })
    );

    expect(useSessionStore.getState().token).toBe('token-123');
    expect(useSessionStore.getState().displayName).toBe('Juani');
    expect(localStorage.getItem(LAST_TABLE_CONTEXT_KEY)).toContain('"table":"12"');
  });

  it('falls back to the localized anonymous name when the field is empty', async () => {
    joinSessionMock.mockResolvedValue({
      token: 'token-123',
      sessionId: '2eeef7d8-20ae-4676-ba44-39758aee8be0',
      expiresAt: '2026-03-30T12:00:00Z',
      branch: { id: 1, name: 'Buen Sabor Centro', slug: 'centro' },
      table: { identifier: '12', displayName: 'Mesa 12' },
    });

    renderLanding();
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    await waitFor(() => {
      expect(joinSessionMock).toHaveBeenCalledWith(
        expect.objectContaining({ displayName: 'Anonimo' })
      );
    });
  });

  it('shows the translated 404 error toast when join fails', async () => {
    joinSessionMock.mockRejectedValue({ response: { status: 404 } });

    renderLanding();
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    await waitFor(() => {
      expect(useUiStore.getState().toasts.at(-1)?.message).toBe(
        'Sucursal o mesa no encontrada'
      );
    });
  });
});
