import { cn } from '@/lib/cn';

interface SkeletonProps {
  className?: string;
  'aria-label'?: string;
}

/**
 * Loading placeholder with pulse animation.
 * Shape and size are controlled via className.
 *
 * @example
 *   // Rectangle
 *   <Skeleton className="h-4 w-32 rounded" />
 *   // Circle
 *   <Skeleton className="h-10 w-10 rounded-full" />
 *   // Card
 *   <Skeleton className="h-48 w-full rounded-lg" />
 */
export function Skeleton({ className, 'aria-label': ariaLabel }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label={ariaLabel}
      aria-busy="true"
      className={cn(
        'animate-pulse rounded bg-surface-muted',
        className
      )}
    />
  );
}
