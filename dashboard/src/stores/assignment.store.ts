/**
 * Assignment store — manages waiter-sector assignments by date and shift.
 *
 * NEVER destructure: use individual selectors always.
 */
import { create } from 'zustand';
import { assignmentService } from '@/services/assignment.service';
import { logger } from '@/lib/logger';
import type {
  Assignment,
  AssignmentBulkCreate,
  AssignmentsByShift,
} from '@/types/assignment';

const EMPTY_ARRAY: Assignment[] = [];

/** Format date as YYYY-MM-DD */
const formatDate = (date: Date): string => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

interface AssignmentState {
  assignments: Assignment[];
  isLoading: boolean;
  error: string | null;
  selectedDate: string;
  selectedShift: string | null;

  fetchAssignments: (branchId: number, fecha?: string) => Promise<void>;
  createBulk: (branchId: number, data: AssignmentBulkCreate) => Promise<Assignment[]>;
  removeAssignment: (branchId: number, id: number) => Promise<void>;
  setSelectedDate: (date: string) => void;
  setSelectedShift: (shift: string | null) => void;
  clearAssignments: () => void;
}

export const useAssignmentStore = create<AssignmentState>()((set, get) => ({
  assignments: EMPTY_ARRAY,
  isLoading: false,
  error: null,
  selectedDate: formatDate(new Date()),
  selectedShift: null,

  fetchAssignments: async (branchId, fecha?) => {
    const date = fecha ?? get().selectedDate;
    set({ isLoading: true, error: null });
    try {
      const data = await assignmentService.list(branchId, date);
      set({ assignments: Array.isArray(data) ? data : [], isLoading: false });
    } catch (err) {
      logger.error('Failed to fetch assignments', err);
      set({ error: 'Error al cargar asignaciones', isLoading: false });
    }
  },

  createBulk: async (branchId, data) => {
    await assignmentService.createBulk(branchId, data);
    // Refetch to get updated assignments from server
    const date = data.fecha ?? get().selectedDate;
    const updated = await assignmentService.list(branchId, date);
    set({ assignments: Array.isArray(updated) ? updated : [] });
  },

  removeAssignment: async (branchId, id) => {
    await assignmentService.remove(branchId, id);
    set((s) => ({
      assignments: s.assignments.filter((a) => a.id !== id),
    }));
  },

  setSelectedDate: (date) => set({ selectedDate: date }),
  setSelectedShift: (shift) => set({ selectedShift: shift }),
  clearAssignments: () =>
    set({
      assignments: EMPTY_ARRAY,
      error: null,
      selectedShift: null,
    }),
}));

// Selectors — use these, never destructure the store
export const selectAssignments = (s: AssignmentState) => s.assignments;
export const selectAssignmentsLoading = (s: AssignmentState) => s.isLoading;
export const selectAssignmentsError = (s: AssignmentState) => s.error;
export const selectSelectedDate = (s: AssignmentState) => s.selectedDate;
export const selectSelectedShift = (s: AssignmentState) => s.selectedShift;

/** Returns assignments grouped by shift (morning, afternoon, night). */
export const selectAssignmentsByShift = (s: AssignmentState): AssignmentsByShift => {
  const grouped: AssignmentsByShift = {
    morning: [],
    afternoon: [],
    night: [],
  };

  for (const assignment of s.assignments) {
    const shift = assignment.turno.toLowerCase();
    if (shift === 'morning' || shift === 'mañana') {
      grouped.morning.push(assignment);
    } else if (shift === 'afternoon' || shift === 'tarde') {
      grouped.afternoon.push(assignment);
    } else if (shift === 'night' || shift === 'noche') {
      grouped.night.push(assignment);
    }
  }

  return grouped;
};

/** Returns assignments filtered by the currently selected shift. */
export const selectFilteredAssignments = (s: AssignmentState): Assignment[] => {
  if (s.selectedShift === null) {
    return s.assignments;
  }
  return s.assignments.filter((a) => a.turno === s.selectedShift);
};
