import { apiClient } from '@/services/api-client';
import type { Sector, SectorCreate, SectorUpdate } from '@/types/sector';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Branch-scoped sector service. All endpoints require a branchId. */
export const sectorService = {
  list: (
    branchId: number,
    params: PaginationParams,
  ): Promise<PaginatedResponse<Sector>> =>
    apiClient
      .get<PaginatedResponse<Sector>>(
        `/v1/branches/${branchId}/sectors`,
        { params },
      )
      .then((r) => r.data),

  getById: (branchId: number, id: number): Promise<Sector> =>
    apiClient
      .get<ApiResponse<Sector>>(
        `/v1/branches/${branchId}/sectors/${id}`,
      )
      .then((r) => r.data.data),

  create: (branchId: number, data: SectorCreate): Promise<Sector> =>
    apiClient
      .post<ApiResponse<Sector>>(
        `/v1/branches/${branchId}/sectors`,
        data,
      )
      .then((r) => r.data.data),

  update: (
    branchId: number,
    id: number,
    data: SectorUpdate,
  ): Promise<Sector> =>
    apiClient
      .put<ApiResponse<Sector>>(
        `/v1/branches/${branchId}/sectors/${id}`,
        data,
      )
      .then((r) => r.data.data),

  remove: (branchId: number, id: number): Promise<void> =>
    apiClient
      .delete(`/v1/branches/${branchId}/sectors/${id}`)
      .then(() => undefined),
};
