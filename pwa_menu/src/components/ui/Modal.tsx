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

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Accessible title — shown in the header and used for aria-labelledby */
  title: string;
  children: ReactNode;
  className?: string;
}

/**
 * Bottom-sheet modal on mobile, centered dialog on desktop (≥768px).
 *
 * Interactions:
 * - Swipe down >100px → dismiss (touch)
 * - Backdrop click → dismiss
 * - Escape key → dismiss
 * - Focus trap active while open
 *
 * Animations:
 * - Mobile: slide up (transform translateY)
 * - Respects prefers-reduced-motion
 *
 * Accessibility:
 * - role="dialog", aria-modal="true", aria-labelledby
 * - Rendered in a portal to document.body
 */
export function Modal({ isOpen, onClose, title, children, className }: ModalProps) {
  const { t } = useTranslation('common');
  const titleId = useId();
  const containerRef = useRef<HTMLDivElement>(null);

  // Touch state for swipe-to-dismiss
  const touchStartYRef = useRef<number>(0);

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

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartYRef.current = e.touches[0]?.clientY ?? 0;
  }, []);

  const handleTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      const endY = e.changedTouches[0]?.clientY ?? 0;
      const delta = endY - touchStartYRef.current;
      // Swipe down > 100px dismisses
      if (delta > 100) {
        onClose();
      }
    },
    [onClose]
  );

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
      className="fixed inset-0 z-50 flex items-end justify-center md:items-center"
      aria-hidden={!isOpen}
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm motion-reduce:transition-none"
        aria-hidden="true"
      />

      {/* Dialog panel */}
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        className={cn(
          // Base
          'relative z-10 w-full bg-surface-card shadow-xl',
          // Mobile: bottom sheet
          'rounded-t-2xl max-h-[92dvh] overflow-y-auto',
          // Desktop: centered card
          'md:rounded-2xl md:max-w-lg md:max-h-[85dvh]',
          // Slide-up animation (mobile)
          'animate-slide-up motion-reduce:animate-none',
          className
        )}
      >
        {/* Drag handle indicator (mobile) */}
        <div
          className="mx-auto mt-3 h-1 w-10 rounded-full bg-surface-border md:hidden"
          aria-hidden="true"
        />

        {/* Header */}
        <div className="flex items-center justify-between px-4 pt-4 pb-2">
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

        {/* Content */}
        <div className="px-4 pb-8">{children}</div>
      </div>
    </div>,
    document.body
  );
}
