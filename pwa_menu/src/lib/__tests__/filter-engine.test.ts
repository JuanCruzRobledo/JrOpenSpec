/**
 * Unit tests for filter-engine.ts
 * Tests the pure filter functions directly — no React, no timers.
 */

import { describe, it, expect } from 'vitest';
import {
  filterProducts,
  filterCategories,
  summarizeCrossReactionHiddenProducts,
} from '../filter-engine';
import type { MenuProduct, MenuCategory } from '@/types/menu';

// ---------------------------------------------------------------------------
// Test fixtures
// ---------------------------------------------------------------------------

function makeProduct(overrides: Partial<MenuProduct>): MenuProduct {
  return {
    id: '1',
    name: 'Product',
    slug: 'product',
    description: null,
    imageUrl: null,
    priceCents: 1000,
    isAvailable: true,
    badges: [],
    seals: [],
    allergenSlugs: [],
    mayContainSlugs: [],
    dietaryProfileSlugs: [],
    cookingMethodSlugs: [],
    ...overrides,
  };
}

const pizzaMargherita = makeProduct({
  id: '1',
  name: 'Pizza Margherita',
  slug: 'pizza-margherita',
  allergenSlugs: ['gluten', 'lacteos'],
  mayContainSlugs: ['huevo'],
  dietaryProfileSlugs: ['vegetariano'],
  cookingMethodSlugs: ['horno'],
});

const pizzaNapolitana = makeProduct({
  id: '2',
  name: 'Pizza Napolitana',
  slug: 'pizza-napolitana',
  allergenSlugs: ['gluten', 'lacteos'],
  dietaryProfileSlugs: ['vegetariano'],
  cookingMethodSlugs: ['horno'],
});

const steak = makeProduct({
  id: '3',
  name: 'Steak a la parrilla',
  slug: 'steak-parrilla',
  allergenSlugs: [],
  dietaryProfileSlugs: [],
  cookingMethodSlugs: ['parrilla'],
});

const veganSalad = makeProduct({
  id: '4',
  name: 'Ensalada vegana',
  slug: 'ensalada-vegana',
  allergenSlugs: [],
  dietaryProfileSlugs: ['vegano', 'vegetariano'],
  cookingMethodSlugs: ['frio'],
});

const fishTacos = makeProduct({
  id: '5',
  name: 'Tacos de pescado',
  slug: 'tacos-pescado',
  allergenSlugs: ['pescado', 'gluten'],
  dietaryProfileSlugs: [],
  cookingMethodSlugs: ['frito'],
});

const nutsDesert = makeProduct({
  id: '6',
  name: 'Tarta de frutos secos',
  slug: 'tarta-frutos-secos',
  // frutos_de_cascara cross-reacts with cacahuetes
  allergenSlugs: ['frutos_de_cascara'],
  dietaryProfileSlugs: ['vegetariano'],
  cookingMethodSlugs: ['horno'],
});

const allProducts = [pizzaMargherita, pizzaNapolitana, steak, veganSalad, fishTacos, nutsDesert];

// Empty cross-reaction map for tests that don't need cross-reactions
const emptyCrossMap = new Map<string, string[]>();

// Cross-reaction map: frutos_de_cascara <-> cacahuetes
const crossMap = new Map<string, string[]>([
  ['frutos_de_cascara', ['cacahuetes']],
  ['cacahuetes', ['frutos_de_cascara']],
  ['huevo', ['ave']],
  ['ave', ['huevo']],
]);

