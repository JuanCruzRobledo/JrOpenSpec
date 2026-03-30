import { useRef, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import {
  useSessionStore,
  selectBranchSlug,
} from '@/stores/session.store';
import {
  useAllergenCatalogStore,
  selectFetchCatalogAction,
} from '@/stores/allergen-catalog.store';
import {
  useUiStore,
  selectFilterDrawerOpen,
  selectCloseFilterDrawerAction,
  selectAddToastAction,
} from '@/stores/ui.store';
import {
  useProductDetailStore,
  selectProduct,
  selectProductIsOpen,
  selectFetchProductAction,
  selectCloseProductAction,
} from '@/stores/product-detail.store';
import { useMenuData } from '@/hooks/useMenuData';
import { useFilteredProducts } from '@/hooks/useFilteredProducts';
import { useCategoryScroll } from '@/hooks/useCategoryScroll';
import { MenuHeader } from '@/components/layout/MenuHeader';
import { CategoryTabs } from '@/components/menu/CategoryTabs';
import { CategorySection } from '@/components/menu/CategorySection';
import { SearchBar } from '@/components/menu/SearchBar';
import { EmptyState } from '@/components/menu/EmptyState';
import { MenuSkeleton } from '@/components/menu/MenuSkeleton';
import { CrossReactionFilterFeedback } from '@/components/menu/CrossReactionFilterFeedback';
import { FilterDrawer } from '@/components/filters/FilterDrawer';
import { ProductDetailModal } from '@/components/product-detail/ProductDetailModal';
import type { MenuProduct } from '@/types/menu';
import { humanizeSlug } from '@/lib/text';
import i18n from '@/i18n';
import { useCrossReactionFeedback } from '@/hooks/useCrossReactionFeedback';

/**
 * Main menu page container.
 *
 * Data flow:
 * 1. Reads branchSlug from session store
 * 2. useMenuData handles stale-while-revalidate fetch
 * 3. useFilteredProducts applies filter engine to categories
 * 4. useCategoryScroll syncs active tab with visible section
 * 5. Allergen catalog is prefetched on mount for filter panel
 *
 * Layout (top → bottom):
 * MenuHeader → CategoryTabs → SearchBar → CategorySections / EmptyState
 *
 * Bottom padding (pb-24) accounts for the BottomBar overlay.
 */
export default function MenuPage() {
  const { t } = useTranslation('menu');
  const navigate = useNavigate();
  const params = useParams<{ tenant: string; branch: string; productId?: string }>();

  const branchSlug = useSessionStore(selectBranchSlug);
  const fetchCatalog = useAllergenCatalogStore(selectFetchCatalogAction);
  const filterDrawerOpen = useUiStore(selectFilterDrawerOpen);
  const closeFilterDrawer = useUiStore(selectCloseFilterDrawerAction);
  const addToast = useUiStore(selectAddToastAction);
  const productIsOpen = useProductDetailStore(selectProductIsOpen);
  const product = useProductDetailStore(selectProduct);
  const fetchProduct = useProductDetailStore(selectFetchProductAction);
  const closeProduct = useProductDetailStore(selectCloseProductAction);

  const { data, isLoading, isBackgroundRefreshing, error } = useMenuData(branchSlug ?? undefined);

  const filteredCategories = useFilteredProducts(data?.categories);
  const crossReactionFeedback = useCrossReactionFeedback(data?.categories);

  // Section refs for IntersectionObserver category scroll sync
  const sectionRefsMap = useRef(new Map<string, HTMLElement>());
  // Stable ref callbacks per category id — avoids re-registering observer on each render
  const refCallbacksCache = useRef(new Map<string, (el: HTMLElement | null) => void>());
  const { activeCategory, scrollToCategory } = useCategoryScroll(sectionRefsMap.current);

  // Returns a stable callback ref for a given category id
  const getSectionRef = useCallback((id: string) => {
    const cached = refCallbacksCache.current.get(id);
    if (cached) return cached;
    const cb = (el: HTMLElement | null) => {
      if (el) {
        sectionRefsMap.current.set(id, el);
      } else {
        sectionRefsMap.current.delete(id);
      }
    };
    refCallbacksCache.current.set(id, cb);
    return cb;
  }, []);

  // Prefetch allergen catalog on mount — needed for filter panel
  useEffect(() => {
    if (branchSlug) {
      // tenantSlug is extracted from branchSlug prefix or params
      const tenantSlug = params.tenant ?? branchSlug.split('/')[0] ?? branchSlug;
      void fetchCatalog(tenantSlug);
    }
  }, [branchSlug, params.tenant, fetchCatalog]);

  // Open product detail if URL contains productId
  useEffect(() => {
    if (params.productId && branchSlug) {
      const id = parseInt(params.productId, 10);
      if (!isNaN(id)) {
        void fetchProduct(branchSlug, id);
      }
    }
  }, [params.productId, branchSlug, fetchProduct]);

  // Show error toast when menu fails to load
  useEffect(() => {
    if (error) {
      addToast(t('error'), 'error');
    }
  }, [error, addToast, t]);

  useEffect(() => {
    const appName = i18n.t('app.name', { ns: 'common' });
    const branchName = data?.branch.name ?? (params.branch ? humanizeSlug(params.branch) : appName);
    document.title = product?.name ? `${product.name} | ${branchName}` : `${branchName} | ${appName}`;

    const description = document.querySelector('meta[name="description"]');
    if (description) {
      description.setAttribute('content', t('meta.description', { branchName }));
    }
  }, [data?.branch.name, params.branch, product?.name]);

  const handleProductClick = useCallback(
    (product: MenuProduct) => {
      if (params.tenant && params.branch) {
        navigate(`/${params.tenant}/${params.branch}/product/${product.id}`);
      } else {
        void fetchProduct(branchSlug ?? '', parseInt(product.id, 10));
      }
    },
    [navigate, params.tenant, params.branch, branchSlug, fetchProduct]
  );

  const handleProductModalClose = useCallback(() => {
    closeProduct();
    if (params.productId) {
      navigate(-1);
    }
  }, [closeProduct, navigate, params.productId]);

  const handleCategorySelect = useCallback(
    (id: string) => {
      scrollToCategory(id);
    },
    [scrollToCategory]
  );

  // Determine the active category tab — use scroll-synced value or first category
  const activeCategoryId =
    activeCategory ?? filteredCategories[0]?.id ?? data?.categories[0]?.id ?? '';

  return (
    <>
      <MenuHeader />

      {/* Stale data banner — Hard Stop Rule #1: always show indicator */}
      {isBackgroundRefreshing && (
        <div
          role="status"
          aria-live="polite"
          className="bg-warning/10 border-b border-warning/30 px-4 py-2 text-center text-xs text-warning"
        >
          {t('stale')}
        </div>
      )}

      {/* Category navigation tabs */}
      {!isLoading && filteredCategories.length > 0 && (
        <CategoryTabs
          categories={filteredCategories}
          activeId={activeCategoryId}
          onSelect={handleCategorySelect}
        />
      )}

      {/* Search bar */}
      <SearchBar />

      {/* Main content area */}
      <main className="flex-1 px-4 pb-24">
        {crossReactionFeedback && (
          <div className="mb-4">
            <CrossReactionFilterFeedback summary={crossReactionFeedback} />
          </div>
        )}

        {isLoading ? (
          <MenuSkeleton />
        ) : filteredCategories.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="flex flex-col gap-10">
            {filteredCategories.map((category) => (
              <CategorySection
                key={category.id}
                ref={getSectionRef(category.id)}
                category={category}
                onProductClick={handleProductClick}
              />
            ))}
          </div>
        )}
      </main>

      {/* Filter drawer overlay */}
      <FilterDrawer
        isOpen={filterDrawerOpen}
        onClose={closeFilterDrawer}
        categories={data?.categories ?? []}
      />

      {/* Product detail modal */}
      {productIsOpen && (
        <ProductDetailModal onClose={handleProductModalClose} />
      )}
    </>
  );
}
