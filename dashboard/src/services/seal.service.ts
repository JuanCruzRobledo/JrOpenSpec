import { apiClient } from '@/services/api-client';
import type { Seal, SealCreate, SealUpdate } from '@/types/seal';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Seal service — tenant-scoped CRUD. */
export const sealService = {
  list: (params: PaginationParams): Promise<PaginatedResponse<Seal>> =>
    apiClient
      .get<PaginatedResponse<Seal>>('/dashboard/seals', { params })
      .then((r) => r.data),

  getById: (id: number): Promise<Seal> =>
    apiClient
      .get<ApiResponse<Seal>>(`/dashboard/seals/${id}`)
      .then((r) => r.data.data),

  create: (data: SealCreate): Promise<Seal> =>
    apiClient
      .post<ApiResponse<Seal>>('/dashboard/seals', data)
      .then((r) => r.data.data),

  update: (id: number, data: SealUpdate): Promise<Seal> =>
    apiClient
      .put<ApiResponse<Seal>>(`/dashboard/seals/${id}`, data)
      .then((r) => r.data.data),

  remove: (id: number): Promise<void> =>
    apiClient.delete(`/dashboard/seals/${id}`).then(() => undefined),
};
