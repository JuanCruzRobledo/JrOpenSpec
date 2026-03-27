import { apiClient } from '@/services/api-client';
import type { Restaurant, RestaurantUpdate } from '@/types/restaurant';
import type { ApiResponse } from '@/types/api';

export const restaurantService = {
  getMe: (): Promise<Restaurant> =>
    apiClient
      .get<ApiResponse<Restaurant>>('/v1/restaurants/me')
      .then((r) => r.data.data),

  update: (id: number, data: RestaurantUpdate): Promise<Restaurant> =>
    apiClient
      .put<ApiResponse<Restaurant>>(`/v1/restaurants/${id}`, data)
      .then((r) => r.data.data),
};
