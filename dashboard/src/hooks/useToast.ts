import { useUIStore } from '@/stores/ui.store';
import type { ToastType } from '@/types/ui';

/**
 * Convenience hook for adding toasts.
 */
export function useToast() {
  const addToast = useUIStore((s) => s.addToast);

  return {
    success: (message: string) => addToast({ type: 'success' as ToastType, message }),
    error: (message: string) => addToast({ type: 'error' as ToastType, message }),
    warning: (message: string) => addToast({ type: 'warning' as ToastType, message }),
    info: (message: string) => addToast({ type: 'info' as ToastType, message }),
    add: addToast,
  };
}
