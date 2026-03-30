import { useState, useEffect, useCallback, useRef } from 'react';
import { usePagination } from '@/hooks/usePagination';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { PaginatedResponse, PaginationParams } from '@/types/api';

interface UseCrudOptions<T, TCreate, TUpdate> {
  /** Fetch function — receives pagination params (and branchId is already bound by the caller) */
  fetchFn: (params: PaginationParams) => Promise<PaginatedResponse<T>>;
  createFn: (data: TCreate) => Promise<T>;
  updateFn: (id: string, data: TUpdate) => Promise<T>;
  deleteFn: (id: string) => Promise<void>;
  entityName: string;
  pageSize?: number;
}

interface UseCrudReturn<T, TCreate, TUpdate> {
  items: T[];
  isLoading: boolean;
  error: string | null;
  page: number;
  totalPages: number;
  setPage: (page: number) => void;
  refresh: () => Promise<void>;
  create: (data: TCreate) => Promise<T | null>;
  update: (id: string, data: TUpdate) => Promise<T | null>;
  remove: (id: string) => Promise<boolean>;
}

/**
 * Generic CRUD hook — handles list fetching, pagination, and CRUD operations
 * with toast notifications.
 *
 * The backend returns { data: T[], meta: { page, limit, total } }.
 * For branch-scoped entities, bind the branchId in the caller before passing fetchFn.
 */
export function useCrud<T, TCreate, TUpdate>(
  options: UseCrudOptions<T, TCreate, TUpdate>,
): UseCrudReturn<T, TCreate, TUpdate> {
  const { fetchFn, createFn, updateFn, deleteFn, entityName, pageSize } = options;
  const { page, limit, totalPages, setPage, setTotal } = usePagination({ pageSize });
  const toast = useToast();

  const [items, setItems] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Stable ref so refresh doesn't re-create on every render when fetchFn identity changes
  const fetchFnRef = useRef(fetchFn);
  fetchFnRef.current = fetchFn;

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchFnRef.current({ page, limit });
      setItems(res.data);
      setTotal(res.meta.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar datos';
      setError(message);
      logger.error(`Failed to fetch ${entityName}`, err);
    } finally {
      setIsLoading(false);
    }
  }, [page, limit, entityName, setTotal]);

  // Fetch on mount and when page changes
  useEffect(() => {
    refresh();
  }, [refresh]);

  const create = async (data: TCreate): Promise<T | null> => {
    try {
      const result = await createFn(data);
      toast.success(`${entityName} creado/a exitosamente`);
      await refresh();
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : `Error al crear ${entityName}`;
      toast.error(message);
      logger.error(`Failed to create ${entityName}`, err);
      return null;
    }
  };

  const update = async (id: string, data: TUpdate): Promise<T | null> => {
    try {
      const result = await updateFn(id, data);
      toast.success(`${entityName} actualizado/a exitosamente`);
      await refresh();
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : `Error al actualizar ${entityName}`;
      toast.error(message);
      logger.error(`Failed to update ${entityName}`, err);
      return null;
    }
  };

  const remove = async (id: string): Promise<boolean> => {
    try {
      await deleteFn(id);
      toast.success(`${entityName} eliminado/a exitosamente`);
      await refresh();
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : `Error al eliminar ${entityName}`;
      toast.error(message);
      logger.error(`Failed to delete ${entityName}`, err);
      return false;
    }
  };

  return {
    items,
    isLoading,
    error,
    page,
    totalPages,
    setPage,
    refresh,
    create,
    update,
    remove,
  };
}