const categoriesFixture: MenuCategory[] = [
  {
    id: 'cat-1',
    name: 'Principales',
    slug: 'principales',
    displayOrder: 1,
    subcategories: [
      {
        id: 'sub-1',
        name: 'Todos',
        slug: 'todos',
        displayOrder: 1,
        products: [
          ...allProducts,
          makeProduct({
            id: '7',
            name: 'Pollo grillado',
            slug: 'pollo-grillado',
            allergenSlugs: ['ave'],
            cookingMethodSlugs: ['parrilla'],
          }),
        ],
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// S10: Search filter (pure function — no debounce involved)
// ---------------------------------------------------------------------------

describe('filterProducts — search (S10)', () => {
  it('returns all products when search is empty', () => {
    const result = filterProducts(allProducts, '', { codes: [], mode: 'off' }, [], [], emptyCrossMap);
    expect(result).toHaveLength(allProducts.length);
  });

  it('returns all products when search is only whitespace', () => {
    const result = filterProducts(allProducts, '   ', { codes: [], mode: 'off' }, [], [], emptyCrossMap);
    expect(result).toHaveLength(allProducts.length);
  });

  it('finds both pizzas when searching "piz"', () => {
    const result = filterProducts(allProducts, 'piz', { codes: [], mode: 'off' }, [], [], emptyCrossMap);
    const ids = result.map((p) => p.id);
    expect(ids).toContain('1');
    expect(ids).toContain('2');
    expect(ids).not.toContain('3'); // Steak
  });

  it('search is case-insensitive — "PIZZA" finds both pizzas', () => {
    const result = filterProducts(allProducts, 'PIZZA', { codes: [], mode: 'off' }, [], [], emptyCrossMap);
    expect(result).toHaveLength(2);
  });

  it('search is accent-insensitive — "Ensalada vegana" found via "vegana"', () => {
    const result = filterProducts(allProducts, 'vegana', { codes: [], mode: 'off' }, [], [], emptyCrossMap);
    const ids = result.map((p) => p.id);
    expect(ids).toContain('4');
  });

  it('search matches against description when name does not match', () => {
    const productWithDesc = makeProduct({
      id: '99',
      name: 'Plato especial',
      description: 'Contiene champiñones frescos',
    });
    const result = filterProducts([productWithDesc], 'champiñon', { codes: [], mode: 'off' }, [], [], emptyCrossMap);
    expect(result).toHaveLength(1);
  });

  it('returns empty when no match', () => {
    const result = filterProducts(allProducts, 'xyznonexistent', { codes: [], mode: 'off' }, [], [], emptyCrossMap);
    expect(result).toHaveLength(0);
  });

  it('accent-insensitive: "noqui" matches "Ñoquis"', () => {
    const noquis = makeProduct({ id: '7', name: 'Ñoquis al pesto' });
    const result = filterProducts([noquis], 'noqui', { codes: [], mode: 'off' }, [], [], emptyCrossMap);
    expect(result).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// S11: Allergen strict mode — hides products that CONTAIN selected allergen
// ---------------------------------------------------------------------------

describe('filterProducts — allergen strict mode (S11)', () => {
  it('hides products that contain the selected allergen', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: ['gluten'], mode: 'strict' },
      [],
      [],
      emptyCrossMap
    );
    const ids = result.map((p) => p.id);
    // pizzas and fishTacos have gluten
    expect(ids).not.toContain('1'); // pizza margherita
    expect(ids).not.toContain('2'); // pizza napolitana
    expect(ids).not.toContain('5'); // fish tacos
    // steak, veganSalad, nutsDesert don't have gluten
    expect(ids).toContain('3');
    expect(ids).toContain('4');
    expect(ids).toContain('6');
  });

  it('allows products that do NOT contain the selected allergen', () => {
    const result = filterProducts(
      [steak, veganSalad],
      '',
      { codes: ['gluten'], mode: 'strict' },
      [],
      [],
      emptyCrossMap
    );
    expect(result).toHaveLength(2);
  });

  it('no filtering when mode is "off" even if codes are provided', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: ['gluten'], mode: 'off' },
      [],
      [],
      emptyCrossMap
    );
    expect(result).toHaveLength(allProducts.length);
  });

  it('no filtering when codes array is empty with strict mode', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: [], mode: 'strict' },
      [],
      [],
      emptyCrossMap
    );
    expect(result).toHaveLength(allProducts.length);
  });

  it('multiple allergens: strict hides products with ANY of the selected allergens', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: ['gluten', 'pescado'], mode: 'strict' },
      [],
      [],
      emptyCrossMap
    );
    const ids = result.map((p) => p.id);
    // pizzas (gluten), fishTacos (pescado + gluten) all hidden
    expect(ids).not.toContain('1');
    expect(ids).not.toContain('2');
    expect(ids).not.toContain('5');
  });
});

// ---------------------------------------------------------------------------
// S12: Very strict mode — expands with cross-reactions
// ---------------------------------------------------------------------------

