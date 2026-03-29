import { useEffect } from 'react';

/** CSS selector for all naturally focusable elements */
const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ');

interface UseFocusTrapOptions {
  /** Called when the Escape key is pressed inside the trap */
  onEscape?: () => void;
}

/**
 * Traps keyboard focus within `ref` when `isActive` is true.
 *
 * - Tab: cycles forward through focusable elements within the container
 * - Shift+Tab: cycles backward
 * - Escape: calls `onEscape` if provided
 *
 * Automatically focuses the first focusable element on activation.
 * Restores focus to the previously focused element on deactivation.
 *
 * @param ref      - Ref to the container element that should trap focus
 * @param isActive - Whether the trap is currently active
 * @param options  - Optional callbacks
 */
export function useFocusTrap(
  ref: React.RefObject<HTMLElement | null>,
  isActive: boolean,
  options?: UseFocusTrapOptions
): void {
  const { onEscape } = options ?? {};

  useEffect(() => {
    if (!isActive || !ref.current) return;

    const container = ref.current;
    // Remember what had focus before we trapped it
    const previouslyFocused = document.activeElement as HTMLElement | null;

    // Focus the first focusable element inside the container
    const focusable = Array.from(
      container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
    );

    if (focusable[0]) {
      focusable[0].focus();
    }

    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === 'Escape') {
        onEscape?.();
        return;
      }

      if (event.key !== 'Tab') return;

      // Re-query on each keydown in case DOM changed (e.g. dynamic content)
      const currentFocusable = Array.from(
        container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
      );
      const currentFirst = currentFocusable[0];
      const currentLast = currentFocusable[currentFocusable.length - 1];

      if (!currentFirst) return;

      if (event.shiftKey) {
        // Shift+Tab: wrap from first → last
        if (document.activeElement === currentFirst) {
          event.preventDefault();
          currentLast?.focus();
        }
      } else {
        // Tab: wrap from last → first
        if (document.activeElement === currentLast) {
          event.preventDefault();
          currentFirst?.focus();
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      // Restore focus to previously focused element on deactivation
      previouslyFocused?.focus();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive, ref, onEscape]);
  // Note: focusable elements are queried inside the effect. Deps intentionally
  // limited to isActive/ref/onEscape — re-runs when trap activates/deactivates.
}
