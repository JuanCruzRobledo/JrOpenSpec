import { createPortal } from 'react-dom';
import { useUIStore } from '@/stores/ui.store';
import { Button } from '@/components/ui/Button';

interface Props {}

export function ConfirmDialog(_props: Props) {
  const confirmDialog = useUIStore((s) => s.confirmDialog);

  if (!confirmDialog) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/50"
      role="alertdialog"
      aria-modal="true"
      aria-label={confirmDialog.title}
    >
      <div className="w-full max-w-md rounded-xl bg-bg-surface border border-border-default shadow-2xl p-6">
        <h3 className="text-lg font-semibold text-text-primary">
          {confirmDialog.title}
        </h3>
        <p className="mt-2 text-sm text-text-secondary">
          {confirmDialog.description}
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={confirmDialog.onCancel}>
            {confirmDialog.cancelLabel ?? 'Cancelar'}
          </Button>
          <Button
            variant={confirmDialog.variant === 'danger' ? 'danger' : 'primary'}
            onClick={confirmDialog.onConfirm}
          >
            {confirmDialog.confirmLabel ?? 'Confirmar'}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
