import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import { Skeleton } from '@/components/ui/Skeleton';

interface ProductImageGalleryProps {
  imageUrls: string[];
  productName: string;
}

/**
 * Product image gallery.
 * - Single large primary image
 * - Thumbnail row if gallery has more than 1 image
 * - Lazy loading with skeleton placeholder
 */
export function ProductImageGallery({ imageUrls, productName }: ProductImageGalleryProps) {
  const { t } = useTranslation('menu');
  const [activeIndex, setActiveIndex] = useState(0);
  const [loadedIndices, setLoadedIndices] = useState<Set<number>>(new Set());
  const [errorIndices, setErrorIndices] = useState<Set<number>>(new Set());

  const handleImageLoad = useCallback((index: number) => {
    setLoadedIndices((prev) => new Set([...prev, index]));
  }, []);

  const handleImageError = useCallback((index: number) => {
    setErrorIndices((prev) => new Set([...prev, index]));
    setLoadedIndices((prev) => new Set([...prev, index]));
  }, []);

  const activeUrl = imageUrls[activeIndex];
  const isActiveLoaded = loadedIndices.has(activeIndex);
  const isActiveError = errorIndices.has(activeIndex);

  if (imageUrls.length === 0) {
    return (
      <div className="flex aspect-video w-full items-center justify-center rounded-xl bg-surface-muted">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-12 w-12 text-text-tertiary"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M1.5 6a2.25 2.25 0 0 1 2.25-2.25h16.5A2.25 2.25 0 0 1 22.5 6v12a2.25 2.25 0 0 1-2.25 2.25H3.75A2.25 2.25 0 0 1 1.5 18V6ZM3 16.06V18c0 .414.336.75.75.75h16.5A.75.75 0 0 0 21 18v-1.94l-2.69-2.689a1.5 1.5 0 0 0-2.12 0l-.88.879.97.97a.75.75 0 1 1-1.06 1.06l-5.16-5.159a1.5 1.5 0 0 0-2.12 0L3 16.061Zm10.125-7.81a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Z"
            clipRule="evenodd"
          />
        </svg>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Primary image */}
      <div className="relative aspect-video w-full overflow-hidden rounded-xl bg-surface-muted">
        {!isActiveLoaded && (
          <Skeleton
            className="absolute inset-0 h-full w-full rounded-none"
            aria-label={t('product.imageAlt', { name: productName })}
          />
        )}
        {!isActiveError && activeUrl ? (
          <img
            key={activeUrl}
            src={activeUrl}
            alt={t('product.imageAlt', { name: productName })}
            loading="lazy"
            onLoad={() => handleImageLoad(activeIndex)}
            onError={() => handleImageError(activeIndex)}
            className={cn(
              'h-full w-full object-cover transition-opacity duration-200',
              isActiveLoaded ? 'opacity-100' : 'opacity-0'
            )}
          />
        ) : isActiveError ? (
          <div className="flex h-full w-full items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="h-12 w-12 text-text-tertiary"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M1.5 6a2.25 2.25 0 0 1 2.25-2.25h16.5A2.25 2.25 0 0 1 22.5 6v12a2.25 2.25 0 0 1-2.25 2.25H3.75A2.25 2.25 0 0 1 1.5 18V6Z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        ) : null}
      </div>

      {/* Thumbnails — only shown when gallery has multiple images */}
      {imageUrls.length > 1 && (
        <div className="flex gap-2 overflow-x-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          {imageUrls.map((url, index) => (
            <button
              key={url}
              type="button"
              onClick={() => setActiveIndex(index)}
              aria-label={t('product.imageAlt', { name: productName })}
              aria-pressed={index === activeIndex}
              className={cn(
                'relative h-14 w-14 flex-shrink-0 overflow-hidden rounded-lg',
                'transition-all duration-150',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
                index === activeIndex
                  ? 'ring-2 ring-accent'
                  : 'opacity-60 hover:opacity-100'
              )}
            >
              <img
                src={url}
                alt=""
                aria-hidden="true"
                loading="lazy"
                onLoad={() => handleImageLoad(index)}
                onError={() => handleImageError(index)}
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
