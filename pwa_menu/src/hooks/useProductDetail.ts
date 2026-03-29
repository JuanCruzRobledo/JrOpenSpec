import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  useProductDetailStore,
  selectProduct,
  selectProductIsLoading,
  selectProductError,
  selectProductIsOpen,
  selectFetchProductAction,
  selectCloseProductAction,
} from '@/stores/product-detail.store';
import { useSessionStore, selectBranchSlug } from '@/stores/session.store';
import type { ProductDetail } from '@/types/product-detail';
import type { ApiError } from '@/types/api';

interface UseProductDetailResult {
  product: ProductDetail | null;
  isLoading: boolean;
  error: ApiError | null;
  isOpen: boolean;
  close: () => void;
}

/**
 * Reads the productId from URL params, triggers a fetch if present,
 * and cleans up the store on unmount.
 *
 * URL param: `productId` — expected to be a numeric string.
 * If absent, the store is not touched.
 */
export function useProductDetail(): UseProductDetailResult {
  const params = useParams<{ productId?: string }>();
  const branchSlug = useSessionStore(selectBranchSlug);

  const product = useProductDetailStore(selectProduct);
  const isLoading = useProductDetailStore(selectProductIsLoading);
  const error = useProductDetailStore(selectProductError);
  const isOpen = useProductDetailStore(selectProductIsOpen);
  const fetchProduct = useProductDetailStore(selectFetchProductAction);
  const closeProduct = useProductDetailStore(selectCloseProductAction);

  useEffect(() => {
    if (!params.productId || !branchSlug) return;

    const id = parseInt(params.productId, 10);
    if (isNaN(id)) return;

    void fetchProduct(branchSlug, id);

    // Cleanup: close and clear the store when the component using this hook unmounts
    return () => {
      closeProduct();
    };
  }, [params.productId, branchSlug, fetchProduct, closeProduct]);

  return {
    product,
    isLoading,
    error,
    isOpen,
    close: closeProduct,
  };
}
