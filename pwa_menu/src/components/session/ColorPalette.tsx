import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import { AVATAR_COLORS, type AvatarColor } from '@/config/constants';

interface ColorPaletteProps {
  selectedColor: AvatarColor | string;
  onSelect: (color: AvatarColor) => void;
}

/**
 * 16-color avatar color picker.
 * Selected color shows an orange ring (accent color) to match the app theme.
 */
export function ColorPalette({ selectedColor, onSelect }: ColorPaletteProps) {
  const { t } = useTranslation('session');

  return (
    <div>
      <p className="mb-2 text-sm font-medium text-surface-text">
        {t('landing.colorLabel')}
      </p>
      <div
        role="radiogroup"
        aria-label={t('landing.colorLabel')}
        className="grid grid-cols-8 gap-2"
      >
        {AVATAR_COLORS.map((color) => {
          const isSelected = color === selectedColor;
          return (
            <button
              key={color}
              type="button"
              role="radio"
              aria-checked={isSelected}
              aria-label={color}
              onClick={() => onSelect(color)}
              className={cn(
                'h-8 w-8 rounded-full transition-all duration-150',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
                // Selected: orange ring
                isSelected
                  ? 'ring-2 ring-accent ring-offset-2 ring-offset-surface-bg scale-110'
                  : 'hover:scale-110 hover:ring-2 hover:ring-white/40 hover:ring-offset-1 hover:ring-offset-surface-bg'
              )}
              style={{ backgroundColor: color }}
            />
          );
        })}
      </div>
    </div>
  );
}
