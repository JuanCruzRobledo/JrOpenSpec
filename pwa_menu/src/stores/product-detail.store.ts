import { create } from 'zustand';
import type { ProductDetail } from '@/types/product-detail';
import type { ApiError } from '@/types/api';
import { getProductDetail } from '@/services/menu.service';

// ---------------------------------------------------------------------------
// State & Actions interface
// NOT persisted — modal state is ephemeral
// ---------------------------------------------------------------------------

interface ProductDetailStoreState {
  product: ProductDetail | null;
  isLoading: boolean;
  error: ApiError | null;
  isOpen: boolean;

  // Actions
  fetchProduct: (branchSlug: string, productId: number) => Promise<void>;
  close: () => void;
}

// ---------------------------------------------------------------------------
// Store creation — NOT persisted
// ---------------------------------------------------------------------------

const useProductDetailStore = create<ProductDetailStoreState>()((set) => ({
  product: null,
  isLoading: false,
  error: null,
  isOpen: false,

  async fetchProduct(branchSlug, productId) {
    set({ isLoading: true, error: null, isOpen: true });
    try {
      const product = await getProductDetail(branchSlug, productId);
      set({ product, isLoading: false });
    } catch (err) {
      const apiError: ApiError = {
        status: 0,
        code: 'FETCH_ERROR',
        message: err instanceof Error ? err.message : 'Unknown error',
      };
      set({ isLoading: false, error: apiError });
    }
  },

  close() {
    set({ isOpen: false, product: null, error: null });
  },
}));

// ---------------------------------------------------------------------------
// Individual selectors
// ---------------------------------------------------------------------------

export const selectProduct = (s: ProductDetailStoreState) => s.product;
export const selectProductIsLoading = (s: ProductDetailStoreState) => s.isLoading;
export const selectProductError = (s: ProductDetailStoreState) => s.error;
export const selectProductIsOpen = (s: ProductDetailStoreState) => s.isOpen;

// Action selectors
export const selectFetchProductAction = (s: ProductDetailStoreState) => s.fetchProduct;
export const selectCloseProductAction = (s: ProductDetailStoreState) => s.close;

export { useProductDetailStore };
