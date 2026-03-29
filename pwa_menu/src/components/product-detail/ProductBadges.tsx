import { Badge } from '@/components/ui/Badge';
import { SealBadge } from '@/components/ui/SealBadge';
import type { Badge as BadgeType, Seal } from '@/types/menu';

interface ProductBadgesProps {
  badges: BadgeType[];
  seals: Seal[];
}

/**
 * Full badges and seals section for product detail.
 * Shows all badges (no truncation) and all seals with SealBadge.
 */
export function ProductBadges({ badges, seals }: ProductBadgesProps) {
  if (badges.length === 0 && seals.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      {badges.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {badges.map((badge) => (
            <Badge key={badge.id} name={badge.name} colorHex={badge.colorHex} />
          ))}
        </div>
      )}

      {seals.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          {seals.map((seal) => (
            <SealBadge key={seal.id} name={seal.name} imageUrl={seal.imageUrl} />
          ))}
        </div>
      )}
    </div>
  );
}
