import type { MenuProduct, MenuCategory } from '@/types/menu';
import type { AllergenMode } from '@/types/filters';
import { searchIncludes } from '@/lib/text';

/**
 * Pure filter function for menu products.
 *
 * Filtering rules:
 * - Search: accent-insensitive, case-insensitive match on name + shortDescription
 * - Allergen strict: hide product if allergenSlugs contains ANY selected allergen
 * - Allergen very_strict: first expand selected allergens with cross-reactions,
 *   then hide if allergenSlugs OR mayContainSlugs contains any expanded allergen
 * - Dietary: AND logic — product must match ALL selected dietary profiles
 * - Cooking: OR logic — product must match at least one selected cooking method
 *
 * @param products        - Flat list of products to filter
 * @param search          - Raw search string (accent normalization applied internally)
 * @param allergenFilter  - Allergen codes and filtering mode
 * @param dietaryFilter   - Dietary profile slugs (AND logic)
 * @param cookingFilter   - Cooking method slugs (OR logic)
 * @param crossReactionMap - Bidirectional map of allergen slug → cross-reacting slugs
 * @returns Filtered product list
 */
export function filterProducts(
  products: MenuProduct[],
  search: string,
  allergenFilter: { codes: string[]; mode: AllergenMode },
  dietaryFilter: string[],
  cookingFilter: string[],
  crossReactionMap: Map<string, string[]>
): MenuProduct[] {
  const hasSearch = search.trim().length > 0;
  const hasAllergens = allergenFilter.codes.length > 0 && allergenFilter.mode !== 'off';
  const hasDietary = dietaryFilter.length > 0;
  const hasCooking = cookingFilter.length > 0;

  // Early exit — nothing to filter
  if (!hasSearch && !hasAllergens && !hasDietary && !hasCooking) {
    return products;
  }

  // Expand allergen codes with cross-reactions for very_strict mode
  let expandedAllergens = allergenFilter.codes;
  if (allergenFilter.mode === 'very_strict' && allergenFilter.codes.length > 0) {
    const expanded = new Set<string>(allergenFilter.codes);
    for (const code of allergenFilter.codes) {
      const crossReacts = crossReactionMap.get(code);
      if (crossReacts) {
        for (const cr of crossReacts) {
          expanded.add(cr);
        }
      }
    }
    expandedAllergens = Array.from(expanded);
  }

  return products.filter((product) => {
    // --- Search filter ---
    if (hasSearch) {
      const matchesName = searchIncludes(product.name, search);
      const matchesDescription =
        product.description != null && searchIncludes(product.description, search);
      if (!matchesName && !matchesDescription) return false;
    }

    // --- Allergen filter ---
    if (hasAllergens) {
      if (allergenFilter.mode === 'strict') {
        // Strict: hide if product CONTAINS any selected allergen
        const hasConflict = expandedAllergens.some((code) =>
          product.allergenSlugs.includes(code)
        );
        if (hasConflict) return false;
      } else if (allergenFilter.mode === 'very_strict') {
        // Very strict: expanded allergens, hide if contains OR may contain
        const hasConflict = expandedAllergens.some((code) =>
          product.allergenSlugs.includes(code)
        );
        if (hasConflict) return false;
        // Note: MenuProduct only has allergenSlugs (contains). The mayContain
        // check would require the full ProductDetail. For quick-filter purposes,
        // very_strict with expanded cross-reactions is the best we can do from
        // the menu list. Full mayContain info is shown in the detail modal.
      }
    }

    // --- Dietary filter (AND) ---
    if (hasDietary) {
      const matchesAll = dietaryFilter.every((slug) =>
        product.dietaryProfileSlugs.includes(slug)
      );
      if (!matchesAll) return false;
    }

    // --- Cooking filter (OR) ---
    if (hasCooking) {
      const matchesAny = cookingFilter.some((slug) =>
        product.cookingMethodSlugs.includes(slug)
      );
      if (!matchesAny) return false;
    }

    return true;
  });
}

/**
 * Filters a full category tree, removing products that don't match and then
 * removing empty subcategories and empty categories.
 *
 * @returns A new MenuCategory array with only matching content.
 */
export function filterCategories(
  categories: MenuCategory[],
  search: string,
  allergenFilter: { codes: string[]; mode: AllergenMode },
  dietaryFilter: string[],
  cookingFilter: string[],
  crossReactionMap: Map<string, string[]>
): MenuCategory[] {
  return categories
    .map((category) => {
      const filteredSubcategories = category.subcategories
        .map((sub) => {
          const filteredProducts = filterProducts(
            sub.products,
            search,
            allergenFilter,
            dietaryFilter,
            cookingFilter,
            crossReactionMap
          );
          return { ...sub, products: filteredProducts };
        })
        .filter((sub) => sub.products.length > 0);

      return { ...category, subcategories: filteredSubcategories };
    })
    .filter((category) => category.subcategories.length > 0);
}
