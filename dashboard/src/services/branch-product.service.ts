import { apiClient } from '@/services/api-client';
import type { ApiResponse } from '@/types/api';
import type { BranchProduct, BranchProductInput } from '@/types/product-extended';

/** Branch product service — pricing and availability per branch. */
export const branchProductService = {
  listByProduct: (productId: number): Promise<BranchProduct[]> =>
    apiClient
      .get<ApiResponse<BranchProduct[]>>(`/dashboard/products/${productId}/branches`)
      .then((r) => r.data.data),

  bulkUpdate: (productId: number, data: BranchProductInput[]): Promise<BranchProduct[]> =>
    apiClient
      .put<ApiResponse<BranchProduct[]>>(`/dashboard/products/${productId}/branches`, data)
      .then((r) => r.data.data),

  toggleAvailability: (
    productId: number,
    branchId: number,
  ): Promise<BranchProduct> =>
    apiClient
      .patch<ApiResponse<BranchProduct>>(
        `/dashboard/products/${productId}/branches/${branchId}/toggle`,
      )
      .then((r) => r.data.data),

  updatePrice: (
    productId: number,
    branchId: number,
    precioCentavos: number | null,
  ): Promise<BranchProduct> =>
    apiClient
      .patch<ApiResponse<BranchProduct>>(
        `/dashboard/products/${productId}/branches/${branchId}/price`,
        { precio_centavos: precioCentavos },
      )
      .then((r) => r.data.data),
};
