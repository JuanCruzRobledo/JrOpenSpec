/**
 * useCrud hook tests — S12 (delete with confirm) and S15 (pagination).
 * Tests the hook in isolation by mocking all dependencies.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useCrud } from '../useCrud';
import type { PaginatedResponse, PaginationParams } from '@/types/api';

// ---------------------------------------------------------------------------
// Mock toast and pagination hooks
// ---------------------------------------------------------------------------
const mockToastSuccess = vi.fn();
const mockToastError = vi.fn();

vi.mock('@/hooks/useToast', () => ({
  useToast: () => ({
    success: mockToastSuccess,
    error: mockToastError,
    warning: vi.fn(),
    info: vi.fn(),
    add: vi.fn(),
  }),
}));

vi.mock('@/lib/logger', () => ({
  logger: {
    error: vi.fn(),
    warn: vi.fn(),
    debug: vi.fn(),
    info: vi.fn(),
  },
}));

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------
interface FakeItem {
  id: number;
  name: string;
}

function makePagedResponse(items: FakeItem[], total = items.length): PaginatedResponse<FakeItem> {
  return {
    data: items,
    meta: { page: 1, limit: 20, total },
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('S12 — useCrud remove calls deleteFn and refreshes list', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls deleteFn with the correct id on remove', async () => {
    const items: FakeItem[] = [
      { id: 1, name: 'Item A' },
      { id: 2, name: 'Item B' },
    ];

    const fetchFn = vi.fn((_params: PaginationParams): Promise<PaginatedResponse<FakeItem>> =>
      Promise.resolve(makePagedResponse(items)),
    );
    const deleteFn = vi.fn((_id: number): Promise<void> => Promise.resolve());
    const createFn = vi.fn();
    const updateFn = vi.fn();

    const { result } = renderHook(() =>
      useCrud<FakeItem, Partial<FakeItem>, Partial<FakeItem>>({
        fetchFn,
        createFn,
        updateFn,
        deleteFn,
        entityName: 'Item',
      }),
    );

    // Wait for initial fetch
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      const success = await result.current.remove(1);
      expect(success).toBe(true);
    });

    expect(deleteFn).toHaveBeenCalledWith(1);
    expect(mockToastSuccess).toHaveBeenCalledWith(expect.stringContaining('Item'));
  });

  it('shows error toast and returns false when deleteFn throws', async () => {
    const fetchFn = vi.fn((): Promise<PaginatedResponse<FakeItem>> =>
      Promise.resolve(makePagedResponse([])),
    );
    const deleteFn = vi.fn((): Promise<void> => Promise.reject(new Error('Delete failed')));

    const { result } = renderHook(() =>
      useCrud<FakeItem, Partial<FakeItem>, Partial<FakeItem>>({
        fetchFn,
        createFn: vi.fn(),
        updateFn: vi.fn(),
        deleteFn,
        entityName: 'Item',
      }),
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      const success = await result.current.remove(99);
      expect(success).toBe(false);
    });

    expect(mockToastError).toHaveBeenCalledWith('Delete failed');
  });
});

describe('S15 — useCrud pagination: setPage triggers new fetch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches with page=2 when setPage(2) is called', async () => {
    const fetchFn = vi.fn(({ page }: PaginationParams): Promise<PaginatedResponse<FakeItem>> =>
      Promise.resolve(makePagedResponse([{ id: page, name: `Page ${page}` }], 40)),
    );

    const { result } = renderHook(() =>
      useCrud<FakeItem, Partial<FakeItem>, Partial<FakeItem>>({
        fetchFn,
        createFn: vi.fn(),
        updateFn: vi.fn(),
        deleteFn: vi.fn(),
        entityName: 'Item',
      }),
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(fetchFn).toHaveBeenCalledWith(expect.objectContaining({ page: 1 }));

    act(() => {
      result.current.setPage(2);
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(fetchFn).toHaveBeenCalledWith(expect.objectContaining({ page: 2 }));
  });

  it('exposes correct totalPages based on meta.total', async () => {
    const fetchFn = vi.fn((): Promise<PaginatedResponse<FakeItem>> =>
      Promise.resolve(makePagedResponse([], 60)),
    );

    const { result } = renderHook(() =>
      useCrud<FakeItem, Partial<FakeItem>, Partial<FakeItem>>({
        fetchFn,
        createFn: vi.fn(),
        updateFn: vi.fn(),
        deleteFn: vi.fn(),
        entityName: 'Item',
      }),
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // With total=60 and default pageSize=20 → 3 pages
    expect(result.current.totalPages).toBe(3);
  });
});

describe('useCrud create — posts and refreshes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls createFn and shows success toast', async () => {
    const newItem: FakeItem = { id: 10, name: 'New' };
    const fetchFn = vi.fn((): Promise<PaginatedResponse<FakeItem>> =>
      Promise.resolve(makePagedResponse([])),
    );
    const createFn = vi.fn((): Promise<FakeItem> => Promise.resolve(newItem));

    const { result } = renderHook(() =>
      useCrud<FakeItem, Partial<FakeItem>, Partial<FakeItem>>({
        fetchFn,
        createFn,
        updateFn: vi.fn(),
        deleteFn: vi.fn(),
        entityName: 'Item',
      }),
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      const created = await result.current.create({ name: 'New' });
      expect(created).toEqual(newItem);
    });

    expect(createFn).toHaveBeenCalledWith({ name: 'New' });
    expect(mockToastSuccess).toHaveBeenCalled();
  });
});
