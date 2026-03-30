import { apiClient } from './api-client';
import type { MenuResponse } from '@/types/menu';
import type {
  AllergenPresence,
  AllergenRiskLevel,
  ProductDetail,
  ProductAllergenDetail,
  CrossReaction,
  DietaryProfileInfo,
  CookingMethodInfo,
  Ingredient,
} from '@/types/product-detail';

interface RawCrossReaction {
  allergenId?: string | number;
  allergenSlug?: string;
  allergenName?: string;
  code?: string;
  name?: string;
  severity?: string;
  riskLevel?: string;
}

interface RawProductAllergen {
  allergenId?: string | number;
  allergenSlug?: string;
  allergenName?: string;
  code?: string;
  name?: string;
  icon?: string | null;
  presence?: string;
  presenceType?: string;
  riskLevel?: string;
  notes?: string | null;
  crossReactions?: RawCrossReaction[];
}

interface RawNamedProfile {
  id?: string | number;
  slug?: string;
  code?: string;
  name?: string;
  icon?: string | null;
  iconName?: string | null;
}

interface RawIngredient {
  id?: string | number;
  name?: string;
  isOptional?: boolean;
  quantity?: number | null;
  unit?: string | null;
  allergenSlugs?: string[];
}

interface RawProductDetailResponse {
  id?: string | number;
  name?: string;
  slug?: string;
  description?: string | null;
  shortDescription?: string | null;
  priceCents?: number;
  imageUrl?: string | null;
  imageUrls?: string[];
  isAvailable?: boolean;
  categoryName?: string;
  subcategoryName?: string;
  category?: { name?: string; slug?: string };
  subcategory?: { name?: string; slug?: string };
  allergens?: RawProductAllergen[];
  dietaryProfiles?: RawNamedProfile[];
  cookingMethods?: RawNamedProfile[];
  ingredients?: RawIngredient[];
  flavorProfiles?: string[];
  textureProfiles?: string[];
  preparationTime?: number | null;
  portionSize?: string | null;
  calories?: number | null;
}

function normalizeRiskLevel(value: string | undefined): AllergenRiskLevel {
  switch (value) {
    case 'low':
      return 'low';
    case 'medium':
    case 'moderate':
      return 'medium';
    case 'high':
    case 'severe':
    case 'life_threatening':
      return 'high';
    default:
      return 'low';
  }
}

function normalizePresence(value: string | undefined): AllergenPresence {
  switch (value) {
    case 'contains':
      return 'contains';
    case 'may_contain':
      return 'may_contain';
    case 'free':
    case 'free_of':
      return 'free';
    default:
      return 'contains';
  }
}

function normalizeCrossReaction(crossReaction: RawCrossReaction, index: number): CrossReaction {
  const slug = crossReaction.allergenSlug ?? crossReaction.code ?? `cross-reaction-${index}`;

  return {
    allergenId: String(crossReaction.allergenId ?? slug),
    allergenSlug: slug,
    allergenName: crossReaction.allergenName ?? crossReaction.name ?? slug,
    riskLevel: normalizeRiskLevel(crossReaction.riskLevel ?? crossReaction.severity),
  };
}

function normalizeAllergen(allergen: RawProductAllergen, index: number): ProductAllergenDetail {
  const slug = allergen.allergenSlug ?? allergen.code ?? `allergen-${index}`;

  return {
    allergenId: String(allergen.allergenId ?? slug),
    allergenSlug: slug,
    allergenName: allergen.allergenName ?? allergen.name ?? slug,
    icon: allergen.icon ?? null,
    presence: normalizePresence(allergen.presence ?? allergen.presenceType),
    riskLevel: normalizeRiskLevel(allergen.riskLevel),
    notes: allergen.notes ?? null,
    crossReactions: (allergen.crossReactions ?? []).map(normalizeCrossReaction),
  };
}

function normalizeDietaryProfile(profile: RawNamedProfile, index: number): DietaryProfileInfo {
  const slug = profile.slug ?? profile.code ?? `dietary-${index}`;

  return {
    id: String(profile.id ?? slug),
    slug,
    name: profile.name ?? slug,
    iconName: profile.iconName ?? profile.icon ?? null,
  };
}

function normalizeCookingMethod(method: RawNamedProfile, index: number): CookingMethodInfo {
  const slug = method.slug ?? method.code ?? `cooking-${index}`;

  return {
    id: String(method.id ?? slug),
    slug,
    name: method.name ?? slug,
  };
}

function normalizeIngredient(ingredient: RawIngredient, index: number): Ingredient {
  return {
    id: String(ingredient.id ?? `ingredient-${index}`),
    name: ingredient.name ?? '',
    isOptional: ingredient.isOptional ?? false,
    quantity: ingredient.quantity ?? null,
    unit: ingredient.unit ?? null,
    allergenSlugs: ingredient.allergenSlugs ?? [],
  };
}

function normalizeProductDetail(raw: RawProductDetailResponse): ProductDetail {
  const imageUrls = raw.imageUrls ?? (raw.imageUrl ? [raw.imageUrl] : []);
  const categoryName = raw.categoryName ?? raw.category?.name ?? '';
  const subcategoryName = raw.subcategoryName ?? raw.subcategory?.name ?? '';

  return {
    id: String(raw.id ?? ''),
    name: raw.name ?? '',
    slug: raw.slug ?? '',
    description: raw.description ?? raw.shortDescription ?? null,
    imageUrls,
    priceCents: raw.priceCents ?? 0,
    isAvailable: raw.isAvailable ?? true,
    categoryName,
    subcategoryName,
    allergens: (raw.allergens ?? []).map(normalizeAllergen),
    dietaryProfiles: (raw.dietaryProfiles ?? []).map(normalizeDietaryProfile),
    cookingMethods: (raw.cookingMethods ?? []).map(normalizeCookingMethod),
    ingredients: (raw.ingredients ?? []).map(normalizeIngredient),
    flavorProfiles: raw.flavorProfiles ?? [],
    textureProfiles: raw.textureProfiles ?? [],
    preparationTime: raw.preparationTime ?? null,
    portionSize: raw.portionSize ?? null,
    calories: raw.calories ?? null,
  };
}

/**
 * Fetches the full public menu for a branch.
 *
 * GET /api/public/menu/{slug}
 *
 * Response is cached by the menu store with stale-while-revalidate pattern.
 * The Workbox NetworkFirst strategy (5s timeout) also caches this at the SW level.
 *
 * @param slug - Branch slug (e.g. "buen-sabor-centro")
 */
export async function getMenu(slug: string): Promise<MenuResponse> {
  const response = await apiClient.get<MenuResponse>(
    `/api/public/menu/${encodeURIComponent(slug)}`
  );
  return response.data;
}

/**
 * Fetches the full detail for a single product.
 *
 * GET /api/public/menu/{slug}/product/{id}
 *
 * Called when a product card is tapped to open the detail modal.
 * Product IDs are BigInteger on the backend; passed as number here.
 *
 * @param slug      - Branch slug
 * @param productId - Product ID (BigInteger from backend)
 */
export async function getProductDetail(
  slug: string,
  productId: number
): Promise<ProductDetail> {
  const response = await apiClient.get<RawProductDetailResponse>(
    `/api/public/menu/${encodeURIComponent(slug)}/product/${productId}`
  );
  return normalizeProductDetail(response.data);
}
