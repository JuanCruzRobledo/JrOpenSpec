// Auth-related types matching the real backend schemas

/** POST /api/auth/login response */
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

/** GET /api/auth/me response */
export interface UserProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  tenant_id: number;
  branch_ids: number[];
  roles: string[];
  is_superadmin: boolean;
}

/** Login request payload */
export interface LoginPayload {
  email: string;
  password: string;
}
