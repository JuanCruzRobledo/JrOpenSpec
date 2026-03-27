import { cn } from '@/lib/cn';
import type { Toast as ToastType } from '@/types/ui';

interface Props {
  toast: ToastType;
  onClose: (id: string) => void;
}

const variantStyles: Record<ToastType['type'], string> = {
  success: 'border-success/30 bg-success/10 text-success',
  error: 'border-error/30 bg-error/10 text-error',
  warning: 'border-warning/30 bg-warning/10 text-warning',
  info: 'border-info/30 bg-info/10 text-info',
};

const iconMap: Record<ToastType['type'], string> = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
};

export function Toast({ toast, onClose }: Props) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg',
        'animate-in slide-in-from-right',
        variantStyles[toast.type],
      )}
      role="alert"
    >
      <span className="text-lg leading-none">{iconMap[toast.type]}</span>
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={() => onClose(toast.id)}
        className="shrink-0 opacity-60 hover:opacity-100 transition-opacity"
        aria-label="Cerrar"
      >
        ✕
      </button>
    </div>
  );
}
