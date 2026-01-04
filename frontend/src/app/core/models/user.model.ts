export interface User {
  id: number;
  email: string;
  phone_number: string;
  full_name: string;
  role: 'user' | 'admin';
  age?: number;
  gender?: 'M' | 'F' | 'O';
  marital_status?: string;
  number_of_kids?: number;
  profession?: string;
  salary_range?: string;
  profile_photo?: string;
  identity_document?: string;
  activity_status: string;
  spouse_name?: string;
  spouse_age?: number;
  spouse_profession?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  phone_number: string;
  full_name: string;
  password: string;
  password_confirm: string;
  role?: string;
}