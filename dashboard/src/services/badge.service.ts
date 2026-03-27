import { apiClient } from '@/services/api-client';
import type { Badge, BadgeCreate, BadgeUpdate } from '@/types/badge';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Badge service — tenant-scoped CRUD. */
export const badgeService = {
  list: (params: PaginationParams): Promise<PaginatedResponse<Badge>> =>
    apiClient
      .get<PaginatedResponse<Badge>>('/dashboard/badges', { params })
      .then((r) => r.data),

  getById: (id: number): Promise<Badge> =>
    apiClient
      .get<ApiResponse<Badge>>(`/dashboard/badges/${id}`)
      .then((r) => r.data.data),

  create: (data: BadgeCreate): Promise<Badge> =>
    apiClient
      .post<ApiResponse<Badge>>('/dashboard/badges', data)
      .then((r) => r.data.data),

  update: (id: number, data: BadgeUpdate): Promise<Badge> =>
    apiClient
      .put<ApiResponse<Badge>>(`/dashboard/badges/${id}`, data)
      .then((r) => r.data.data),

  remove: (id: number): Promise<void> =>
    apiClient.delete(`/dashboard/badges/${id}`).then(() => undefined),
};
