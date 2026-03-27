// Formatting utilities for currency, dates, etc.

const currencyFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * Format cents (integer) to Argentine peso currency string.
 * Example: 12550 -> "$125,50"
 */
export function formatCurrency(cents: number): string {
  return currencyFormatter.format(cents / 100);
}

const dateFormatter = new Intl.DateTimeFormat('es-AR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

/**
 * Format an ISO date string to "DD/MM/YYYY HH:mm" (Argentina locale).
 */
export function formatDate(isoString: string): string {
  return dateFormatter.format(new Date(isoString));
}
