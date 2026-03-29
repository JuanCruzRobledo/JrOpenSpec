import { type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface ChipProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'onClick'> {
  /** Whether the chip is currently selected/active */
  isSelected?: boolean;
  /** Optional icon rendered before the label */
  icon?: ReactNode;
  /** Callback invoked when the chip is toggled */
  onToggle?: () => void;
  children: ReactNode;
}

/**
 * Togglable chip — used for filter options and category tabs.
 * Minimum 44px height enforced for touch accessibility.
 */
export function Chip({
  isSelected = false,
  icon,
  onToggle,
  className,
  children,
  disabled,
  ...rest
}: ChipProps) {
  return (
    <button
      {...rest}
      type="button"
      role="checkbox"
      aria-checked={isSelected}
      disabled={disabled}
      onClick={onToggle}
      className={cn(
        // Base layout
        'inline-flex items-center gap-1.5 rounded-full px-3 font-medium text-sm',
        'min-h-[44px] whitespace-nowrap',
        // Transition
        'transition-colors duration-150',
        // Focus ring
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
        // Selected state
        isSelected
          ? 'bg-accent text-white border border-accent'
          : 'bg-surface-muted text-surface-text border border-surface-border hover:border-accent hover:text-accent',
        // Disabled
        disabled && 'cursor-not-allowed opacity-50',
        className
      )}
    >
      {icon && <span aria-hidden="true" className="flex-shrink-0">{icon}</span>}
      {children}
    </button>
  );
}
