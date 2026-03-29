/**
 * Application-wide constants.
 * All timing values in milliseconds unless noted otherwise.
 */

/** Base URL for the REST API backend, injected at build time */
export const API_URL = import.meta.env['VITE_API_URL'] as string;

/** Menu data cache TTL — 5 minutes before stale-while-revalidate kicks in */
export const CACHE_TTL_MS = 300_000;

/** Allergen catalog cache TTL — same as menu */
export const ALLERGEN_CACHE_TTL_MS = 300_000;

/** Session inactivity window — 8 hours in milliseconds */
export const SESSION_INACTIVITY_MS = 28_800_000;

/** Search input debounce delay */
export const DEBOUNCE_MS = 300;

/** Toast auto-dismiss duration */
export const TOAST_DURATION_MS = 4_000;

/** Maximum visible toasts at once */
export const TOAST_MAX = 5;

/** PWA install banner shows after this delay */
export const INSTALL_BANNER_DELAY_MS = 30_000;

/** PWA install banner dismiss cooldown — 7 days */
export const INSTALL_BANNER_COOLDOWN_MS = 7 * 24 * 60 * 60 * 1_000;

/** LocalStorage key for install banner dismiss timestamp */
export const INSTALL_BANNER_DISMISSED_KEY = 'buen-sabor-install-dismissed';

/** Maximum display name length */
export const DISPLAY_NAME_MAX_LENGTH = 50;

/**
 * Avatar color palette — exactly 16 colors as specified in the spec.
 * Covers the full hue spectrum for maximum visual differentiation.
 * Used for anonymous session identification in the menu.
 */
export const AVATAR_COLORS = [
  '#EF4444', // red-500
  '#F97316', // orange-500
  '#F59E0B', // amber-500
  '#EAB308', // yellow-500
  '#84CC16', // lime-500
  '#22C55E', // green-500
  '#10B981', // emerald-500
  '#14B8A6', // teal-500
  '#06B6D4', // cyan-500
  '#3B82F6', // blue-500
  '#6366F1', // indigo-500
  '#8B5CF6', // violet-500
  '#A855F7', // purple-500
  '#EC4899', // pink-500
  '#F43F5E', // rose-500
  '#78716C', // stone-500
] as const;

/** Type for a valid avatar color value */
export type AvatarColor = (typeof AVATAR_COLORS)[number];

/**
 * Picks a random avatar color from the palette.
 * Used to initialize the color selection on the landing page.
 */
export function pickRandomAvatarColor(): AvatarColor {
  const index = Math.floor(Math.random() * AVATAR_COLORS.length);
  // noUncheckedIndexedAccess: assert non-null since index is bounded
  return AVATAR_COLORS[index] as AvatarColor;
}
