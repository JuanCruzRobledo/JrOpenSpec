import { apiClient } from '@/services/api-client';
import type { ApiResponse } from '@/types/api';
import type { Product } from '@/types/product';
import type {
  ProductAllergenData,
  ProductIngredientData,
  BadgeAssignData,
  SealAssignData,
  FlavorProfile,
  TextureProfile,
} from '@/types/product-extended';

/** Product enrichment service — set associations on a product. */
export const productExtendedService = {
  setAllergens: (productId: number, data: ProductAllergenData[]): Promise<Product> =>
    apiClient
      .put<ApiResponse<Product>>(`/dashboard/products/${productId}/allergens`, data)
      .then((r) => r.data.data),

  setDietaryProfiles: (productId: number, profileIds: number[]): Promise<Product> =>
    apiClient
      .put<ApiResponse<Product>>(`/dashboard/products/${productId}/dietary-profiles`, {
        perfil_ids: profileIds,
      })
      .then((r) => r.data.data),

  setCookingMethods: (productId: number, methodIds: number[]): Promise<Product> =>
    apiClient
      .put<ApiResponse<Product>>(`/dashboard/products/${productId}/cooking-methods`, {
        metodo_ids: methodIds,
      })
      .then((r) => r.data.data),

  setFlavorProfiles: (productId: number, profiles: FlavorProfile[]): Promise<Product> =>
    apiClient
      .put<ApiResponse<Product>>(`/dashboard/products/${productId}/flavor-profiles`, {
        perfiles: profiles,
      })
      .then((r) => r.data.data),

  setTextureProfiles: (productId: number, profiles: TextureProfile[]): Promise<Product> =>
    apiClient
      .put<ApiResponse<Product>>(`/dashboard/products/${productId}/texture-profiles`, {
        perfiles: profiles,
      })
      .then((r) => r.data.data),

  setIngredients: (productId: number, data: ProductIngredientData[]): Promise<Product> =>
    apiClient
      .put<ApiResponse<Product>>(`/dashboard/products/${productId}/ingredients`, data)
      .then((r) => r.data.data),

  setBadges: (productId: number, data: BadgeAssignData[]): Promise<Product> =>
    apiClient
      .put<ApiResponse<Product>>(`/dashboard/products/${productId}/badges`, data)
      .then((r) => r.data.data),

  setSeals: (productId: number, data: SealAssignData[]): Promise<Product> =>
    apiClient
      .put<ApiResponse<Product>>(`/dashboard/products/${productId}/seals`, data)
      .then((r) => r.data.data),
};
