import {
  useEffect,
  useRef,
  useCallback,
  type ReactNode,
  useId,
} from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import { useFocusTrap } from '@/hooks/useFocusTrap';

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  /** Accessible title for the drawer */
  title: string;
  children: ReactNode;
  className?: string;
}

/**
 * Slide-in drawer component.
 * - Desktop (≥768px): slides in from the right side
 * - Mobile (<768px): bottom sheet behavior
 *
 * Interactions:
 * - Backdrop click → close
 * - Escape key → close
 * - Focus trap active while open
 * - Scrollable content area
 *
 * Rendered in a portal to document.body.
 */
export function Drawer({ isOpen, onClose, title, children, className }: DrawerProps) {
  const { t } = useTranslation('common');
  const titleId = useId();
  const containerRef = useRef<HTMLDivElement>(null);

  useFocusTrap(containerRef, isOpen, { onEscape: onClose });

  // Prevent body scroll while open
  useEffect(() => {
    if (!isOpen) return;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen]);

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose]
  );

  if (!isOpen) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-end justify-end md:items-stretch"
      aria-hidden={!isOpen}
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={cn(
          // Base
          'relative z-10 bg-surface-card shadow-xl flex flex-col',
          // Mobile: bottom sheet, max 90% viewport height
          'w-full rounded-t-2xl max-h-[90dvh]',
          // Desktop: right-side drawer, full height
          'md:rounded-none md:rounded-l-2xl md:max-h-full md:h-full md:w-96',
          // Slide animation
          'animate-slide-in-right motion-reduce:animate-none',
          className
        )}
      >
        {/* Drag handle (mobile only) */}
        <div
          className="mx-auto mt-3 h-1 w-10 rounded-full bg-surface-border md:hidden flex-shrink-0"
          aria-hidden="true"
        />

        {/* Header */}
        <div className="flex items-center justify-between px-4 pt-4 pb-3 border-b border-surface-border flex-shrink-0">
          <h2
            id={titleId}
            className="text-lg font-semibold text-surface-text"
          >
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('app.close')}
            className={cn(
              'flex h-11 w-11 items-center justify-center rounded-full',
              'text-surface-text/60 hover:text-surface-text hover:bg-surface-muted',
              'transition-colors duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent'
            )}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              className="h-5 w-5"
              aria-hidden="true"
            >
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
}
