import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';

interface FlavorTextureSectionProps {
  flavorProfiles: string[];
  textureProfiles: string[];
}

/**
 * Flavor and texture tag clouds.
 */
export function FlavorTextureSection({ flavorProfiles, textureProfiles }: FlavorTextureSectionProps) {
  const { t } = useTranslation('menu');

  const hasContent = flavorProfiles.length > 0 || textureProfiles.length > 0;
  if (!hasContent) return null;

  return (
    <div className="flex flex-col gap-3">
      {flavorProfiles.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-tertiary">
            {t('detail.flavorProfile')}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {flavorProfiles.map((flavor) => (
              <span
                key={flavor}
                className={cn(
                  'rounded-full px-3 py-1 text-xs font-medium',
                  'bg-accent/10 border border-accent/30 text-accent'
                )}
              >
                {flavor}
              </span>
            ))}
          </div>
        </div>
      )}

      {textureProfiles.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-tertiary">
            {t('detail.textureProfile')}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {textureProfiles.map((texture) => (
              <span
                key={texture}
                className={cn(
                  'rounded-full px-3 py-1 text-xs font-medium',
                  'bg-surface-muted border border-surface-border text-text-secondary'
                )}
              >
                {texture}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
