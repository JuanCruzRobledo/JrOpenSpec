import { apiClient } from '@/services/api-client';
import type { Staff, StaffCreate, StaffUpdate } from '@/types/staff';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Tenant-scoped staff service. No branchId — staff belongs to tenant. */
export const staffService = {
  list: (params: PaginationParams): Promise<PaginatedResponse<Staff>> =>
    apiClient
      .get<PaginatedResponse<Staff>>('/v1/staff', { params })
      .then((r) => r.data),

  getById: (id: number): Promise<Staff> =>
    apiClient
      .get<ApiResponse<Staff>>(`/v1/staff/${id}`)
      .then((r) => r.data.data),

  create: (data: StaffCreate): Promise<Staff> =>
    apiClient
      .post<ApiResponse<Staff>>('/v1/staff', data)
      .then((r) => r.data.data),

  update: (id: number, data: StaffUpdate): Promise<Staff> =>
    apiClient
      .put<ApiResponse<Staff>>(`/v1/staff/${id}`, data)
      .then((r) => r.data.data),

  remove: (id: number): Promise<void> =>
    apiClient
      .delete(`/v1/staff/${id}`)
      .then(() => undefined),
};
