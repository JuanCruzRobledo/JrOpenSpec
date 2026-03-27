// Subcategory types matching the real backend API (Spanish field names)

export type SubcategoryEstado = 'activo' | 'inactivo';

export interface Subcategory {
  id: number;
  nombre: string;
  imagen_url: string | null;
  categoria_id: number;
  categoria_nombre: string | null;
  orden: number;
  estado: SubcategoryEstado;
  productos_count: number;
  created_at: string;
  updated_at: string;
}

export interface SubcategoryCreate {
  nombre: string;
  categoria_id: number;
  imagen_url?: string | null;
  orden?: number;
  estado?: SubcategoryEstado;
}

export interface SubcategoryUpdate {
  nombre?: string;
  categoria_id?: number;
  imagen_url?: string | null;
  orden?: number;
  estado?: SubcategoryEstado;
}