describe('filterProducts — allergen very_strict mode (S12)', () => {
  it('hides products containing cross-reaction allergens (expanded)', () => {
    // User selects cacahuetes (peanuts), cross-reacts with frutos_de_cascara (tree nuts)
    // nutsDesert has frutos_de_cascara — should be hidden in very_strict mode
    const result = filterProducts(
      allProducts,
      '',
      { codes: ['cacahuetes'], mode: 'very_strict' },
      [],
      [],
      crossMap
    );
    const ids = result.map((p) => p.id);
    expect(ids).not.toContain('6'); // nutsDesert has frutos_de_cascara (cross-reaction)
  });

  it('without cross-reaction map, very_strict behaves like strict for direct allergens', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: ['gluten'], mode: 'very_strict' },
      [],
      [],
      emptyCrossMap
    );
    const ids = result.map((p) => p.id);
    expect(ids).not.toContain('1');
    expect(ids).not.toContain('2');
    expect(ids).not.toContain('5');
  });

  it('hides products that may_contain the selected allergen', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: ['huevo'], mode: 'very_strict' },
      [],
      [],
      emptyCrossMap
    );

    expect(result.map((p) => p.id)).not.toContain('1');
  });

  it('does NOT expand when mode is strict (not very_strict)', () => {
    // In strict mode with cacahuetes, nutsDesert should still appear
    // because it has frutos_de_cascara, not cacahuetes directly
    const result = filterProducts(
      allProducts,
      '',
      { codes: ['cacahuetes'], mode: 'strict' },
      [],
      [],
      crossMap
    );
    const ids = result.map((p) => p.id);
    expect(ids).toContain('6'); // nutsDesert safe in strict mode
  });

  it('does not hide may_contain matches in strict mode', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: ['huevo'], mode: 'strict' },
      [],
      [],
      emptyCrossMap
    );

    expect(result.map((p) => p.id)).toContain('1');
  });

  it('expands both directions: selecting frutos_de_cascara also expands to cacahuetes', () => {
    const peanutProduct = makeProduct({
      id: '8',
      name: 'Manteca de cacahuete',
      allergenSlugs: ['cacahuetes'],
    });
    const result = filterProducts(
      [peanutProduct],
      '',
      { codes: ['frutos_de_cascara'], mode: 'very_strict' },
      [],
      [],
      crossMap
    );
    // With expansion, cacahuetes is in the expanded set → peanutProduct hidden
    expect(result).toHaveLength(0);
  });
});

describe('summarizeCrossReactionHiddenProducts', () => {
  it('reports only products hidden exclusively by cross-reactions', () => {
    const summary = summarizeCrossReactionHiddenProducts(
      categoriesFixture,
      { codes: ['huevo'], mode: 'very_strict' },
      crossMap,
      [
        { id: '1', slug: 'huevo', name: 'Huevo', crossReacts: [] },
        { id: '2', slug: 'ave', name: 'Ave', crossReacts: [] },
      ]
    );

    expect(summary).toEqual({
      hiddenProductCount: 1,
      selectedAllergenNames: ['Huevo'],
      crossReactionAllergenNames: ['Ave'],
    });
  });

  it('returns null when no products are hidden only by cross-reactions', () => {
    const summary = summarizeCrossReactionHiddenProducts(
      categoriesFixture,
      { codes: ['gluten'], mode: 'very_strict' },
      crossMap,
      [{ id: '1', slug: 'gluten', name: 'Gluten', crossReacts: [] }]
    );

    expect(summary).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// S13: Dietary filter — AND logic
// ---------------------------------------------------------------------------

describe('filterProducts — dietary filter (S13)', () => {
  it('returns only products matching ALL selected dietary profiles (AND)', () => {
    // veganSalad has both 'vegano' and 'vegetariano'
    // pizzas have only 'vegetariano'
    const result = filterProducts(
      allProducts,
      '',
      { codes: [], mode: 'off' },
      ['vegano', 'vegetariano'],
      [],
      emptyCrossMap
    );
    const ids = result.map((p) => p.id);
    expect(ids).toContain('4'); // veganSalad — has both
    expect(ids).not.toContain('1'); // pizza — only vegetariano
    expect(ids).not.toContain('3'); // steak — no dietary
  });

  it('single dietary filter works correctly', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: [], mode: 'off' },
      ['vegetariano'],
      [],
      emptyCrossMap
    );
    const ids = result.map((p) => p.id);
    expect(ids).toContain('1');
    expect(ids).toContain('2');
    expect(ids).toContain('4');
    expect(ids).not.toContain('3'); // steak
    expect(ids).not.toContain('5'); // fishTacos
  });

  it('empty dietary filter returns all products', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: [], mode: 'off' },
      [],
      [],
      emptyCrossMap
    );
    expect(result).toHaveLength(allProducts.length);
  });
});

