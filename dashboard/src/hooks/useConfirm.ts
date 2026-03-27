import { useUIStore } from '@/stores/ui.store';
import type { ConfirmDialogConfig } from '@/types/ui';

/**
 * Convenience hook for showing the confirmation dialog.
 * Returns a function that opens the dialog and resolves to boolean.
 */
export function useConfirm() {
  const showConfirm = useUIStore((s) => s.showConfirm);

  const confirm = (config: ConfirmDialogConfig): Promise<boolean> => {
    return showConfirm(config);
  };

  return confirm;
}
