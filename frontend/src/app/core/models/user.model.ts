export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number?: string;

  age?: number;
  gender?: string;
  marital_status?: string;
  profession?: string;
  
  profile_photo?: string | null;
  profile_photo_url?: string | null;

  date_joined: string;
  last_login?: string;

  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;

  email_verified: boolean;
  two_factor_enabled: boolean;
  biometric_enabled: boolean;

  role?: string;
  activity_status: string;

  created_at: string;
  updated_at: string;
}

/* ================= AUTH ================= */

export interface AuthResponse {
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
  message?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
}
