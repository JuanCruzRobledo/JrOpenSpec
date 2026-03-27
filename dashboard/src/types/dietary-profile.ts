// Dietary profile types matching the real backend API (Spanish field names)

export interface DietaryProfile {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  icono: string | null;
  es_sistema: boolean;
  created_at: string;
  updated_at: string;
}

export interface DietaryProfileCreate {
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  icono?: string | null;
}

export interface DietaryProfileUpdate {
  nombre?: string;
  descripcion?: string | null;
  icono?: string | null;
}
