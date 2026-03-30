import { useTranslation } from 'react-i18next';
import { formatPrice } from '@/lib/format';
import type { ProductDetail } from '@/types/product-detail';

interface ProductInfoProps {
  product: Pick<
    ProductDetail,
    | 'name'
    | 'description'
    | 'priceCents'
    | 'isAvailable'
    | 'categoryName'
    | 'subcategoryName'
    | 'preparationTime'
    | 'portionSize'
    | 'calories'
  >;
}

/**
 * Product name, description, price, and metadata.
 */
export function ProductInfo({ product }: ProductInfoProps) {
  const { t } = useTranslation('menu');

  return (
    <div className="flex flex-col gap-3">
      {/* Breadcrumb */}
      {(product.categoryName || product.subcategoryName) && (
        <p className="text-xs text-text-tertiary">
          {[product.categoryName, product.subcategoryName].filter(Boolean).join(' / ')}
        </p>
      )}

      {/* Name */}
      <h1 className="text-xl font-bold text-surface-text leading-tight">
        {product.name}
      </h1>

      {/* Price — large and prominent */}
      <p
        className="text-2xl font-bold text-accent"
        aria-label={t('product.price', { price: formatPrice(product.priceCents) })}
      >
        {formatPrice(product.priceCents)}
      </p>

      {/* Availability */}
      {!product.isAvailable && (
        <span className="inline-flex self-start rounded-full bg-error/20 px-3 py-1 text-xs font-medium text-error">
          {t('product.unavailable')}
        </span>
      )}

      {/* Description */}
      {product.description ? (
        <p className="text-sm text-text-secondary leading-relaxed">
          {product.description}
        </p>
      ) : (
        <p className="text-sm italic text-text-tertiary">{t('product.noDescription')}</p>
      )}

      {/* Metadata row */}
      <div className="flex flex-wrap gap-3 text-xs text-text-tertiary">
        {product.preparationTime !== null && (
          <span>{t('product.preparationTime', { minutes: product.preparationTime })}</span>
        )}
        {product.portionSize !== null && (
          <span>{t('product.portionSize', { size: product.portionSize })}</span>
        )}
        {product.calories !== null && (
          <span>{t('product.calories', { kcal: product.calories })}</span>
        )}
      </div>
    </div>
  );
}
