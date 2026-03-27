// Allergen types matching the real backend API (Spanish field names)

export type AllergenSeverity = 'low' | 'moderate' | 'severe' | 'life_threatening';
export type PresenceType = 'contains' | 'may_contain' | 'free_of';

export interface Allergen {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  icono: string | null;
  es_sistema: boolean;
  created_at: string;
  updated_at: string;
}

export interface AllergenCreate {
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  icono?: string | null;
}

export interface AllergenUpdate {
  nombre?: string;
  descripcion?: string | null;
  icono?: string | null;
}

export interface CrossReaction {
  id: number;
  alergeno_id: number;
  alergeno_relacionado_id: number;
  alergeno_nombre: string;
  alergeno_relacionado_nombre: string;
  descripcion: string;
  severidad: AllergenSeverity;
}

export interface CrossReactionCreate {
  alergeno_relacionado_id: number;
  descripcion: string;
  severidad: AllergenSeverity;
}

export interface ProductAllergen {
  alergeno_id: number;
  tipo_presencia: PresenceType;
  nivel_riesgo: AllergenSeverity;
  notas: string | null;
}

export interface ProductAllergenInput {
  alergeno_id: number;
  tipo_presencia: PresenceType;
  nivel_riesgo: AllergenSeverity;
  notas?: string | null;
}
