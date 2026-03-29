import { useTranslation } from 'react-i18next';
import { Input } from '@/components/ui/Input';
import { DISPLAY_NAME_MAX_LENGTH } from '@/config/constants';

interface NameInputProps {
  value: string;
  onChange: (value: string) => void;
}

/**
 * Controlled name input for the landing page.
 * Optional — empty value sends anonymous session.
 */
export function NameInput({ value, onChange }: NameInputProps) {
  const { t } = useTranslation('session');

  return (
    <div className="flex flex-col gap-1">
      <Input
        type="text"
        label={t('landing.nameLabel')}
        placeholder={t('landing.namePlaceholder')}
        value={value}
        maxLength={DISPLAY_NAME_MAX_LENGTH}
        onChange={(e) => onChange(e.target.value)}
        showClearButton={value.length > 0}
        onClear={() => onChange('')}
        aria-label={t('landing.nameLabel')}
        autoComplete="given-name"
        autoCapitalize="words"
        spellCheck={false}
      />
      {value.length > 0 && (
        <p className="text-right text-xs text-surface-text/50">
          {value.length}/{DISPLAY_NAME_MAX_LENGTH}
        </p>
      )}
    </div>
  );
}
