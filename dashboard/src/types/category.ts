// Category types matching the real backend API (Spanish field names)

export type CategoryEstado = 'activo' | 'inactivo';

export interface Category {
  id: number;
  nombre: string;
  icono: string | null;
  imagen_url: string | null;
  orden: number;
  estado: CategoryEstado;
  es_home: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreate {
  nombre: string;
  icono?: string | null;
  imagen_url?: string | null;
  orden?: number;
  estado?: CategoryEstado;
  es_home?: boolean;
}

export interface CategoryUpdate {
  nombre?: string;
  icono?: string | null;
  imagen_url?: string | null;
  orden?: number;
  estado?: CategoryEstado;
  es_home?: boolean;
}
