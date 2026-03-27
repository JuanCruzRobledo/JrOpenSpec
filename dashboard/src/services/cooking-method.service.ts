import { apiClient } from '@/services/api-client';
import type { CookingMethod, CookingMethodCreate, CookingMethodUpdate } from '@/types/cooking-method';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Cooking method service — tenant-scoped CRUD. */
export const cookingMethodService = {
  list: (params: PaginationParams): Promise<PaginatedResponse<CookingMethod>> =>
    apiClient
      .get<PaginatedResponse<CookingMethod>>('/dashboard/cooking-methods', { params })
      .then((r) => r.data),

  getById: (id: number): Promise<CookingMethod> =>
    apiClient
      .get<ApiResponse<CookingMethod>>(`/dashboard/cooking-methods/${id}`)
      .then((r) => r.data.data),

  create: (data: CookingMethodCreate): Promise<CookingMethod> =>
    apiClient
      .post<ApiResponse<CookingMethod>>('/dashboard/cooking-methods', data)
      .then((r) => r.data.data),

  update: (id: number, data: CookingMethodUpdate): Promise<CookingMethod> =>
    apiClient
      .put<ApiResponse<CookingMethod>>(`/dashboard/cooking-methods/${id}`, data)
      .then((r) => r.data.data),

  remove: (id: number): Promise<void> =>
    apiClient.delete(`/dashboard/cooking-methods/${id}`).then(() => undefined),
};
