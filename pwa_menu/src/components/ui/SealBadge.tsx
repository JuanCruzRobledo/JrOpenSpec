import { cn } from '@/lib/cn';

interface SealBadgeProps {
  name: string;
  imageUrl: string | null;
  className?: string;
}

/**
 * Circular seal badge for quality certifications (e.g. "Sin TACC", "Apto Vegano").
 * Shows an image if available, otherwise shows the first letter of the name.
 */
export function SealBadge({ name, imageUrl, className }: SealBadgeProps) {
  return (
    <span
      title={name}
      aria-label={name}
      className={cn(
        'inline-flex h-7 w-7 items-center justify-center overflow-hidden rounded-full',
        'border border-surface-border bg-surface-muted',
        'text-xs font-bold text-surface-text',
        className
      )}
    >
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={name}
          className="h-full w-full object-cover"
          loading="lazy"
        />
      ) : (
        <span aria-hidden="true">{name.charAt(0).toUpperCase()}</span>
      )}
    </span>
  );
}
