
export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number?: string;
  profile_photo?: string;
  date_joined: string;
  last_login?: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  email_verified: boolean;
  two_factor_enabled: boolean;
  biometric_enabled: boolean;
  role?: string; // Optional, if you add custom roles
  age?: number;
  gender?: 'M' | 'F' | 'O';
  marital_status?: string;
  number_of_kids?: number;
  profession?: string;
  salary_range?: string;
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
  message?: string;
}

export interface TwoFactorRequiredResponse {
  requires_2fa: true;
  temp_token: string;
  email: string;
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

export interface TwoFactorSetup {
  secret: string;
  qr_code: string; // Base64 encoded QR code image
}

export interface TwoFactorConfirmResponse {
  message: string;
  backup_codes: string[];
}

export interface BiometricDevice {
  id: number;
  device_type: string;
  device_id: string;
  device_name: string;
  credential_id: string;
  is_active: boolean;
  created_at: string;
  last_used?: string;
}

export interface BiometricChallenge {
  challenge: string;
  credential_id: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  uid: string;
  token: string;
  new_password: string;
}

export interface TokenRefreshResponse {
  access: string;
  refresh?: string; // Optional, returned if rotation is enabled
}

export interface ErrorResponse {
  error?: string;
  detail?: string;
  [key: string]: any; // For field-specific errors
}