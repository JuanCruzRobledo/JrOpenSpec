// Restaurant types matching the real backend API (Spanish field names)

export interface Restaurant {
  id: number;
  nombre: string;
  slug: string;
  descripcion: string | null;
  logo_url: string | null;
  banner_url: string | null;
  telefono: string | null;
  email: string | null;
  direccion: string | null;
}

export interface RestaurantUpdate {
  nombre?: string;
  slug?: string;
  descripcion?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  telefono?: string | null;
  email?: string | null;
  direccion?: string | null;
}
