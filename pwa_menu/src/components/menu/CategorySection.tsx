import { forwardRef } from 'react';
import type { MenuCategory, MenuProduct } from '@/types/menu';
import { SubcategorySection } from '@/components/menu/SubcategorySection';

interface CategorySectionProps {
  category: MenuCategory;
  onProductClick: (product: MenuProduct) => void;
}

/**
 * Category section with header and all its subcategories.
 * Forwarded ref used by useCategoryScroll's IntersectionObserver.
 */
export const CategorySection = forwardRef<HTMLElement, CategorySectionProps>(
  function CategorySection({ category, onProductClick }, ref) {
    return (
      <section
        ref={ref}
        id={`category-${category.id}`}
        aria-label={category.name}
        className="scroll-mt-28"
      >
        <h2 className="mb-4 text-lg font-bold text-surface-text">
          {category.name}
        </h2>

        <div className="flex flex-col gap-6">
          {category.subcategories.map((sub) => (
            <SubcategorySection
              key={sub.id}
              subcategory={sub}
              onProductClick={onProductClick}
            />
          ))}
        </div>
      </section>
    );
  }
);
