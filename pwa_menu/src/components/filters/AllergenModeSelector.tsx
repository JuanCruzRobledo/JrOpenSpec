import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import type { AllergenMode } from '@/types/filters';
import {
  useFilterStore,
  selectAllergenMode,
  selectSetAllergenModeAction,
} from '@/stores/filter.store';

const MODES: AllergenMode[] = ['off', 'strict', 'very_strict'];

/**
 * Radio group for allergen filter mode selection.
 * - off: no filtering
 * - strict: hide products that CONTAIN selected allergens
 * - very_strict: hide products that contain OR may contain, including cross-reactions
 */
export function AllergenModeSelector() {
  const { t } = useTranslation('filters');
  const currentMode = useFilterStore(selectAllergenMode);
  const setAllergenMode = useFilterStore(selectSetAllergenModeAction);

  const handleSelect = useCallback(
    (mode: AllergenMode) => {
      setAllergenMode(mode);
    },
    [setAllergenMode]
  );

  return (
    <div
      role="radiogroup"
      aria-label={t('allergenMode.label')}
      className="flex flex-col gap-2"
    >
      {MODES.map((mode) => {
        const isSelected = currentMode === mode;
        return (
          <button
            key={mode}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => handleSelect(mode)}
            className={cn(
              'flex flex-col items-start rounded-xl px-3 py-3 text-left',
              'min-h-[44px]',
              'transition-colors duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
              isSelected
                ? 'bg-accent/15 border border-accent text-surface-text'
                : 'bg-surface-muted border border-surface-border text-text-secondary hover:border-accent/50 hover:text-surface-text'
            )}
          >
            <span className="flex items-center gap-2 font-medium text-sm">
              {/* Radio indicator */}
              <span
                className={cn(
                  'flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full border-2',
                  isSelected ? 'border-accent' : 'border-text-tertiary'
                )}
                aria-hidden="true"
              >
                {isSelected && (
                  <span className="h-2 w-2 rounded-full bg-accent" />
                )}
              </span>
              {t(`allergenMode.${mode}`)}
            </span>
            <span className="mt-0.5 pl-6 text-xs opacity-70">
              {t(`allergenMode.${mode}Description`)}
            </span>
          </button>
        );
      })}
    </div>
  );
}
