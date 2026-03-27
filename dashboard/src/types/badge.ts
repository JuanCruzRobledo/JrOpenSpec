// Badge types matching the real backend API (Spanish field names)

export interface Badge {
  id: number;
  codigo: string;
  nombre: string;
  color: string;
  icono: string | null;
  es_sistema: boolean;
  created_at: string;
  updated_at: string;
}

export interface BadgeCreate {
  codigo: string;
  nombre: string;
  color: string;
  icono?: string | null;
}

export interface BadgeUpdate {
  nombre?: string;
  color?: string;
  icono?: string | null;
}
