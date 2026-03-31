// Phase 5 — Table domain types

export type TableStatus =
  | 'libre'
  | 'ocupada'
  | 'pedido_solicitado'
  | 'pedido_cumplido'
  | 'cuenta'
  | 'inactiva';

export interface Table {
  id: number;
  sector_id: number;
  numero: number;
  codigo: string | null;
  capacidad: number;
  estado: TableStatus;
  version: number;
  status_changed_at: string | null;
  occupied_at: string | null;
  order_requested_at: string | null;
  order_fulfilled_at: string | null;
  check_requested_at: string | null;
  session_count: number;
}

export interface TableCreate {
  numero: number;
  capacidad: number;
  sector_id: number;
}

export interface TableBatchCreate {
  sector_id: number;
  cantidad: number;
  capacidad_base: number;
  numero_inicio?: number;
}

export interface TableUpdate {
  capacidad?: number;
  sector_id?: number;
}

export interface TableStatusUpdate {
  estado: TableStatus;
  version: number;
}
