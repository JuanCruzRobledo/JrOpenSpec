import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from '@/components/ui/Modal';
import { ProductDetailSkeleton } from '@/components/product-detail/ProductDetailSkeleton';
import { ProductImageGallery } from '@/components/product-detail/ProductImageGallery';
import { ProductInfo } from '@/components/product-detail/ProductInfo';
import { AllergenList } from '@/components/product-detail/AllergenList';
import { IngredientList } from '@/components/product-detail/IngredientList';
import { DietaryProfileList } from '@/components/product-detail/DietaryProfileList';
import { CookingMethodList } from '@/components/product-detail/CookingMethodList';
import { FlavorTextureSection } from '@/components/product-detail/FlavorTextureSection';
import {
  useProductDetailStore,
  selectProduct,
  selectProductIsLoading,
  selectProductIsOpen,
} from '@/stores/product-detail.store';

interface ProductDetailModalProps {
  onClose: () => void;
}

/**
 * Product detail bottom-sheet / modal.
 *
 * Uses the existing Modal component (slide-up on mobile, centered on desktop).
 * URL sync (open/close navigation) is handled by the parent (MenuPage).
 * Focus management and aria-modal are delegated to Modal.
 */
export function ProductDetailModal({ onClose }: ProductDetailModalProps) {
  const { t } = useTranslation('menu');

  const product = useProductDetailStore(selectProduct);
  const isLoading = useProductDetailStore(selectProductIsLoading);
  const isOpen = useProductDetailStore(selectProductIsOpen);

  const title = product?.name ?? t('detail.title');

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      className="md:max-w-2xl"
    >
      {isLoading ? (
        <ProductDetailSkeleton />
      ) : product ? (
        <div className="flex flex-col gap-6">
          {/* Image gallery */}
          <ProductImageGallery
            imageUrls={product.imageUrls}
            productName={product.name}
          />

          {/* Name, price, description, metadata */}
          <ProductInfo product={product} />

          {/* Allergens section */}
          <DetailSection title={t('detail.allergens')}>
            <AllergenList allergens={product.allergens} />
          </DetailSection>

          {/* Ingredients section */}
          <DetailSection title={t('detail.ingredients')}>
            <IngredientList ingredients={product.ingredients} />
          </DetailSection>

          {/* Dietary profiles */}
          <DetailSection title={t('detail.dietary')}>
            <DietaryProfileList profiles={product.dietaryProfiles} />
          </DetailSection>

          {/* Cooking methods */}
          <DetailSection title={t('detail.cookingMethods')}>
            <CookingMethodList methods={product.cookingMethods} />
          </DetailSection>

          {/* Flavor and texture */}
          <FlavorTextureSection
            flavorProfiles={product.flavorProfiles}
            textureProfiles={product.textureProfiles}
          />
        </div>
      ) : null}
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Local helper — labeled section wrapper
// ---------------------------------------------------------------------------

interface DetailSectionProps {
  title: string;
  children: ReactNode;
}

function DetailSection({ title, children }: DetailSectionProps) {
  return (
    <section aria-label={title}>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-tertiary">
        {title}
      </h3>
      {children}
    </section>
  );
}
