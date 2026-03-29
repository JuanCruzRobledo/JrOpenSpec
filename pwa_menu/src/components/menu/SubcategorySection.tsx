import type { MenuSubcategory, MenuProduct } from '@/types/menu';
import { ProductGrid } from '@/components/menu/ProductGrid';

interface SubcategorySectionProps {
  subcategory: MenuSubcategory;
  onProductClick: (product: MenuProduct) => void;
}

/**
 * Subcategory header with its product grid.
 */
export function SubcategorySection({ subcategory, onProductClick }: SubcategorySectionProps) {
  if (subcategory.products.length === 0) return null;

  return (
    <section aria-label={subcategory.name}>
      <h3 className="mb-3 text-sm font-medium text-text-secondary uppercase tracking-wide">
        {subcategory.name}
      </h3>
      <ProductGrid products={subcategory.products} onProductClick={onProductClick} />
    </section>
  );
}
