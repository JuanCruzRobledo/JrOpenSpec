import { apiClient } from '@/services/api-client';
import type { RolesMatrix } from '@/types/role';

/** Role permissions service — read-only. */
export const roleService = {
  getPermissions: (): Promise<RolesMatrix> =>
    apiClient
      .get<RolesMatrix>('/v1/roles/permissions')
      .then((r) => r.data),
};
