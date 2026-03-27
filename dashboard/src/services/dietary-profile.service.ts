import { apiClient } from '@/services/api-client';
import type { DietaryProfile, DietaryProfileCreate, DietaryProfileUpdate } from '@/types/dietary-profile';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Dietary profile service — tenant-scoped CRUD. */
export const dietaryProfileService = {
  list: (params: PaginationParams): Promise<PaginatedResponse<DietaryProfile>> =>
    apiClient
      .get<PaginatedResponse<DietaryProfile>>('/dashboard/dietary-profiles', { params })
      .then((r) => r.data),

  getById: (id: number): Promise<DietaryProfile> =>
    apiClient
      .get<ApiResponse<DietaryProfile>>(`/dashboard/dietary-profiles/${id}`)
      .then((r) => r.data.data),

  create: (data: DietaryProfileCreate): Promise<DietaryProfile> =>
    apiClient
      .post<ApiResponse<DietaryProfile>>('/dashboard/dietary-profiles', data)
      .then((r) => r.data.data),

  update: (id: number, data: DietaryProfileUpdate): Promise<DietaryProfile> =>
    apiClient
      .put<ApiResponse<DietaryProfile>>(`/dashboard/dietary-profiles/${id}`, data)
      .then((r) => r.data.data),

  remove: (id: number): Promise<void> =>
    apiClient.delete(`/dashboard/dietary-profiles/${id}`).then(() => undefined),
};
