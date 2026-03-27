import { apiClient } from '@/services/api-client';
import type { Branch, BranchCreate, BranchUpdate } from '@/types/branch';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

export const branchService = {
  list: (params: PaginationParams): Promise<PaginatedResponse<Branch>> =>
    apiClient
      .get<PaginatedResponse<Branch>>('/v1/branches', { params })
      .then((r) => r.data),

  getById: (id: number): Promise<Branch> =>
    apiClient
      .get<ApiResponse<Branch>>(`/v1/branches/${id}`)
      .then((r) => r.data.data),

  create: (data: BranchCreate): Promise<Branch> =>
    apiClient
      .post<ApiResponse<Branch>>('/v1/branches', data)
      .then((r) => r.data.data),

  update: (id: number, data: BranchUpdate): Promise<Branch> =>
    apiClient
      .put<ApiResponse<Branch>>(`/v1/branches/${id}`, data)
      .then((r) => r.data.data),

  remove: (id: number): Promise<void> =>
    apiClient
      .delete(`/v1/branches/${id}`)
      .then(() => undefined),
};
