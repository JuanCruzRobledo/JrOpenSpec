import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';

interface Language {
  code: string;
  flag: string;
  labelKey: 'es' | 'en' | 'pt';
}

const LANGUAGES: Language[] = [
  { code: 'es', flag: '🇦🇷', labelKey: 'es' },
  { code: 'en', flag: '🇺🇸', labelKey: 'en' },
  { code: 'pt', flag: '🇧🇷', labelKey: 'pt' },
];

/**
 * Language picker — 3 pill buttons with flag emoji.
 * Uses i18n.changeLanguage() which persists via i18next-browser-languagedetector to localStorage.
 */
export function LanguageSelector() {
  const { t, i18n } = useTranslation('common');

  const currentLang = i18n.language.slice(0, 2).toLowerCase();

  async function handleSelect(code: string): Promise<void> {
    await i18n.changeLanguage(code);
  }

  return (
    <div
      role="group"
      aria-label={t('language.label')}
      className="flex items-center gap-1"
    >
      {LANGUAGES.map((lang) => {
        const isActive = currentLang === lang.code;
        return (
          <button
            key={lang.code}
            type="button"
            aria-label={t(`language.${lang.labelKey}`)}
            aria-pressed={isActive}
            onClick={() => void handleSelect(lang.code)}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium',
              'min-h-[44px] min-w-[44px]',
              'transition-colors duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
              isActive
                ? 'bg-accent text-white'
                : 'bg-surface-muted text-surface-text/70 hover:text-surface-text hover:bg-surface-border'
            )}
          >
            <span aria-hidden="true">{lang.flag}</span>
            <span className="sr-only">{t(`language.${lang.labelKey}`)}</span>
            <span aria-hidden="true" className="uppercase text-xs">
              {lang.code}
            </span>
          </button>
        );
      })}
    </div>
  );
}
