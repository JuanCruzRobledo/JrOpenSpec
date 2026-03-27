import { cn } from '@/lib/cn';

interface Props {
  className?: string;
  width?: string | number;
  height?: string | number;
}

export function Skeleton({ className, width, height }: Props) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-bg-elevated',
        className,
      )}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}
