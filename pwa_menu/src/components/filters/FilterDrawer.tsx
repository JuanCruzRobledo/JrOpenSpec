import { useTranslation } from 'react-i18next';
import { Drawer } from '@/components/ui/Drawer';
import { AllergenFilterSection } from '@/components/filters/AllergenFilterSection';
import { DietaryFilterSection } from '@/components/filters/DietaryFilterSection';
import { CookingFilterSection } from '@/components/filters/CookingFilterSection';
import { ClearFiltersButton } from '@/components/filters/ClearFiltersButton';
import type { MenuCategory } from '@/types/menu';

interface FilterDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  /** Full (unfiltered) category tree for extracting dietary/cooking options */
  categories: MenuCategory[];
}

/**
 * Filter drawer — orchestrates all filter sections.
 * Uses the Drawer component (right-side on desktop, bottom-sheet on mobile).
 *
 * Filters update the filter store in real time — no "Apply" button needed.
 * The "Clear" button is shown only when at least one filter is active.
 */
export function FilterDrawer({ isOpen, onClose, categories }: FilterDrawerProps) {
  const { t } = useTranslation('filters');

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={t('title')}
    >
      <div className="flex flex-col gap-6">
        {/* Allergen section — mode + chips */}
        <AllergenFilterSection />

        {/* Dietary profile chips */}
        <DietaryFilterSection categories={categories} />

        {/* Cooking method chips */}
        <CookingFilterSection categories={categories} />

        {/* Clear all button — sticky at bottom */}
        <div className="sticky bottom-0 pt-2 pb-safe-area-inset-bottom bg-surface-card">
          <ClearFiltersButton />
        </div>
      </div>
    </Drawer>
  );
}
