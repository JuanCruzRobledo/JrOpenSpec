// Branch types matching the real backend API (Spanish field names)

export type BranchEstado = 'activo' | 'inactivo';

export interface Branch {
  id: number;
  nombre: string;
  direccion: string | null;
  telefono: string | null;
  email: string | null;
  imagen_url: string | null;
  horario_apertura: string | null;
  horario_cierre: string | null;
  estado: BranchEstado;
  orden: number;
  created_at: string;
  updated_at: string;
}

export interface BranchCreate {
  nombre: string;
  direccion?: string | null;
  telefono?: string | null;
  email?: string | null;
  imagen_url?: string | null;
  horario_apertura?: string | null;
  horario_cierre?: string | null;
  estado?: BranchEstado;
  orden?: number;
}

export interface BranchUpdate {
  nombre?: string;
  direccion?: string | null;
  telefono?: string | null;
  email?: string | null;
  imagen_url?: string | null;
  horario_apertura?: string | null;
  horario_cierre?: string | null;
  estado?: BranchEstado;
  orden?: number;
}
