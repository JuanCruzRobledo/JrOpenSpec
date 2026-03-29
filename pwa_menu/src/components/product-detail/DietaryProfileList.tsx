import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import type { DietaryProfileInfo } from '@/types/product-detail';

interface DietaryProfileListProps {
  profiles: DietaryProfileInfo[];
}

/**
 * Dietary profile chips with icon and name.
 */
export function DietaryProfileList({ profiles }: DietaryProfileListProps) {
  const { t } = useTranslation('menu');

  if (profiles.length === 0) {
    return (
      <p className="text-sm italic text-text-tertiary">{t('detail.noDietary')}</p>
    );
  }

  return (
    <div
      className="flex flex-wrap gap-2"
      aria-label={t('detail.dietary')}
    >
      {profiles.map((profile) => (
        <span
          key={profile.id}
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full px-3 py-1.5',
            'text-xs font-medium',
            'bg-success/10 border border-success/30 text-success'
          )}
        >
          {profile.iconName && (
            <span aria-hidden="true" className="text-sm">{profile.iconName}</span>
          )}
          {profile.name}
        </span>
      ))}
    </div>
  );
}
