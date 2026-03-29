import { Skeleton } from '@/components/ui/Skeleton';
import { useTranslation } from 'react-i18next';

/**
 * Skeleton placeholder for the full product detail modal content.
 */
export function ProductDetailSkeleton() {
  const { t } = useTranslation('menu');

  return (
    <div role="status" aria-label={t('loading')} aria-busy="true" className="flex flex-col gap-5">
      {/* Image skeleton */}
      <Skeleton className="aspect-video w-full rounded-xl" />

      {/* Name and price */}
      <div className="flex flex-col gap-2">
        <Skeleton className="h-3 w-32 rounded" />
        <Skeleton className="h-7 w-3/4 rounded" />
        <Skeleton className="h-8 w-24 rounded" />
        <Skeleton className="h-4 w-full rounded" />
        <Skeleton className="h-4 w-5/6 rounded" />
      </div>

      {/* Badges row */}
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-6 w-14 rounded-full" />
      </div>

      {/* Section header */}
      <Skeleton className="h-4 w-24 rounded" />

      {/* Allergen entries */}
      <div className="flex flex-col gap-2">
        <Skeleton className="h-14 w-full rounded-lg" />
        <Skeleton className="h-14 w-full rounded-lg" />
      </div>

      {/* Ingredients */}
      <Skeleton className="h-4 w-24 rounded" />
      <div className="flex flex-col gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-5 w-full rounded" />
        ))}
      </div>
    </div>
  );
}
