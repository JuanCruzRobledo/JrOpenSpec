import { apiClient } from '@/services/api-client';
import type { Assignment, AssignmentBulkCreate, AssignmentsByShift } from '@/types/assignment';

/** Branch-scoped assignment service. */
export const assignmentService = {
  list: async (
    branchId: number,
    fecha: string,
  ): Promise<Assignment[]> => {
    const r = await apiClient.get<{ data: AssignmentsByShift }>(
      `/v1/branches/${branchId}/assignments/`,
      { params: { fecha } },
    );
    const grouped = r.data.data;
    return [
      ...grouped.morning,
      ...grouped.afternoon,
      ...grouped.night,
    ];
  },

  createBulk: (
    branchId: number,
    data: AssignmentBulkCreate,
  ): Promise<void> =>
    apiClient
      .post(`/v1/branches/${branchId}/assignments/bulk`, data)
      .then(() => undefined),

  remove: (branchId: number, id: number): Promise<void> =>
    apiClient
      .delete(`/v1/branches/${branchId}/assignments/${id}`)
      .then(() => undefined),
};
