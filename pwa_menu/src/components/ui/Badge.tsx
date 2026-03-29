import { cn } from '@/lib/cn';

interface BadgeProps {
  name: string;
  colorHex: string;
  className?: string;
}

/**
 * Small pill badge for product labels (e.g. "Destacado", "Nuevo").
 * Color is applied inline from the badge's configured hex color.
 */
export function Badge({ name, colorHex, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        className
      )}
      style={{
        backgroundColor: `${colorHex}26`, // 15% opacity background
        color: colorHex,
        borderColor: `${colorHex}4D`, // 30% opacity border
        border: '1px solid',
      }}
    >
      {name}
    </span>
  );
}
