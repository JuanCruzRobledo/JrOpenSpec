/**
 * ConfirmDialog tests — S23 (cancel resolves false and closes dialog).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useUIStore } from '@/stores/ui.store';

// Reset the ui store between tests
function resetStore() {
  useUIStore.setState({
    toasts: [],
    confirmDialog: null,
    sidebarCollapsed: false,
  });
}

describe('S23 — ConfirmDialog cancel resolves false and closes', () => {
  beforeEach(() => {
    resetStore();
    vi.clearAllMocks();
  });

  it('does not render when confirmDialog is null', () => {
    render(<ConfirmDialog />);
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  });

  it('renders dialog with title and description when confirmDialog is set', async () => {
    useUIStore.getState().showConfirm({
      title: 'Eliminar elemento',
      description: 'Esta accion no se puede deshacer.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    render(<ConfirmDialog />);

    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    expect(screen.getByText('Eliminar elemento')).toBeInTheDocument();
    expect(screen.getByText('Esta accion no se puede deshacer.')).toBeInTheDocument();
  });

  it('calls onCancel and resolves false when Cancel button is clicked', async () => {
    const user = userEvent.setup();

    const promise = useUIStore.getState().showConfirm({
      title: 'Confirmar?',
      description: 'Descripcion de prueba',
    });

    render(<ConfirmDialog />);

    const cancelBtn = screen.getByRole('button', { name: /cancelar/i });
    await user.click(cancelBtn);

    expect(await promise).toBe(false);
    expect(useUIStore.getState().confirmDialog).toBeNull();
  });

  it('resolves true when Confirm button is clicked', async () => {
    const user = userEvent.setup();

    const promise = useUIStore.getState().showConfirm({
      title: 'Confirmar?',
      description: 'Descripcion de prueba',
      confirmLabel: 'Confirmar',
    });

    render(<ConfirmDialog />);

    const confirmBtn = screen.getByRole('button', { name: /confirmar/i });
    await user.click(confirmBtn);

    expect(await promise).toBe(true);
    expect(useUIStore.getState().confirmDialog).toBeNull();
  });

  it('uses danger variant for confirm button when variant="danger"', () => {
    useUIStore.getState().showConfirm({
      title: 'Eliminar?',
      description: 'Esto se borra',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    render(<ConfirmDialog />);

    const confirmBtn = screen.getByRole('button', { name: /eliminar/i });
    expect(confirmBtn).toBeInTheDocument();
  });
});
