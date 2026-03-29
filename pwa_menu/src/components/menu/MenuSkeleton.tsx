import { Skeleton } from '@/components/ui/Skeleton';
import { useTranslation } from 'react-i18next';

/**
 * Full-page skeleton shown while the menu is loading.
 * Matches the layout of CategoryTabs + ProductGrid.
 */
export function MenuSkeleton() {
  const { t } = useTranslation('menu');

  return (
    <div
      role="status"
      aria-label={t('loading')}
      aria-busy="true"
      className="w-full"
    >
      {/* Category tabs skeleton */}
      <div className="flex gap-2 overflow-hidden px-4 py-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-11 w-24 flex-shrink-0 rounded-full" />
        ))}
      </div>

      {/* Category header skeleton */}
      <div className="px-4 pt-4 pb-2">
        <Skeleton className="h-6 w-40 rounded" />
      </div>

      {/* Subcategory header skeleton */}
      <div className="px-4 py-2">
        <Skeleton className="h-4 w-28 rounded" />
      </div>

      {/* Product grid skeleton — 2 cols on mobile */}
      <div className="grid grid-cols-2 gap-3 px-4 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex flex-col gap-2 rounded-xl overflow-hidden">
            {/* Image placeholder */}
            <Skeleton className="aspect-[4/3] w-full rounded-none rounded-t-xl" />
            {/* Text placeholders */}
            <div className="flex flex-col gap-1.5 p-3">
              <Skeleton className="h-4 w-full rounded" />
              <Skeleton className="h-4 w-3/4 rounded" />
              <Skeleton className="h-5 w-16 rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
