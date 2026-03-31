// Phase 5 — Sector domain types

export interface Sector {
  id: number;
  nombre: string;
  tipo: string;
  prefijo: string;
  capacidad: number | null;
  estado: string;
  cantidad_mesas: number;
  mesas_disponibles: number;
  created_at: string;
}

export interface SectorCreate {
  nombre: string;
  tipo: string;
  capacidad?: number;
}

export interface SectorUpdate {
  nombre?: string;
  tipo?: string;
  capacidad?: number;
}
