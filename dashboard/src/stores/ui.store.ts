/**
 * UI store — sidebar state, toasts, confirmation dialogs.
 * Only sidebarCollapsed is persisted to localStorage.
 *
 * NEVER destructure: use individual selectors always.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { MAX_TOASTS, TOAST_DURATION_MS } from '@/config/constants';
import type { Toast, ConfirmDialogConfig, ConfirmDialogState } from '@/types/ui';

interface UIState {
  sidebarCollapsed: boolean;
  toasts: Toast[];
  confirmDialog: ConfirmDialogState | null;

  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  showConfirm: (config: ConfirmDialogConfig) => Promise<boolean>;
  hideConfirm: () => void;
}

let toastIdCounter = 0;

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      sidebarCollapsed: false,
      toasts: [],
      confirmDialog: null,

      toggleSidebar: () =>
        set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

      setSidebarCollapsed: (collapsed: boolean) =>
        set({ sidebarCollapsed: collapsed }),

      addToast: (toast) => {
        const id = String(++toastIdCounter);
        const newToast: Toast = { ...toast, id };
        const duration = toast.duration ?? TOAST_DURATION_MS;

        set((s) => ({
          toasts: [...s.toasts.slice(-(MAX_TOASTS - 1)), newToast],
        }));

        setTimeout(() => {
          get().removeToast(id);
        }, duration);
      },

      removeToast: (id: string) =>
        set((s) => ({
          toasts: s.toasts.filter((t) => t.id !== id),
        })),

      showConfirm: (config: ConfirmDialogConfig) =>
        new Promise<boolean>((resolve) => {
          set({
            confirmDialog: {
              ...config,
              onConfirm: () => {
                set({ confirmDialog: null });
                resolve(true);
              },
              onCancel: () => {
                set({ confirmDialog: null });
                resolve(false);
              },
            },
          });
        }),

      hideConfirm: () => set({ confirmDialog: null }),
    }),
    {
      name: 'buen-sabor-ui',
      partialize: (s) => ({ sidebarCollapsed: s.sidebarCollapsed }),
    },
  ),
);
