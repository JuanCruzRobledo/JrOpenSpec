import { type InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/cn';

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string | null;
  isRequired?: boolean;
}

export const Input = forwardRef<HTMLInputElement, Props>(
  ({ label, error, isRequired, className, id, ...rest }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1.5">
        {label ? (
          <label
            htmlFor={inputId}
            className="text-sm text-text-secondary"
          >
            {label}
            {isRequired ? (
              <span className="text-error ml-0.5">*</span>
            ) : null}
          </label>
        ) : null}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'h-10 rounded-lg border bg-bg-surface px-3 text-sm text-text-primary',
            'placeholder:text-text-tertiary',
            'transition-colors duration-150',
            'focus:outline-none focus:border-border-focus focus:ring-1 focus:ring-border-focus',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error
              ? 'border-error'
              : 'border-border-default',
            className,
          )}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...rest}
        />
        {error ? (
          <span
            id={`${inputId}-error`}
            className="text-sm text-error"
            role="alert"
          >
            {error}
          </span>
        ) : null}
      </div>
    );
  },
);

Input.displayName = 'Input';
