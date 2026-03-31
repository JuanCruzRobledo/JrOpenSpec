/**
 * useAssignmentMatrix — manages assignment matrix state:
 * selected cells, waiter/sector lists, save logic.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useAssignmentStore, selectAssignments, selectAssignmentsLoading, selectAssignmentsError, selectSelectedDate, selectSelectedShift } from '@/stores/assignment.store';
import { useStaffStore, selectStaff } from '@/stores/staff.store';
import { useSectorStore, selectSectors } from '@/stores/sector.store';
import { useBranch } from '@/hooks/useBranch';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import { cellKey } from '@/components/assignments/AssignmentMatrix';
import type { AssignmentBulkItem } from '@/types/assignment';

export function useAssignmentMatrix() {
  const { selectedBranchId } = useBranch();
  const branchId = selectedBranchId!;
  const toast = useToast();

  // Assignment store selectors
  const assignments = useAssignmentStore(useShallow(selectAssignments));
  const isLoading = useAssignmentStore(selectAssignmentsLoading);
  const error = useAssignmentStore(selectAssignmentsError);
  const selectedDate = useAssignmentStore(selectSelectedDate);
  const selectedShift = useAssignmentStore(selectSelectedShift);
  const fetchAssignments = useAssignmentStore((s) => s.fetchAssignments);
  const createBulk = useAssignmentStore((s) => s.createBulk);
  const setSelectedDate = useAssignmentStore((s) => s.setSelectedDate);
  const setSelectedShift = useAssignmentStore((s) => s.setSelectedShift);

  // Staff store — filter to WAITER role only
  const allStaff = useStaffStore(useShallow(selectStaff));
  const fetchStaff = useStaffStore((s) => s.fetchStaff);
  const waiters = useMemo(
    () => allStaff.filter((s) => s.rol === 'WAITER'),
    [allStaff],
  );

  // Sector store
  const sectors = useSectorStore(useShallow(selectSectors));
  const fetchSectors = useSectorStore((s) => s.fetchSectors);

  // Local cell state — Set of "waiterId:sectorId" keys
  const [selectedCells, setSelectedCells] = useState<Set<string>>(new Set());
  const [isSaving, setIsSaving] = useState(false);

  // Fetch dependencies on mount
  useEffect(() => {
    fetchStaff();
    fetchSectors(branchId);
  }, [branchId, fetchStaff, fetchSectors]);

  // Fetch assignments when date changes
  useEffect(() => {
    if (selectedDate) {
      fetchAssignments(branchId, selectedDate);
    }
  }, [branchId, selectedDate, fetchAssignments]);

  // Sync selected cells from fetched assignments when shift matches
  useEffect(() => {
    const cells = new Set<string>();
    const filtered = selectedShift
      ? assignments.filter((a) => a.turno === selectedShift)
      : assignments;

    for (const assignment of filtered) {
      cells.add(cellKey(assignment.mozo.id, assignment.sector.id));
    }
    setSelectedCells(cells);
  }, [assignments, selectedShift]);

  const handleToggle = useCallback((waiterId: number, sectorId: number) => {
    setSelectedCells((prev) => {
      const next = new Set(prev);
      const key = cellKey(waiterId, sectorId);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const handleSave = useCallback(async () => {
    if (!selectedShift) {
      toast.warning('Selecciona un turno antes de guardar');
      return;
    }

    setIsSaving(true);
    try {
      const asignaciones: AssignmentBulkItem[] = Array.from(selectedCells).map((key) => {
        const [waiterId, sectorId] = key.split(':').map(Number);
        return { mozo_id: waiterId, sector_id: sectorId };
      });

      await createBulk(branchId, {
        fecha: selectedDate,
        turno: selectedShift,
        asignaciones,
      });

      toast.success('Asignaciones guardadas exitosamente');
      // Refresh to get updated assignment IDs from server
      await fetchAssignments(branchId, selectedDate);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar asignaciones';
      toast.error(message);
      logger.error('Failed to save assignments', err);
    } finally {
      setIsSaving(false);
    }
  }, [branchId, selectedDate, selectedShift, selectedCells, createBulk, fetchAssignments, toast]);

  return {
    waiters,
    sectors,
    assignments,
    selectedCells,
    isLoading,
    isSaving,
    error,
    selectedDate,
    selectedShift,
    setSelectedDate,
    setSelectedShift,
    handleToggle,
    handleSave,
    refresh: () => fetchAssignments(branchId, selectedDate),
  };
}
