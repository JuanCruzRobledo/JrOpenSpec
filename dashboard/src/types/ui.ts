// UI-related types for toasts, confirmation dialogs, etc.

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

export interface ConfirmDialogConfig {
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'default';
}

export interface ConfirmDialogState extends ConfirmDialogConfig {
  onConfirm: () => void;
  onCancel: () => void;
}
