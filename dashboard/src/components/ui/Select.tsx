import { type SelectHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/cn';

interface SelectOption {
  value: string | number;
  label: string;
}

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string | null;
  isRequired?: boolean;
  options: SelectOption[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, Props>(
  ({ label, error, isRequired, options, placeholder, className, id, ...rest }, ref) => {
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
        <select
          ref={ref}
          id={inputId}
          className={cn(
            'h-10 rounded-lg border bg-bg-surface px-3 text-sm text-text-primary',
            'transition-colors duration-150 appearance-none',
            'focus:outline-none focus:border-border-focus focus:ring-1 focus:ring-border-focus',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error
              ? 'border-error'
              : 'border-border-default',
            className,
          )}
          aria-invalid={error ? 'true' : undefined}
          {...rest}
        >
          {placeholder ? (
            <option value="" className="text-text-tertiary">
              {placeholder}
            </option>
          ) : null}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {error ? (
          <span className="text-sm text-error" role="alert">
            {error}
          </span>
        ) : null}
      </div>
    );
  },
);

Select.displayName = 'Select';
