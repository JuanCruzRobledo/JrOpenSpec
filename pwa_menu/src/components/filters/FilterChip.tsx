import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface FilterChipProps {
  label: string;
  isSelected: boolean;
  onToggle: () => void;
  icon?: ReactNode;
  ariaLabel?: string;
}

/**
 * Togglable filter chip.
 * Uses role="checkbox" / aria-checked for filter semantics.
 * Minimum 44px height for touch accessibility.
 */
export function FilterChip({ label, isSelected, onToggle, icon, ariaLabel }: FilterChipProps) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={isSelected}
      aria-label={ariaLabel ?? label}
      onClick={onToggle}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-3 font-medium text-sm',
        'min-h-[44px] whitespace-nowrap',
        'transition-colors duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
        isSelected
          ? 'bg-accent text-white border border-accent'
          : 'bg-surface-muted text-text-secondary border border-surface-border hover:border-accent/50 hover:text-surface-text'
      )}
    >
      {icon && (
        <span aria-hidden="true" className="flex-shrink-0 text-base">
          {icon}
        </span>
      )}
      {label}
    </button>
  );
}
