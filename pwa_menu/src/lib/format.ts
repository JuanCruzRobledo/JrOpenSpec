/**
 * Price formatting utilities.
 *
 * IMPORTANT: Prices are stored as integer centavos in the backend.
 * Display rule: backendCents / 100  → e.g. 150000 → "$1.500"
 * Send to backend: Math.round(displayPrice * 100)
 */

/**
 * Formats a centavo amount to a locale-aware currency string.
 * Uses Argentine Spanish dot-separator format as default.
 *
 * @param centavos - Integer amount in centavos (e.g. 150000 = $1.500)
 * @param locale   - BCP 47 locale string, defaults to 'es-AR'
 * @returns        - Formatted price string, e.g. "$1.500"
 *
 * @example
 *   formatPrice(150000) // "$1.500"
 *   formatPrice(1500)   // "$15"
 *   formatPrice(150)    // "$1,50"
 */
export function formatPrice(centavos: number, locale: string = 'es-AR'): string {
  const amount = centavos / 100;

  // Intl.NumberFormat handles locale-specific separators correctly
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: amount % 1 === 0 ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Converts a display price (pesos) back to centavos for backend.
 *
 * @param displayPrice - Float price in pesos (e.g. 1500.50)
 * @returns            - Integer centavos (e.g. 150050)
 */
export function toCentavos(displayPrice: number): number {
  return Math.round(displayPrice * 100);
}
