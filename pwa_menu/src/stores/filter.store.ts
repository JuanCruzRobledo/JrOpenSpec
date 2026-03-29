import { create } from 'zustand';
import type { AllergenMode, FilterState } from '@/types/filters';

// ---------------------------------------------------------------------------
// State & Actions interface
// NOT persisted — resets on page reload by design
// ---------------------------------------------------------------------------

interface FilterStoreState extends FilterState {
  // Actions
  setSearchQuery: (query: string) => void;
  setAllergenMode: (mode: AllergenMode) => void;
  /**
   * Toggle an allergen slug selection.
   * Auto-upgrades allergenMode from 'off' to 'strict' when the first allergen
   * is selected — prevents silent no-op filtering.
   */
  toggleAllergen: (slug: string) => void;
  toggleDietary: (slug: string) => void;
  toggleCooking: (slug: string) => void;
  /** Resets all filter state to defaults */
  clearAll: () => void;
  /** Returns the count of active non-search filters */
  activeFilterCount: () => number;
}

const defaultState: FilterState = {
  searchQuery: '',
  allergenMode: 'off',
  selectedAllergens: [],
  selectedDietary: [],
  selectedCooking: [],
};

// ---------------------------------------------------------------------------
// Store creation — NOT persisted (intentional: fresh filter state per visit)
// ---------------------------------------------------------------------------

const useFilterStore = create<FilterStoreState>()((set, get) => ({
  ...defaultState,

  setSearchQuery(query) {
    set({ searchQuery: query });
  },

  setAllergenMode(mode) {
    set({ allergenMode: mode });
  },

  toggleAllergen(slug) {
    const { selectedAllergens, allergenMode } = get();
    const isSelected = selectedAllergens.includes(slug);
    const next = isSelected
      ? selectedAllergens.filter((s) => s !== slug)
      : [...selectedAllergens, slug];

    // Auto-promote mode to 'strict' when adding the first allergen while mode is 'off'
    const nextMode: AllergenMode =
      !isSelected && next.length > 0 && allergenMode === 'off'
        ? 'strict'
        : allergenMode;

    set({ selectedAllergens: next, allergenMode: nextMode });
  },

  toggleDietary(slug) {
    const { selectedDietary } = get();
    const isSelected = selectedDietary.includes(slug);
    set({
      selectedDietary: isSelected
        ? selectedDietary.filter((s) => s !== slug)
        : [...selectedDietary, slug],
    });
  },

  toggleCooking(slug) {
    const { selectedCooking } = get();
    const isSelected = selectedCooking.includes(slug);
    set({
      selectedCooking: isSelected
        ? selectedCooking.filter((s) => s !== slug)
        : [...selectedCooking, slug],
    });
  },

  clearAll() {
    set({ ...defaultState });
  },

  activeFilterCount() {
    const { allergenMode, selectedAllergens, selectedDietary, selectedCooking } = get();
    const allergenCount = allergenMode !== 'off' || selectedAllergens.length > 0 ? 1 : 0;
    return allergenCount + selectedDietary.length + selectedCooking.length;
  },
}));

// ---------------------------------------------------------------------------
// Individual selectors
// ---------------------------------------------------------------------------

export const selectSearchQuery = (s: FilterStoreState) => s.searchQuery;
export const selectAllergenMode = (s: FilterStoreState) => s.allergenMode;
export const selectSelectedAllergens = (s: FilterStoreState) => s.selectedAllergens;
export const selectSelectedDietary = (s: FilterStoreState) => s.selectedDietary;
export const selectSelectedCooking = (s: FilterStoreState) => s.selectedCooking;
export const selectActiveFilterCount = (s: FilterStoreState) => s.activeFilterCount();

// Action selectors
export const selectSetSearchQueryAction = (s: FilterStoreState) => s.setSearchQuery;
export const selectSetAllergenModeAction = (s: FilterStoreState) => s.setAllergenMode;
export const selectToggleAllergenAction = (s: FilterStoreState) => s.toggleAllergen;
export const selectToggleDietaryAction = (s: FilterStoreState) => s.toggleDietary;
export const selectToggleCookingAction = (s: FilterStoreState) => s.toggleCooking;
export const selectClearAllAction = (s: FilterStoreState) => s.clearAll;

export { useFilterStore };
