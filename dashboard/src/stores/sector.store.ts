/**
 * Sector store — manages sector list and CRUD operations.
 *
 * NEVER destructure: use individual selectors always.
 */
import { create } from 'zustand';
import { sectorService } from '@/services/sector.service';
import { logger } from '@/lib/logger';
import type { Sector, SectorCreate, SectorUpdate } from '@/types/sector';
import type { PaginationMeta } from '@/types/api';

const EMPTY_ARRAY: Sector[] = [];

interface SectorState {
  sectors: Sector[];
  isLoading: boolean;
  error: string | null;
  meta: PaginationMeta | null;

  fetchSectors: (branchId: number, page?: number, limit?: number) => Promise<void>;
  createSector: (branchId: number, data: SectorCreate) => Promise<Sector>;
  updateSector: (branchId: number, id: number, data: SectorUpdate) => Promise<Sector>;
  removeSector: (branchId: number, id: number) => Promise<void>;
  clearSectors: () => void;
}

export const useSectorStore = create<SectorState>()((set) => ({
  sectors: EMPTY_ARRAY,
  isLoading: false,
  error: null,
  meta: null,

  fetchSectors: async (branchId, page = 1, limit = 50) => {
    set({ isLoading: true, error: null });
    try {
      const res = await sectorService.list(branchId, { page, limit });
      set({ sectors: res.data, meta: res.meta, isLoading: false });
    } catch (err) {
      logger.error('Failed to fetch sectors', err);
      set({ error: 'Error al cargar sectores', isLoading: false });
    }
  },

  createSector: async (branchId, data) => {
    const sector = await sectorService.create(branchId, data);
    set((s) => ({ sectors: [...s.sectors, sector] }));
    return sector;
  },

  updateSector: async (branchId, id, data) => {
    const updated = await sectorService.update(branchId, id, data);
    set((s) => ({
      sectors: s.sectors.map((sec) => (sec.id === id ? updated : sec)),
    }));
    return updated;
  },

  removeSector: async (branchId, id) => {
    await sectorService.remove(branchId, id);
    set((s) => ({
      sectors: s.sectors.filter((sec) => sec.id !== id),
    }));
  },

  clearSectors: () => set({ sectors: EMPTY_ARRAY, meta: null, error: null }),
}));

// Selectors — use these, never destructure the store
export const selectSectors = (s: SectorState) => s.sectors;
export const selectSectorsLoading = (s: SectorState) => s.isLoading;
export const selectSectorsError = (s: SectorState) => s.error;
export const selectSectorsMeta = (s: SectorState) => s.meta;
