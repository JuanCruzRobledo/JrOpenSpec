/**
 * Tabbed product form — 8 tabs for full product management.
 * Each tab saves independently via the corresponding API endpoint.
 * The "Basico" tab uses useActionState; other tabs manage their own state.
 */
import { useState, useCallback } from 'react';
import { Tabs } from '@/components/ui/Tabs';
import { BasicInfoTab } from '@/components/forms/product-tabs/BasicInfoTab';
import { AllergensTab } from '@/components/forms/product-tabs/AllergensTab';
import { DietaryTab } from '@/components/forms/product-tabs/DietaryTab';
import { CookingMethodsTab } from '@/components/forms/product-tabs/CookingMethodsTab';
import { FlavorTextureTab } from '@/components/forms/product-tabs/FlavorTextureTab';
import { IngredientsTab } from '@/components/forms/product-tabs/IngredientsTab';
import { BadgesSealsTab } from '@/components/forms/product-tabs/BadgesSealsTab';
import { BranchPricingTab } from '@/components/forms/product-tabs/BranchPricingTab';
import type { Product, ProductCreate, ProductUpdate } from '@/types/product';
import type { Category } from '@/types/category';
import type { Subcategory } from '@/types/subcategory';

interface Props {
  product: Product | null;
  categories: Category[];
  subcategories: Subcategory[];
  onSuccess: () => void;
  onCancel: () => void;
  createFn: (data: ProductCreate) => Promise<Product | null>;
  updateFn: (id: number, data: ProductUpdate) => Promise<Product | null>;
}

const TABS = [
  { key: 'basic', label: 'Basico' },
  { key: 'allergens', label: 'Alergenos' },
  { key: 'dietary', label: 'Dieta' },
  { key: 'cooking', label: 'Coccion' },
  { key: 'flavor', label: 'Sabor/Textura' },
  { key: 'ingredients', label: 'Ingredientes' },
  { key: 'badges', label: 'Badges/Sellos' },
  { key: 'pricing', label: 'Precios' },
];

export function ProductFormTabs({
  product,
  categories,
  subcategories,
  onSuccess,
  onCancel,
  createFn,
  updateFn,
}: Props) {
  const isEditing = product !== null;
  const [activeTab, setActiveTab] = useState('basic');
  const [createdProductId, setCreatedProductId] = useState<number | null>(
    product?.id ?? null,
  );

  // After creation, store the ID so other tabs can operate on it
  const handleBasicSuccess = useCallback((savedProduct: Product | null) => {
    if (savedProduct) {
      setCreatedProductId(savedProduct.id);
      if (!isEditing) {
        // Auto-advance to allergens tab after creating
        setActiveTab('allergens');
      }
    }
    if (isEditing) {
      onSuccess();
    }
  }, [isEditing, onSuccess]);

  // Enrichment tabs are only available after the product is saved
  const canShowEnrichmentTabs = createdProductId !== null;

  // For new products, only show basic tab until saved
  const availableTabs = canShowEnrichmentTabs
    ? TABS
    : TABS.filter((t) => t.key === 'basic');

  return (
    <div className="space-y-4">
      <Tabs tabs={availableTabs} activeTab={activeTab} onTabChange={setActiveTab} />

      <div className="min-h-[300px]">
        {activeTab === 'basic' ? (
          <BasicInfoTab
            product={product}
            categories={categories}
            subcategories={subcategories}
            onSuccess={handleBasicSuccess}
            onCancel={onCancel}
            createFn={createFn}
            updateFn={updateFn}
          />
        ) : null}

        {activeTab === 'allergens' && createdProductId ? (
          <AllergensTab productId={createdProductId} />
        ) : null}

        {activeTab === 'dietary' && createdProductId ? (
          <DietaryTab productId={createdProductId} />
        ) : null}

        {activeTab === 'cooking' && createdProductId ? (
          <CookingMethodsTab productId={createdProductId} />
        ) : null}

        {activeTab === 'flavor' && createdProductId ? (
          <FlavorTextureTab productId={createdProductId} />
        ) : null}

        {activeTab === 'ingredients' && createdProductId ? (
          <IngredientsTab productId={createdProductId} />
        ) : null}

        {activeTab === 'badges' && createdProductId ? (
          <BadgesSealsTab productId={createdProductId} />
        ) : null}

        {activeTab === 'pricing' && createdProductId ? (
          <BranchPricingTab productId={createdProductId} />
        ) : null}
      </div>

      {!canShowEnrichmentTabs && activeTab !== 'basic' ? (
        <p className="text-sm text-text-tertiary text-center py-8">
          Guarda el producto primero para configurar esta seccion.
        </p>
      ) : null}
    </div>
  );
}
