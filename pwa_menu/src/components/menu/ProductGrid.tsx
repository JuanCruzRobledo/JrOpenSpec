import type { MenuProduct } from '@/types/menu';
import { ProductCard } from '@/components/menu/ProductCard';

interface ProductGridProps {
  products: MenuProduct[];
  onProductClick: (product: MenuProduct) => void;
}

/**
 * Responsive product grid.
 * - Mobile: 2 columns
 * - Tablet (640px+): 3 columns
 * - Desktop (1024px+): 4 columns
 */
export function ProductGrid({ products, onProductClick }: ProductGridProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          onClick={onProductClick}
        />
      ))}
    </div>
  );
}
