/**
 * Generic API envelope types.
 * The backend wraps all responses in a standard envelope.
 */

/** Standard API error shape from the backend */
export interface ApiError {
  readonly status: number;
  readonly code: string;
  readonly message: string;
  /** Field-level validation errors, keyed by field name */
  readonly errors?: Record<string, string[]>;
}

/**
 * Standard API response envelope.
 * All successful responses are wrapped in this shape.
 */
export interface ApiEnvelope<T> {
  readonly data: T;
  readonly meta?: ApiMeta;
}

/** Pagination metadata present in list responses */
export interface ApiMeta {
  readonly total: number;
  readonly page: number;
  readonly pageSize: number;
  readonly totalPages: number;
}

/** Utility type for async operation state */
export interface AsyncState<T> {
  data: T | null;
  isLoading: boolean;
  error: ApiError | null;
}
