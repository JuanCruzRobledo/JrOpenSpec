import { type TextareaHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/cn';

interface Props extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string | null;
  isRequired?: boolean;
  showCount?: boolean;
  maxLength?: number;
}

export const Textarea = forwardRef<HTMLTextAreaElement, Props>(
  ({ label, error, isRequired, showCount, maxLength, className, id, value, ...rest }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
    const currentLength = typeof value === 'string' ? value.length : 0;
    const isOverLimit = maxLength ? currentLength > maxLength : false;

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
        <textarea
          ref={ref}
          id={inputId}
          value={value}
          maxLength={maxLength}
          className={cn(
            'min-h-[80px] rounded-lg border bg-bg-surface px-3 py-2 text-sm text-text-primary',
            'placeholder:text-text-tertiary resize-y',
            'transition-colors duration-150',
            'focus:outline-none focus:border-border-focus focus:ring-1 focus:ring-border-focus',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error || isOverLimit
              ? 'border-error'
              : 'border-border-default',
            className,
          )}
          aria-invalid={error ? 'true' : undefined}
          {...rest}
        />
        <div className="flex justify-between">
          {error ? (
            <span className="text-sm text-error" role="alert">
              {error}
            </span>
          ) : (
            <span />
          )}
          {showCount && maxLength ? (
            <span
              className={cn(
                'text-xs',
                isOverLimit ? 'text-error' : 'text-text-tertiary',
              )}
            >
              {currentLength}/{maxLength}
            </span>
          ) : null}
        </div>
      </div>
    );
  },
);

Textarea.displayName = 'Textarea';