// ---------------------------------------------------------------------------
// S14: Cooking method filter — OR logic
// ---------------------------------------------------------------------------

describe('filterProducts — cooking method filter (S14)', () => {
  it('returns products matching ANY of the selected cooking methods (OR)', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: [], mode: 'off' },
      [],
      ['horno', 'parrilla'],
      emptyCrossMap
    );
    const ids = result.map((p) => p.id);
    expect(ids).toContain('1'); // horno
    expect(ids).toContain('2'); // horno
    expect(ids).toContain('3'); // parrilla
    expect(ids).toContain('6'); // horno
    expect(ids).not.toContain('4'); // frio
    expect(ids).not.toContain('5'); // frito
  });

  it('single cooking method works', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: [], mode: 'off' },
      [],
      ['frito'],
      emptyCrossMap
    );
    const ids = result.map((p) => p.id);
    expect(ids).toContain('5');
    expect(ids).toHaveLength(1);
  });

  it('empty cooking filter returns all products', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: [], mode: 'off' },
      [],
      [],
      emptyCrossMap
    );
    expect(result).toHaveLength(allProducts.length);
  });
});

// ---------------------------------------------------------------------------
// S15: Combined filters — all active simultaneously
// ---------------------------------------------------------------------------

describe('filterProducts — combined filters (S15)', () => {
  it('applies search + allergen + dietary + cooking simultaneously', () => {
    // Search "pizza", strict gluten filter, vegetariano dietary, horno cooking
    // Both pizzas have gluten → strict mode hides them
    // So with all active: no pizzas remain
    const result = filterProducts(
      allProducts,
      'pizza',
      { codes: ['gluten'], mode: 'strict' },
      ['vegetariano'],
      ['horno'],
      emptyCrossMap
    );
    expect(result).toHaveLength(0);
  });

  it('combined filters return correct results when some pass all conditions', () => {
    // Products that:
    // - name contains "salad" or "ensalada"
    // - no allergen conflicts (empty codes)
    // - vegetariano
    // - frio cooking
    const result = filterProducts(
      allProducts,
      'ensalada',
      { codes: [], mode: 'off' },
      ['vegetariano', 'vegano'],
      ['frio'],
      emptyCrossMap
    );
    const ids = result.map((p) => p.id);
    expect(ids).toContain('4'); // veganSalad matches all
    expect(ids).toHaveLength(1);
  });

  it('early exit optimization: returns all products when nothing is active', () => {
    const result = filterProducts(
      allProducts,
      '',
      { codes: [], mode: 'off' },
      [],
      [],
      emptyCrossMap
    );
    // Should return the same reference (early exit)
    expect(result).toBe(allProducts);
  });
});

// ---------------------------------------------------------------------------
// filterCategories: tree-level filtering
// ---------------------------------------------------------------------------

describe('filterCategories', () => {
  const makeCategory = (products: MenuProduct[]): MenuCategory => ({
    id: 'cat-1',
    name: 'Comidas',
    slug: 'comidas',
    displayOrder: 1,
    subcategories: [
      {
        id: 'sub-1',
        name: 'Pizzas',
        slug: 'pizzas',
        displayOrder: 1,
        products,
      },
    ],
  });

  it('removes subcategories with no matching products', () => {
    const categories = [makeCategory([pizzaMargherita, pizzaNapolitana])];
    const result = filterCategories(
      categories,
      'steak',
      { codes: [], mode: 'off' },
      [],
      [],
      emptyCrossMap
    );
    expect(result).toHaveLength(0);
  });

  it('removes top-level categories when all subcategories become empty', () => {
    const categories = [makeCategory([steak])];
    const result = filterCategories(
      categories,
      'pizza',
      { codes: [], mode: 'off' },
      [],
      [],
      emptyCrossMap
    );
    expect(result).toHaveLength(0);
  });

  it('keeps category and subcategory when some products match', () => {
    const categories = [makeCategory([pizzaMargherita, steak])];
    const result = filterCategories(
      categories,
      'pizza',
      { codes: [], mode: 'off' },
      [],
      [],
      emptyCrossMap
    );
    expect(result).toHaveLength(1);
    expect(result[0]!.subcategories[0]!.products).toHaveLength(1);
    expect(result[0]!.subcategories[0]!.products[0]!.id).toBe('1');
  });
});
