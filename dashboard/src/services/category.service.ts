import { apiClient } from '@/services/api-client';
import type { Category, CategoryCreate, CategoryUpdate } from '@/types/category';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Branch-scoped category service. All endpoints require a branchId. */
export const categoryService = {
  list: (
    branchId: number,
    params: PaginationParams,
  ): Promise<PaginatedResponse<Category>> =>
    apiClient
      .get<PaginatedResponse<Category>>(
        `/v1/branches/${branchId}/categories`,
        { params },
      )
      .then((r) => r.data),

  getById: (branchId: number, id: number): Promise<Category> =>
    apiClient
      .get<ApiResponse<Category>>(
        `/v1/branches/${branchId}/categories/${id}`,
      )
      .then((r) => r.data.data),

  create: (branchId: number, data: CategoryCreate): Promise<Category> =>
    apiClient
      .post<ApiResponse<Category>>(
        `/v1/branches/${branchId}/categories`,
        data,
      )
      .then((r) => r.data.data),

  update: (
    branchId: number,
    id: number,
    data: CategoryUpdate,
  ): Promise<Category> =>
    apiClient
      .put<ApiResponse<Category>>(
        `/v1/branches/${branchId}/categories/${id}`,
        data,
      )
      .then((r) => r.data.data),

  remove: (branchId: number, id: number): Promise<void> =>
    apiClient
      .delete(`/v1/branches/${branchId}/categories/${id}`)
      .then(() => undefined),
};
