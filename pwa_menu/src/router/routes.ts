/**
 * Central route path constants.
 *
 * Using `as const` so TypeScript narrows the types to literal strings,
 * enabling type-safe route composition throughout the app.
 *
 * Params:
 * - :tenant  — tenant slug (e.g. "buen-sabor")
 * - :branch  — branch slug (e.g. "sucursal-centro")
 * - :table   — table identifier (e.g. "5") — landing only
 * - :productId — product ID (e.g. "42") — product detail overlay
 */
export const ROUTES = {
  LANDING: '/:tenant/:branch/mesa/:table',
  MENU: '/:tenant/:branch',
  PRODUCT_DETAIL: '/:tenant/:branch/product/:productId',
} as const;
