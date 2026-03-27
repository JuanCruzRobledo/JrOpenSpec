// Cooking method types matching the real backend API (Spanish field names)

export interface CookingMethod {
  id: number;
  codigo: string;
  nombre: string;
  icono: string | null;
  es_sistema: boolean;
  created_at: string;
  updated_at: string;
}

export interface CookingMethodCreate {
  codigo: string;
  nombre: string;
  icono?: string | null;
}

export interface CookingMethodUpdate {
  nombre?: string;
  icono?: string | null;
}
