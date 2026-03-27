// Extended product types for Phase 4 enrichment endpoints

import type { AllergenSeverity, PresenceType } from '@/types/allergen';

export type FlavorProfile = 'sweet' | 'salty' | 'sour' | 'bitter' | 'umami' | 'spicy';
export type TextureProfile = 'crispy' | 'creamy' | 'crunchy' | 'soft' | 'chewy' | 'liquid';
export type IngredientUnit = 'g' | 'kg' | 'ml' | 'l' | 'unit' | 'tbsp' | 'tsp' | 'cup' | 'oz' | 'lb' | 'pinch';
export type BatchPriceOperation =
  | 'fixed_add'
  | 'fixed_subtract'
  | 'percentage_increase'
  | 'percentage_decrease';

// -- Product allergen association --
export interface ProductAllergenData {
  alergeno_id: number;
  tipo_presencia: PresenceType;
  nivel_riesgo: AllergenSeverity;
  notas?: string | null;
}

// -- Product ingredient --
export interface ProductIngredientData {
  nombre: string;
  cantidad: number;
  unidad: IngredientUnit;
  orden: number;
  es_opcional: boolean;
  notas?: string | null;
}

// -- Badge/seal assign --
export interface BadgeAssignData {
  badge_id: number;
  orden: number;
}

export interface SealAssignData {
  seal_id: number;
  orden: number;
}

// -- Branch product --
export interface BranchProduct {
  id: number;
  sucursal_id: number;
  sucursal_nombre: string;
  producto_id: number;
  activo: boolean;
  precio_centavos: number | null;
  /** Effective price: branch override or product base price */
  precio_efectivo_centavos: number;
  orden: number;
}

export interface BranchProductInput {
  sucursal_id: number;
  activo: boolean;
  precio_centavos: number | null;
}

// -- Batch price --
export interface BatchPriceRequest {
  producto_ids: number[];
  operacion: BatchPriceOperation;
  monto: number;
  sucursal_id: number | null;
}

export interface BatchPriceChange {
  producto_id: number;
  producto_nombre: string;
  sucursal_id: number;
  sucursal_nombre: string;
  precio_anterior_centavos: number;
  precio_nuevo_centavos: number;
}

export interface BatchPricePreview {
  cambios: BatchPriceChange[];
  total_productos: number;
  total_sucursales: number;
  total_cambios: number;
}

export interface BatchPriceApplyResponse {
  aplicados: number;
  audit_log_ids: number[];
}
