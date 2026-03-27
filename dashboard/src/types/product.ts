// Product types matching the real backend API (Spanish field names)
// Prices stored in cents (integer): 12550 = $125.50

export type ProductEstado = 'activo' | 'inactivo';

export interface Product {
  id: number;
  nombre: string;
  descripcion: string | null;
  categoria_id: number;
  categoria_nombre: string | null;
  subcategoria_id: number | null;
  subcategoria_nombre: string | null;
  /** Price in cents (integer). Display: precio / 100 */
  precio: number;
  imagen_url: string | null;
  destacado: boolean;
  popular: boolean;
  estado: ProductEstado;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  nombre: string;
  descripcion?: string | null;
  categoria_id: number;
  subcategoria_id?: number | null;
  /** Price in cents (integer) */
  precio: number;
  imagen_url?: string | null;
  destacado?: boolean;
  popular?: boolean;
  estado?: ProductEstado;
}

export interface ProductUpdate {
  nombre?: string;
  descripcion?: string | null;
  categoria_id?: number;
  subcategoria_id?: number | null;
  /** Price in cents (integer) */
  precio?: number;
  imagen_url?: string | null;
  destacado?: boolean;
  popular?: boolean;
  estado?: ProductEstado;
}
