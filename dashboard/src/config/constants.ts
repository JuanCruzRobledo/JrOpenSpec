// Application constants

export const API_URL = import.meta.env.VITE_API_URL;

/** Milliseconds before token expiry to trigger proactive refresh (60s) */
export const TOKEN_REFRESH_MARGIN_MS = 60_000;

/** Default toast auto-dismiss duration in milliseconds */
export const TOAST_DURATION_MS = 5_000;

/** Default page size for paginated lists */
export const PAGE_SIZE = 20;

/** Maximum number of visible toasts at once */
export const MAX_TOASTS = 5;

/** Sidebar width in pixels when expanded */
export const SIDEBAR_WIDTH = 280;

/** Sidebar width in pixels when collapsed */
export const SIDEBAR_COLLAPSED_WIDTH = 64;

/** Reusable empty array constant to prevent unnecessary re-renders */
export const EMPTY_ARRAY: readonly never[] = Object.freeze([]);
