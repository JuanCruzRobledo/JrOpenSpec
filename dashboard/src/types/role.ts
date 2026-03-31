// Phase 5 — Role domain types

export interface RolePermissions {
  rol: string;
  etiqueta: string;
  permisos: string[];
}

export interface RolesMatrix {
  roles: RolePermissions[];
}
