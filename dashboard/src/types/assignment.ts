// Phase 5 — Assignment domain types

export interface AssignmentMozo {
  id: number;
  nombre_completo: string;
}

export interface AssignmentSector {
  id: number;
  nombre: string;
}

export interface Assignment {
  id: number;
  mozo: AssignmentMozo;
  sector: AssignmentSector;
  turno: string;
  fecha: string;
}

export interface AssignmentBulkItem {
  mozo_id: number;
  sector_id: number;
}

export interface AssignmentBulkCreate {
  fecha: string;
  turno: string;
  asignaciones: AssignmentBulkItem[];
}

export interface AssignmentsByShift {
  morning: Assignment[];
  afternoon: Assignment[];
  night: Assignment[];
}
