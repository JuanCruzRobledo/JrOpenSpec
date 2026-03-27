import { apiClient } from '@/services/api-client';
import type { Product, ProductCreate, ProductUpdate } from '@/types/product';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Branch-scoped product service. All endpoints require a branchId. */
export const productService = {
  list: (
    branchId: number,
    params: PaginationParams,
  ): Promise<PaginatedResponse<Product>> =>
    apiClient
      .get<PaginatedResponse<Product>>(
        `/v1/branches/${branchId}/products`,
        { params },
      )
      .then((r) => r.data),

  getById: (branchId: number, id: number): Promise<Product> =>
    apiClient
      .get<ApiResponse<Product>>(
        `/v1/branches/${branchId}/products/${id}`,
      )
      .then((r) => r.data.data),

  create: (branchId: number, data: ProductCreate): Promise<Product> =>
    apiClient
      .post<ApiResponse<Product>>(
        `/v1/branches/${branchId}/products`,
        data,
      )
      .then((r) => r.data.data),

  update: (
    branchId: number,
    id: number,
    data: ProductUpdate,
  ): Promise<Product> =>
    apiClient
      .put<ApiResponse<Product>>(
        `/v1/branches/${branchId}/products/${id}`,
        data,
      )
      .then((r) => r.data.data),

  remove: (branchId: number, id: number): Promise<void> =>
    apiClient
      .delete(`/v1/branches/${branchId}/products/${id}`)
      .then(() => undefined),
};
