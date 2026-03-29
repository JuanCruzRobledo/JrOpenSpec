import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

/**
 * i18n configuration.
 *
 * Detection order: localStorage (i18nextLng) → navigator.language → fallback 'es'
 * Namespaces:
 *   - 'common'   → loaded EAGERLY (in this init call) — shared UI strings
 *   - 'session'  → lazy via Suspense when SessionFlow mounts
 *   - 'menu'     → lazy via Suspense when MenuPage mounts
 *   - 'filters'  → lazy via Suspense when FilterDrawer mounts
 *   - 'allergens'→ lazy via Suspense when AllergenList mounts
 */
void i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    // Default namespace used when no ns is specified
    defaultNS: 'common',

    // Only 'common' is loaded eagerly; the rest are lazy
    ns: ['common'],
    preload: ['es'],

    // Supported languages
    supportedLngs: ['es', 'en', 'pt'],
    nonExplicitSupportedLngs: true, // 'es-AR' matches 'es'

    // Fallback chain: detected → es → raw key
    fallbackLng: 'es',
    fallbackNS: false,

    // Detection plugin configuration
    detection: {
      // Order matters: check localStorage first, then browser language
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'i18nextLng',
      caches: ['localStorage'],
    },

    // Backend loads JSON files from /locales/{{lng}}/{{ns}}.json
    // NOTE: Runtime files live in public/locales/ (served as static assets).
    //       Source files in src/i18n/locales/ are used for TypeScript type inference only.
    //       When updating translations, update BOTH locations (or set up a build-time copy script).
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },

    // Suspense: lazy namespaces trigger React Suspense while loading
    react: {
      useSuspense: true,
    },

    interpolation: {
      // React already escapes by default
      escapeValue: false,
    },

    // Show raw key if translation missing (visible in dev, acceptable in prod)
    missingKeyHandler: false,
  });

export default i18n;
