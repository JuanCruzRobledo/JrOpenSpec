import { apiClient } from './api-client';
import type { AllergenCatalogItem } from '@/types/allergen-catalog';

/**
 * Fetches the full allergen catalog for a tenant.
 *
 * GET /api/public/allergens?tenant={slug}
 *
 * Used to build the bidirectional cross-reaction map in the allergen catalog store.
 * Fetched once per session with a 5-minute TTL.
 *
 * NOTE: This endpoint returns { allergens: AllergenCatalogItem[], generatedAt: string }
 * directly (no ApiEnvelope wrapper).
 *
 * @param tenantSlug - Tenant slug (e.g. "buen-sabor")
 */
export async function getAllergenCatalog(
  tenantSlug: string
): Promise<AllergenCatalogItem[]> {
  const response = await apiClient.get<{ allergens: AllergenCatalogItem[] }>(
    '/api/public/allergens',
    { params: { tenant: tenantSlug } }
  );
  return response.data.allergens;
}
