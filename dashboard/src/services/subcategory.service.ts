import { apiClient } from '@/services/api-client';
import type { Subcategory, SubcategoryCreate, SubcategoryUpdate } from '@/types/subcategory';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Optional filter for subcategory listing */
interface SubcategoryListParams extends PaginationParams {
  category_id?: number;
}

/** Branch-scoped subcategory service. All endpoints require a branchId. */
export const subcategoryService = {
  list: (
    branchId: number,
    params: SubcategoryListParams,
  ): Promise<PaginatedResponse<Subcategory>> =>
    apiClient
      .get<PaginatedResponse<Subcategory>>(
        `/v1/branches/${branchId}/subcategories`,
        { params },
      )
      .then((r) => r.data),

  getById: (branchId: number, id: number): Promise<Subcategory> =>
    apiClient
      .get<ApiResponse<Subcategory>>(
        `/v1/branches/${branchId}/subcategories/${id}`,
      )
      .then((r) => r.data.data),

  create: (branchId: number, data: SubcategoryCreate): Promise<Subcategory> =>
    apiClient
      .post<ApiResponse<Subcategory>>(
        `/v1/branches/${branchId}/subcategories`,
        data,
      )
      .then((r) => r.data.data),

  update: (
    branchId: number,
    id: number,
    data: SubcategoryUpdate,
  ): Promise<Subcategory> =>
    apiClient
      .put<ApiResponse<Subcategory>>(
        `/v1/branches/${branchId}/subcategories/${id}`,
        data,
      )
      .then((r) => r.data.data),

  remove: (branchId: number, id: number): Promise<void> =>
    apiClient
      .delete(`/v1/branches/${branchId}/subcategories/${id}`)
      .then(() => undefined),
};
