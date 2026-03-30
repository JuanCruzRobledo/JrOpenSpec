/**
 * Text normalization utilities for search and display.
 * Critical for Spanish/Portuguese menus with accented characters.
 */

/**
 * Removes diacritics/accents from a string.
 * Uses Unicode NFD normalization + regex to strip combining marks.
 *
 * @example
 *   removeAccents("Ñoños")    // "Nonos"
 *   removeAccents("Crêpes")   // "Crepes"
 *   removeAccents("Müsli")    // "Musli"
 */
export function removeAccents(str: string): string {
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

/**
 * Normalizes a string for accent-insensitive search comparison.
 * Lowercases + removes accents + trims whitespace.
 *
 * @example
 *   normalizeSearch("  Ñoqueños  ") // "noquenos"
 *   normalizeSearch("CAFÉ")         // "cafe"
 */
export function normalizeSearch(str: string): string {
  return removeAccents(str.toLowerCase().trim());
}

/**
 * Checks if a haystack string contains the needle, accent-insensitively.
 *
 * @example
 *   searchIncludes("Ñoquis a la Fileto", "noqui") // true
 *   searchIncludes("Café con leche", "cafe")       // true
 */
export function searchIncludes(haystack: string, needle: string): boolean {
  if (!needle) return true;
  return normalizeSearch(haystack).includes(normalizeSearch(needle));
}

/**
 * Truncates a string to maxLength characters, appending ellipsis if needed.
 * Avoids cutting mid-word when possible.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  const truncated = str.slice(0, maxLength - 3);
  const lastSpace = truncated.lastIndexOf(' ');
  // If there's a space within the last 20 chars, cut at word boundary
  if (lastSpace > maxLength - 23) {
    return truncated.slice(0, lastSpace) + '...';
  }
  return truncated + '...';
}

/**
 * Converts URL slugs into a human-friendly label.
 */
export function humanizeSlug(str: string): string {
  return str
    .split('-')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}
