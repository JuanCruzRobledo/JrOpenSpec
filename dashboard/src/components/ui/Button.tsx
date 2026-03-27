import { type ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';
import { Spinner } from '@/components/ui/Spinner';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-accent text-white hover:bg-accent-hover focus:ring-accent/40',
  secondary:
    'bg-transparent border border-border-default text-text-secondary hover:bg-bg-elevated hover:text-text-primary',
  danger:
    'bg-error text-white hover:bg-red-600 focus:ring-error/40',
  ghost:
    'bg-transparent text-text-secondary hover:bg-bg-elevated hover:text-text-primary',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
};

export function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  className,
  children,
  ...rest
}: Props) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium',
        'transition-colors duration-150 focus:outline-none focus:ring-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
      disabled={disabled || isLoading}
      {...rest}
    >
      {isLoading ? <Spinner size="sm" /> : null}
      {children}
    </button>
  );
}
