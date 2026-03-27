import { useState, useMemo } from 'react';
import { PAGE_SIZE } from '@/config/constants';

interface UsePaginationOptions {
  pageSize?: number;
}

interface UsePaginationReturn {
  page: number;
  limit: number;
  totalPages: number;
  setPage: (page: number) => void;
  setTotal: (total: number) => void;
}

/**
 * Manages page-based pagination state.
 * Backend expects { page, limit } params (1-indexed pages).
 */
export function usePagination(options?: UsePaginationOptions): UsePaginationReturn {
  const limit = options?.pageSize ?? PAGE_SIZE;
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / limit)), [total, limit]);

  return { page, limit, totalPages, setPage, setTotal };
}
