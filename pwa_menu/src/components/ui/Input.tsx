import { type InputHTMLAttributes, type ReactNode, useId } from 'react';
import { cn } from '@/lib/cn';
import { useTranslation } from 'react-i18next';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  label?: string;
  /** Validation error message — shown below the input in red */
  errorMessage?: string;
  /** Renders an × button to clear the input value */
  showClearButton?: boolean;
  /** Called when the clear button is clicked */
  onClear?: () => void;
  /** Accessible label for the input (required when `label` prop is not provided) */
  'aria-label'?: string;
}

/**
 * Text input with optional label, error message, and clear button.
 * Enforces orange focus ring on all states.
 */
export function Input({
  label,
  errorMessage,
  showClearButton = false,
  onClear,
  className,
  'aria-label': ariaLabel,
  ...rest
}: InputProps) {
  const { t } = useTranslation('common');
  const inputId = useId();
  const errorId = useId();

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-surface-text"
        >
          {label}
        </label>
      )}

      <div className="relative">
        <input
          {...rest}
          id={inputId}
          aria-label={!label ? ariaLabel : undefined}
          aria-describedby={errorMessage ? errorId : undefined}
          aria-invalid={!!errorMessage}
          className={cn(
            'w-full rounded-lg border bg-surface-muted px-3 py-2.5 text-base text-surface-text',
            'placeholder:text-surface-text/40',
            'border-surface-border',
            'transition-colors duration-150',
            'focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
            'focus-visible:ring-2 focus-visible:ring-accent',
            // Leave room for clear button when shown
            showClearButton && rest.value ? 'pr-10' : '',
            errorMessage && 'border-red-500 focus:ring-red-500',
            // Enforce min height for touch target
            'min-h-[44px]',
            className
          )}
        />

        {showClearButton && rest.value && (
          <button
            type="button"
            onClick={onClear}
            aria-label={t('app.close')}
            className={cn(
              'absolute right-2 top-1/2 -translate-y-1/2',
              'flex h-8 w-8 items-center justify-center rounded-full',
              'text-surface-text/60 hover:text-surface-text hover:bg-surface-border',
              'transition-colors duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent'
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
        )}
      </div>

      {errorMessage && (
        <p id={errorId} role="alert" className="text-sm text-red-500">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
