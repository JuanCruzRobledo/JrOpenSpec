import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import type { Toast as ToastType, ToastVariant } from '@/stores/ui.store';
import {
  useUiStore,
  selectRemoveToastAction,
} from '@/stores/ui.store';

interface ToastProps {
  toast: ToastType;
}

const variantStyles: Record<ToastVariant, { container: string; icon: string; label: string }> = {
  success: {
    container: 'bg-green-900/90 border-green-700 text-green-100',
    icon: '✓',
    label: 'success',
  },
  error: {
    container: 'bg-red-900/90 border-red-700 text-red-100',
    icon: '✕',
    label: 'error',
  },
  warning: {
    container: 'bg-amber-900/90 border-amber-700 text-amber-100',
    icon: '⚠',
    label: 'warning',
  },
  info: {
    container: 'bg-surface-card/95 border-surface-border text-surface-text',
    icon: 'ℹ',
    label: 'info',
  },
};

/**
 * Individual toast notification.
 * Auto-removal is managed by ui.store. This component only handles display + manual dismiss.
 * Slide-in animation via CSS keyframes defined in index.css.
 */
export function Toast({ toast }: ToastProps) {
  const { t } = useTranslation('common');
  const removeToast = useUiStore(selectRemoveToastAction);

  const styles = variantStyles[toast.variant];

  return (
    <div
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      className={cn(
        'flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg',
        'animate-slide-in',
        // Respect reduced motion
        'motion-reduce:animate-none',
        styles.container
      )}
    >
      <span
        aria-label={styles.label}
        className="mt-0.5 flex-shrink-0 text-sm font-bold"
      >
        {styles.icon}
      </span>

      <p className="flex-1 text-sm">{toast.message}</p>

      <button
        type="button"
        onClick={() => removeToast(toast.id)}
        aria-label={t('app.close')}
        className={cn(
          'flex-shrink-0 rounded p-0.5',
          'transition-colors duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
          'opacity-70 hover:opacity-100',
          // Ensure min touch target
          'min-h-[44px] min-w-[44px] flex items-center justify-center -m-2'
        )}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-4 w-4"
          aria-hidden="true"
        >
          <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
        </svg>
      </button>
    </div>
  );
}
