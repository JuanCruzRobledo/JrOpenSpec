import { createPortal } from 'react-dom';
import { useShallow } from 'zustand/react/shallow';
import { useUiStore } from '@/stores/ui.store';
import { Toast } from './Toast';

/**
 * Renders the toast stack in a portal to document.body.
 * Positioned top-right on desktop, top-center on mobile.
 * Maximum 5 toasts enforced by ui.store.
 */
export function ToastContainer() {
  // useShallow prevents re-renders when toast contents change but array reference is stable
  const toasts = useUiStore(useShallow((s) => s.toasts));

  if (toasts.length === 0) return null;

  return createPortal(
    <div
      aria-label="Notifications"
      className="pointer-events-none fixed inset-x-0 top-4 z-[9999] flex flex-col items-center gap-2 px-4 sm:items-end sm:right-4 sm:left-auto sm:max-w-sm"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto w-full">
          <Toast toast={toast} />
        </div>
      ))}
    </div>,
    document.body
  );
}
