import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merges Tailwind CSS class names safely, resolving conflicts via tailwind-merge.
 * Uses clsx for conditional class handling.
 *
 * @example
 *   cn('px-4 py-2', condition && 'bg-accent', 'hover:bg-accent-hover')
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
