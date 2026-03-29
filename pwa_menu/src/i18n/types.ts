/**
 * Type-safe i18n key definitions.
 * These types are derived from the default (es) locale files.
 *
 * Usage in components:
 *   const { t } = useTranslation('common');
 *   t('app.name')  // type-checked
 *
 * Usage with namespace:
 *   const { t } = useTranslation('menu');
 *   t('search.placeholder')  // type-checked
 */

import type common from './locales/es/common.json';
import type session from './locales/es/session.json';
import type menu from './locales/es/menu.json';
import type filters from './locales/es/filters.json';
import type allergens from './locales/es/allergens.json';

/**
 * Augment the i18next module to enable type-safe `t()` calls.
 * TypeScript infers all valid keys from the Spanish locale files.
 */
declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common';
    resources: {
      common: typeof common;
      session: typeof session;
      menu: typeof menu;
      filters: typeof filters;
      allergens: typeof allergens;
    };
  }
}
