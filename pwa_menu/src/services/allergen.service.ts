import { apiClient } from './api-client';
import type { AllergenCatalogItem } from '@/types/allergen-catalog';
import type { ApiEnvelope } from '@/types/api';

/**
 * Fetches the full allergen catalog for a tenant.
 *
 * GET /api/public/allergens?tenant={slug}
 *
 * Used to build the bidirectional cross-reaction map in the allergen catalog store.
 * Fetched once per session with a 5-minute TTL.
 *
 * @param tenantSlug - Tenant slug (e.g. "buen-sabor")
 */
export async function getAllergenCatalog(
  tenantSlug: string
): Promise<AllergenCatalogItem[]> {
  const response = await apiClient.get<ApiEnvelope<AllergenCatalogItem[]>>(
    '/api/public/allergens',
    { params: { tenant: tenantSlug } }
  );
  return response.data.data;
}
