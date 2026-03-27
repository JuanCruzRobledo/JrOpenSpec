import { cn } from '@/lib/cn';

type BadgeVariant = 'success' | 'error' | 'warning' | 'info' | 'default';

interface Props {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  success: 'bg-success/15 text-success',
  error: 'bg-error/15 text-error',
  warning: 'bg-warning/15 text-warning',
  info: 'bg-info/15 text-info',
  default: 'bg-bg-elevated text-text-secondary',
};

export function Badge({ children, variant = 'default', className }: Props) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variantStyles[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
