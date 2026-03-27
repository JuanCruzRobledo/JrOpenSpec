import { createPortal } from 'react-dom';
import { useShallow } from 'zustand/react/shallow';
import { useUIStore } from '@/stores/ui.store';
import { Toast } from '@/components/ui/Toast';

interface Props {}

export function ToastContainer(_props: Props) {
  const toasts = useUIStore(useShallow((s) => s.toasts));
  const removeToast = useUIStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return createPortal(
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-96">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onClose={removeToast} />
      ))}
    </div>,
    document.body,
  );
}
