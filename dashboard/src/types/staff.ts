// Phase 5 — Staff domain types

export interface Staff {
  id: number;
  nombre_completo: string;
  email: string;
  rol: string | null;
  dni: string | null;
  fecha_contratacion: string | null;
  estado: string;
  created_at: string;
}

export interface StaffCreate {
  nombre_completo: string;
  email: string;
  password: string;
  rol: string;
  dni?: string;
  fecha_contratacion?: string;
}

export interface StaffUpdate {
  nombre_completo?: string;
  rol?: string;
  dni?: string;
  fecha_contratacion?: string;
  is_active?: boolean;
}
