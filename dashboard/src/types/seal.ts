// Seal types matching the real backend API (Spanish field names)

export interface Seal {
  id: number;
  codigo: string;
  nombre: string;
  color: string;
  icono: string | null;
  es_sistema: boolean;
  created_at: string;
  updated_at: string;
}

export interface SealCreate {
  codigo: string;
  nombre: string;
  color: string;
  icono?: string | null;
}

export interface SealUpdate {
  nombre?: string;
  color?: string;
  icono?: string | null;
}
