import { apiClient } from './api-client';
import type { MenuResponse } from '@/types/menu';
import type { ProductDetail } from '@/types/product-detail';
import type { ApiEnvelope } from '@/types/api';

/**
 * Fetches the full public menu for a branch.
 *
 * GET /api/public/menu/{slug}
 *
 * Response is cached by the menu store with stale-while-revalidate pattern.
 * The Workbox NetworkFirst strategy (5s timeout) also caches this at the SW level.
 *
 * @param slug - Branch slug (e.g. "buen-sabor-centro")
 */
export async function getMenu(slug: string): Promise<MenuResponse> {
  const response = await apiClient.get<ApiEnvelope<MenuResponse>>(
    `/api/public/menu/${encodeURIComponent(slug)}`
  );
  return response.data.data;
}

/**
 * Fetches the full detail for a single product.
 *
 * GET /api/public/menu/{slug}/product/{id}
 *
 * Called when a product card is tapped to open the detail modal.
 * Product IDs are BigInteger on the backend; passed as number here.
 *
 * @param slug      - Branch slug
 * @param productId - Product ID (BigInteger from backend)
 */
export async function getProductDetail(
  slug: string,
  productId: number
): Promise<ProductDetail> {
  const response = await apiClient.get<ApiEnvelope<ProductDetail>>(
    `/api/public/menu/${encodeURIComponent(slug)}/product/${productId}`
  );
  return response.data.data;
}
