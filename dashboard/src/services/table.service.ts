import { apiClient } from '@/services/api-client';
import type {
  Table,
  TableCreate,
  TableBatchCreate,
  TableUpdate,
  TableStatusUpdate,
} from '@/types/table';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Branch-scoped table service. All endpoints require a branchId. */
export const tableService = {
  list: (
    branchId: number,
    params: PaginationParams,
  ): Promise<PaginatedResponse<Table>> =>
    apiClient
      .get<PaginatedResponse<Table>>(
        `/v1/branches/${branchId}/tables`,
        { params },
      )
      .then((r) => r.data),

  getById: (branchId: number, id: number): Promise<Table> =>
    apiClient
      .get<ApiResponse<Table>>(
        `/v1/branches/${branchId}/tables/${id}`,
      )
      .then((r) => r.data.data),

  create: (branchId: number, data: TableCreate): Promise<Table> =>
    apiClient
      .post<ApiResponse<Table>>(
        `/v1/branches/${branchId}/tables`,
        data,
      )
      .then((r) => r.data.data),

  createBatch: (
    branchId: number,
    data: TableBatchCreate,
  ): Promise<Table[]> =>
    apiClient
      .post<ApiResponse<Table[]>>(
        `/v1/branches/${branchId}/tables/batch`,
        data,
      )
      .then((r) => r.data.data),

  update: (
    branchId: number,
    id: number,
    data: TableUpdate,
  ): Promise<Table> =>
    apiClient
      .put<ApiResponse<Table>>(
        `/v1/branches/${branchId}/tables/${id}`,
        data,
      )
      .then((r) => r.data.data),

  updateStatus: (
    branchId: number,
    id: number,
    data: TableStatusUpdate,
  ): Promise<Table> =>
    apiClient
      .patch<ApiResponse<Table>>(
        `/v1/branches/${branchId}/tables/${id}/status`,
        data,
      )
      .then((r) => r.data.data),

  remove: (branchId: number, id: number): Promise<void> =>
    apiClient
      .delete(`/v1/branches/${branchId}/tables/${id}`)
      .then(() => undefined),
};
