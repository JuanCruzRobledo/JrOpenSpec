import { apiClient } from '@/services/api-client';
import type { Allergen, AllergenCreate, AllergenUpdate, CrossReaction, CrossReactionCreate } from '@/types/allergen';
import type { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api';

/** Allergen service — tenant-scoped CRUD + cross-reactions. */
export const allergenService = {
  list: (params: PaginationParams): Promise<PaginatedResponse<Allergen>> =>
    apiClient
      .get<PaginatedResponse<Allergen>>('/dashboard/allergens', { params })
      .then((r) => r.data),

  getById: (id: number): Promise<Allergen> =>
    apiClient
      .get<ApiResponse<Allergen>>(`/dashboard/allergens/${id}`)
      .then((r) => r.data.data),

  create: (data: AllergenCreate): Promise<Allergen> =>
    apiClient
      .post<ApiResponse<Allergen>>('/dashboard/allergens', data)
      .then((r) => r.data.data),

  update: (id: number, data: AllergenUpdate): Promise<Allergen> =>
    apiClient
      .put<ApiResponse<Allergen>>(`/dashboard/allergens/${id}`, data)
      .then((r) => r.data.data),

  remove: (id: number): Promise<void> =>
    apiClient.delete(`/dashboard/allergens/${id}`).then(() => undefined),

  // Cross-reactions
  getCrossReactions: (allergenId: number): Promise<CrossReaction[]> =>
    apiClient
      .get<ApiResponse<CrossReaction[]>>(`/dashboard/allergens/${allergenId}/cross-reactions`)
      .then((r) => r.data.data),

  addCrossReaction: (allergenId: number, data: CrossReactionCreate): Promise<CrossReaction> =>
    apiClient
      .post<ApiResponse<CrossReaction>>(`/dashboard/allergens/${allergenId}/cross-reactions`, data)
      .then((r) => r.data.data),

  removeCrossReaction: (crossReactionId: number): Promise<void> =>
    apiClient
      .delete(`/dashboard/allergens/cross-reactions/${crossReactionId}`)
      .then(() => undefined),
};
