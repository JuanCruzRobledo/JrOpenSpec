/**
 * Unit tests for filter.store.ts
 * Uses getState/setState directly — no React rendering needed.
 * The filter store is NOT persisted — resets to defaults each visit.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useFilterStore } from '../filter.store';

// ---------------------------------------------------------------------------
// Reset store before each test (not persisted, but state is shared in module)
// ---------------------------------------------------------------------------

beforeEach(() => {
  useFilterStore.getState().clearAll();
});

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

describe('useFilterStore — initial state', () => {
  it('starts with empty searchQuery', () => {
    expect(useFilterStore.getState().searchQuery).toBe('');
  });

  it('starts with allergenMode "off"', () => {
    expect(useFilterStore.getState().allergenMode).toBe('off');
  });

  it('starts with no selected allergens', () => {
    expect(useFilterStore.getState().selectedAllergens).toHaveLength(0);
  });

  it('starts with no selected dietary profiles', () => {
    expect(useFilterStore.getState().selectedDietary).toHaveLength(0);
  });

  it('starts with no selected cooking methods', () => {
    expect(useFilterStore.getState().selectedCooking).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// setSearchQuery
// ---------------------------------------------------------------------------

describe('useFilterStore — setSearchQuery()', () => {
  it('updates searchQuery', () => {
    useFilterStore.getState().setSearchQuery('pizza');
    expect(useFilterStore.getState().searchQuery).toBe('pizza');
  });

  it('can clear searchQuery with empty string', () => {
    useFilterStore.getState().setSearchQuery('pizza');
    useFilterStore.getState().setSearchQuery('');
    expect(useFilterStore.getState().searchQuery).toBe('');
  });
});

// ---------------------------------------------------------------------------
// setAllergenMode
// ---------------------------------------------------------------------------

describe('useFilterStore — setAllergenMode()', () => {
  it('can set mode to "strict"', () => {
    useFilterStore.getState().setAllergenMode('strict');
    expect(useFilterStore.getState().allergenMode).toBe('strict');
  });

  it('can set mode to "very_strict"', () => {
    useFilterStore.getState().setAllergenMode('very_strict');
    expect(useFilterStore.getState().allergenMode).toBe('very_strict');
  });

  it('can set mode back to "off"', () => {
    useFilterStore.getState().setAllergenMode('strict');
    useFilterStore.getState().setAllergenMode('off');
    expect(useFilterStore.getState().allergenMode).toBe('off');
  });
});

// ---------------------------------------------------------------------------
// toggleAllergen — auto-promotes mode from 'off' to 'strict'
// ---------------------------------------------------------------------------

describe('useFilterStore — toggleAllergen()', () => {
  it('adds allergen to selectedAllergens when toggled on', () => {
    useFilterStore.getState().toggleAllergen('gluten');
    expect(useFilterStore.getState().selectedAllergens).toContain('gluten');
  });

  it('removes allergen from selectedAllergens when toggled off', () => {
    useFilterStore.getState().toggleAllergen('gluten');
    useFilterStore.getState().toggleAllergen('gluten');
    expect(useFilterStore.getState().selectedAllergens).not.toContain('gluten');
  });

  it('auto-promotes mode from "off" to "strict" when first allergen is selected', () => {
    expect(useFilterStore.getState().allergenMode).toBe('off');
    useFilterStore.getState().toggleAllergen('gluten');
    expect(useFilterStore.getState().allergenMode).toBe('strict');
  });

  it('does NOT change mode if already "strict" when adding another allergen', () => {
    useFilterStore.getState().toggleAllergen('gluten'); // auto-promotes to strict
    useFilterStore.getState().toggleAllergen('lacteos'); // should stay strict
    expect(useFilterStore.getState().allergenMode).toBe('strict');
  });

  it('does NOT change mode to "off" when removing an allergen', () => {
    useFilterStore.getState().toggleAllergen('gluten');
    // Mode is now strict
    useFilterStore.getState().toggleAllergen('gluten'); // remove it
    // Mode should remain strict (removing does not reset mode)
    expect(useFilterStore.getState().allergenMode).toBe('strict');
    expect(useFilterStore.getState().selectedAllergens).toHaveLength(0);
  });

  it('does NOT auto-promote mode if already "very_strict"', () => {
    useFilterStore.getState().setAllergenMode('very_strict');
    useFilterStore.getState().toggleAllergen('gluten');
    expect(useFilterStore.getState().allergenMode).toBe('very_strict');
  });

  it('can add multiple allergens', () => {
    useFilterStore.getState().toggleAllergen('gluten');
    useFilterStore.getState().toggleAllergen('lacteos');
    useFilterStore.getState().toggleAllergen('pescado');
    expect(useFilterStore.getState().selectedAllergens).toHaveLength(3);
  });
});

// ---------------------------------------------------------------------------
// toggleDietary
// ---------------------------------------------------------------------------

describe('useFilterStore — toggleDietary()', () => {
  it('adds dietary slug when toggled on', () => {
    useFilterStore.getState().toggleDietary('vegano');
    expect(useFilterStore.getState().selectedDietary).toContain('vegano');
  });

  it('removes dietary slug when toggled off', () => {
    useFilterStore.getState().toggleDietary('vegano');
    useFilterStore.getState().toggleDietary('vegano');
    expect(useFilterStore.getState().selectedDietary).not.toContain('vegano');
  });

  it('can toggle multiple dietary slugs independently', () => {
    useFilterStore.getState().toggleDietary('vegano');
    useFilterStore.getState().toggleDietary('vegetariano');
    expect(useFilterStore.getState().selectedDietary).toHaveLength(2);
    useFilterStore.getState().toggleDietary('vegano');
    expect(useFilterStore.getState().selectedDietary).toHaveLength(1);
    expect(useFilterStore.getState().selectedDietary).toContain('vegetariano');
  });
});

// ---------------------------------------------------------------------------
// toggleCooking
// ---------------------------------------------------------------------------

describe('useFilterStore — toggleCooking()', () => {
  it('adds cooking slug when toggled on', () => {
    useFilterStore.getState().toggleCooking('horno');
    expect(useFilterStore.getState().selectedCooking).toContain('horno');
  });

  it('removes cooking slug when toggled off', () => {
    useFilterStore.getState().toggleCooking('horno');
    useFilterStore.getState().toggleCooking('horno');
    expect(useFilterStore.getState().selectedCooking).not.toContain('horno');
  });
});

// ---------------------------------------------------------------------------
// clearAll — resets everything
// ---------------------------------------------------------------------------

describe('useFilterStore — clearAll()', () => {
  it('resets all filters to initial state', () => {
    // Set a bunch of state
    useFilterStore.getState().setSearchQuery('pizza');
    useFilterStore.getState().toggleAllergen('gluten'); // also sets mode to strict
    useFilterStore.getState().toggleDietary('vegano');
    useFilterStore.getState().toggleCooking('horno');

    useFilterStore.getState().clearAll();

    const state = useFilterStore.getState();
    expect(state.searchQuery).toBe('');
    expect(state.allergenMode).toBe('off');
    expect(state.selectedAllergens).toHaveLength(0);
    expect(state.selectedDietary).toHaveLength(0);
    expect(state.selectedCooking).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// activeFilterCount
// ---------------------------------------------------------------------------

describe('useFilterStore — activeFilterCount()', () => {
  it('returns 0 when no filters are active', () => {
    expect(useFilterStore.getState().activeFilterCount()).toBe(0);
  });

  it('counts allergen filter as 1 when mode is strict', () => {
    useFilterStore.getState().toggleAllergen('gluten'); // auto-promotes to strict
    expect(useFilterStore.getState().activeFilterCount()).toBe(1);
  });

  it('counts allergen filter as 1 regardless of how many allergens are selected', () => {
    useFilterStore.getState().toggleAllergen('gluten');
    useFilterStore.getState().toggleAllergen('lacteos');
    expect(useFilterStore.getState().activeFilterCount()).toBe(1);
  });

  it('counts each dietary selection individually', () => {
    useFilterStore.getState().toggleDietary('vegano');
    useFilterStore.getState().toggleDietary('vegetariano');
    expect(useFilterStore.getState().activeFilterCount()).toBe(2);
  });

  it('counts each cooking selection individually', () => {
    useFilterStore.getState().toggleCooking('horno');
    useFilterStore.getState().toggleCooking('parrilla');
    expect(useFilterStore.getState().activeFilterCount()).toBe(2);
  });

  it('sums allergen + dietary + cooking counts', () => {
    useFilterStore.getState().toggleAllergen('gluten'); // +1
    useFilterStore.getState().toggleDietary('vegano'); // +1
    useFilterStore.getState().toggleCooking('horno'); // +1
    expect(useFilterStore.getState().activeFilterCount()).toBe(3);
  });

  it('allergenMode "off" with no allergens = 0 allergen count', () => {
    // mode is off (default), no allergens selected
    expect(useFilterStore.getState().activeFilterCount()).toBe(0);
  });
});
