import { apiClient } from '@/services/api-client';
import type { ApiResponse } from '@/types/api';
import type {
  BatchPriceRequest,
  BatchPricePreview,
  BatchPriceApplyResponse,
} from '@/types/product-extended';

/** Batch price update service — preview + apply. */
export const batchPriceService = {
  preview: (data: BatchPriceRequest): Promise<BatchPricePreview> =>
    apiClient
      .post<ApiResponse<BatchPricePreview>>('/dashboard/products/batch-price/preview', data)
      .then((r) => r.data.data),

  apply: (data: BatchPriceRequest): Promise<BatchPriceApplyResponse> =>
    apiClient
      .post<ApiResponse<BatchPriceApplyResponse>>('/dashboard/products/batch-price/apply', {
        ...data,
        confirmado: true,
      })
      .then((r) => r.data.data),
};
