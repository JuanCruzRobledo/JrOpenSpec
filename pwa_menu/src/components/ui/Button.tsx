import { type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

export type ButtonVariant = 'primary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Shows a loading spinner and disables interaction */
  isLoading?: boolean;
  children: ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-accent text-white hover:bg-accent-hover active:scale-95 disabled:bg-accent/50',
  ghost:
    'bg-transparent text-surface-text border border-surface-border hover:bg-surface-muted active:scale-95 disabled:opacity-50',
  danger:
    'bg-red-600 text-white hover:bg-red-700 active:scale-95 disabled:bg-red-600/50',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-sm min-w-[44px]',
  md: 'h-11 px-4 text-base min-w-[44px]',
  lg: 'h-14 px-6 text-lg min-w-[44px]',
};

/**
 * Base button component.
 * All variants enforce minimum 44×44px touch target.
 */
export function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled ?? isLoading}
      className={cn(
        // Base
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium',
        'transition-colors duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
        // Variant + size
        variantClasses[variant],
        sizeClasses[size],
        // Disabled cursor
        (disabled ?? isLoading) && 'cursor-not-allowed',
        className
      )}
    >
      {isLoading && (
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
          aria-hidden="true"
        />
      )}
      {children}
    </button>
  );
}
