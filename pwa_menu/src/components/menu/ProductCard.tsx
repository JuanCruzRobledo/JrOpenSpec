import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import { formatPrice } from '@/lib/format';
import { Badge } from '@/components/ui/Badge';
import { SealBadge } from '@/components/ui/SealBadge';
import { Skeleton } from '@/components/ui/Skeleton';
import type { MenuProduct } from '@/types/menu';

interface ProductCardProps {
  product: MenuProduct;
  onClick: (product: MenuProduct) => void;
}

const MAX_VISIBLE_BADGES = 3;

/**
 * Menu product card with lazy image, badges, availability overlay, and allergen hints.
 * Clicking opens the product detail modal.
 */
export function ProductCard({ product, onClick }: ProductCardProps) {
  const { t } = useTranslation('menu');
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleImageLoad = useCallback(() => setImageLoaded(true), []);
  const handleImageError = useCallback(() => {
    setImageError(true);
    setImageLoaded(true); // Stop showing skeleton
  }, []);

  const handleClick = useCallback(() => {
    onClick(product);
  }, [onClick, product]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onClick(product);
      }
    },
    [onClick, product]
  );

  const visibleBadges = product.badges.slice(0, MAX_VISIBLE_BADGES);
  const extraBadgeCount = product.badges.length - MAX_VISIBLE_BADGES;

  return (
    <article
      role="article"
      aria-label={product.name}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      className={cn(
        'relative flex flex-col overflow-hidden rounded-xl',
        'bg-surface-card border border-surface-border',
        'cursor-pointer',
        'transition-colors duration-150',
        'hover:border-accent/50 hover:bg-surface-card',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
        !product.isAvailable && 'opacity-80'
      )}
    >
      {/* Product image */}
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-surface-muted">
        {/* Skeleton while image loads */}
        {!imageLoaded && (
          <Skeleton
            className="absolute inset-0 h-full w-full rounded-none"
            aria-label={t('product.imageAlt', { name: product.name })}
          />
        )}

        {product.imageUrl && !imageError ? (
          <img
            src={product.imageUrl}
            alt={t('product.imageAlt', { name: product.name })}
            loading="lazy"
            onLoad={handleImageLoad}
            onError={handleImageError}
            className={cn(
              'h-full w-full object-cover transition-opacity duration-200',
              imageLoaded ? 'opacity-100' : 'opacity-0'
            )}
          />
        ) : imageLoaded ? (
          // Placeholder when no image or load failed
          <div className="flex h-full w-full items-center justify-center bg-surface-muted">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="h-10 w-10 text-text-tertiary"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M1.5 6a2.25 2.25 0 0 1 2.25-2.25h16.5A2.25 2.25 0 0 1 22.5 6v12a2.25 2.25 0 0 1-2.25 2.25H3.75A2.25 2.25 0 0 1 1.5 18V6ZM3 16.06V18c0 .414.336.75.75.75h16.5A.75.75 0 0 0 21 18v-1.94l-2.69-2.689a1.5 1.5 0 0 0-2.12 0l-.88.879.97.97a.75.75 0 1 1-1.06 1.06l-5.16-5.159a1.5 1.5 0 0 0-2.12 0L3 16.061Zm10.125-7.81a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        ) : null}

        {/* Unavailable overlay */}
        {!product.isAvailable && (
          <div className="absolute inset-0 flex items-center justify-center bg-surface-bg/70">
            <span className="rounded-full bg-surface-bg/90 px-3 py-1 text-xs font-semibold text-text-secondary">
              {t('product.unavailable')}
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col gap-1.5 p-3">
        {/* Product name */}
        <h3 className="line-clamp-2 text-sm font-semibold text-surface-text leading-snug">
          {product.name}
        </h3>

        {/* Price */}
        <p className="text-sm font-bold text-accent" aria-label={t('product.price', { price: formatPrice(product.priceCents) })}>
          {formatPrice(product.priceCents)}
        </p>

        {/* Badges row */}
        {product.badges.length > 0 && (
          <div className="flex flex-wrap items-center gap-1">
            {visibleBadges.map((badge) => (
              <Badge key={badge.id} name={badge.name} colorHex={badge.colorHex} />
            ))}
            {extraBadgeCount > 0 && (
              <span className="text-xs text-text-tertiary">
                {t('product.badgesCount', { count: extraBadgeCount })}
              </span>
            )}
          </div>
        )}

        {/* Seals row */}
        {product.seals.length > 0 && (
          <div className="flex items-center gap-1 mt-auto pt-1">
            {product.seals.map((seal) => (
              <SealBadge key={seal.id} name={seal.name} imageUrl={seal.imageUrl} />
            ))}
          </div>
        )}

        {/* Allergen summary — small dots for 'contains' allergens */}
        {product.allergenSlugs.length > 0 && (
          <p className="mt-auto text-[10px] text-text-tertiary leading-tight" aria-hidden="true">
            {product.allergenSlugs.slice(0, 5).join(' · ')}
            {product.allergenSlugs.length > 5 && ' · …'}
          </p>
        )}
      </div>
    </article>
  );
}
