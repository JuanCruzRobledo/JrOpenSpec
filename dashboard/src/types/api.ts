// Generic API response types matching the real backend envelope

/** Single-item response wrapper */
export interface ApiResponse<T> {
  data: T;
}

/** Pagination metadata from the backend */
export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

/**
 * Paginated list response.
 * Backend returns: { data: T[], meta: { page, limit, total } }
 */
export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

/** Standard error response body from the backend */
export interface ApiError {
  detail: string;
  code?: string;
}

/** Pagination params sent to the backend */
export interface PaginationParams {
  page: number;
  limit: number;
}
