import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap, catchError, throwError } from 'rxjs';
import { User, AuthResponse, LoginRequest, RegisterRequest } from '../models/user.model';
import { environment } from '../../environments/environment';
import { ToastService } from './toast.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);
  private toastService = inject(ToastService);
  
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();
  
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_KEY = 'refresh_token';
  private readonly USER_KEY = 'current_user';

  constructor() {
    this.loadUserFromStorage();
  }

  private loadUserFromStorage(): void {
    const userJson = localStorage.getItem(this.USER_KEY);
    if (userJson) {
      try {
        const user = JSON.parse(userJson);
        this.currentUserSubject.next(user);
      } catch (error) {
        console.error('Error parsing user data:', error);
        this.clearStorage();
      }
    }
  }

  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/login/`, credentials)
      .pipe(
        tap(response => {
          if ((response as any).requires_2fa) {
            this.toastService.info('Please enter your 2FA code');
            sessionStorage.setItem('temp_token', (response as any).temp_token);
            sessionStorage.setItem('temp_email', (response as any).email);
            return;
          }
          
          this.handleAuthResponse(response);
          this.toastService.success(`Welcome back, ${response.user.full_name}! 👋`);
        }),
        catchError(error => {
          const message = error.error?.error || 
                         error.error?.detail || 
                         'Invalid email or password';
          this.toastService.error(message);
          return throwError(() => error);
        })
      );
  }

  register(data: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/register/`, data)
      .pipe(
        tap(response => {
          this.handleAuthResponse(response);
          this.toastService.success(`Account created successfully! Welcome, ${response.user.full_name}! 🎉`);
        }),
        catchError(error => {
          const errorMessage = error.error?.email?.[0] || 
                             error.error?.phone_number?.[0] || 
                             error.error?.error ||
                             'Registration failed. Please check your information.';
          this.toastService.error(errorMessage);
          return throwError(() => error);
        })
      );
  }

  verifyEmail(email: string, token: string): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/verify-email/`, { email, token })
      .pipe(
        tap(() => {
          this.toastService.success('Email verified successfully! ✓');
        }),
        catchError(error => {
          const message = error.error?.error || 'Email verification failed';
          this.toastService.error(message);
          return throwError(() => error);
        })
      );
  }

  resendVerification(email: string): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/resend-verification/`, { email })
      .pipe(
        tap(() => {
          this.toastService.success('Verification email sent! Check your inbox.');
        }),
        catchError(error => {
          this.toastService.error('Failed to send verification email');
          return throwError(() => error);
        })
      );
  }

  verify2FA(code: string, isBackupCode: boolean = false): Observable<AuthResponse> {
    const temp_token = sessionStorage.getItem('temp_token');
    const email = sessionStorage.getItem('temp_email');

    if (!temp_token || !email) {
      this.toastService.error('Session expired. Please login again.');
      return throwError(() => new Error('No temp token'));
    }

    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/verify-2fa/`, {
      temp_token,
      email,
      code,
      is_backup_code: isBackupCode
    }).pipe(
      tap(response => {
        this.handleAuthResponse(response);
        sessionStorage.removeItem('temp_token');
        sessionStorage.removeItem('temp_email');
        this.toastService.success('2FA verified successfully! ✓');
      }),
      catchError(error => {
        const message = error.error?.error || 'Invalid verification code';
        this.toastService.error(message);
        return throwError(() => error);
      })
    );
  }

  forgotPassword(email: string): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/forgot-password/`, { email })
      .pipe(
        tap(() => {
          this.toastService.success('Password reset link sent to your email!');
        }),
        catchError(error => {
          this.toastService.error('Failed to send reset link');
          return throwError(() => error);
        })
      );
  }

  resetPasswordConfirm(uid: string, token: string, newPassword: string): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/reset-password-confirm/`, {
      uid,
      token,
      new_password: newPassword
    }).pipe(
      tap(() => {
        this.toastService.success('Password reset successfully! Please login.');
        this.router.navigate(['/auth/login']);
      }),
      catchError(error => {
        const message = error.error?.error || 'Password reset failed';
        this.toastService.error(message);
        return throwError(() => error);
      })
    );
  }

  // ==================== User Profile Management ====================
  
  getUserProfile(userId: number): Observable<User> {
    return this.http.get<User>(`${environment.apiUrl}/auth/users/${userId}/`)
      .pipe(
        tap(user => {
          if (this.getCurrentUser()?.id === userId) {
            localStorage.setItem(this.USER_KEY, JSON.stringify(user));
            this.currentUserSubject.next(user);
          }
        }),
        catchError(error => {
          this.toastService.error('Failed to load user profile');
          return throwError(() => error);
        })
      );
  }

  updateProfile(userId: number, data: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${environment.apiUrl}/auth/users/${userId}/`, data)
      .pipe(
        tap(user => {
          localStorage.setItem(this.USER_KEY, JSON.stringify(user));
          this.currentUserSubject.next(user);
          this.toastService.success('Profile updated successfully! ✓');
        }),
        catchError(error => {
          this.toastService.error('Failed to update profile. Please try again.');
          return throwError(() => error);
        })
      );
  }

  updateProfileWithPhoto(formData: FormData): Observable<User> {
    const user = this.getCurrentUser();
    if (!user) {
      return throwError(() => new Error('No authenticated user'));
    }

    return this.http.patch<User>(
      `${environment.apiUrl}/auth/users/${user.id}/`,
      formData
    ).pipe(
      tap(user => {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        this.currentUserSubject.next(user);
        this.toastService.success('Profile updated successfully! ✓');
      }),
      catchError(error => {
        this.toastService.error('Failed to update profile');
        return throwError(() => error);
      })
    );
  }

  // ==================== Password Management ====================
  
  changePassword(data: { current_password: string; new_password: string; confirm_password: string }): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/users/change_password/`, data)
      .pipe(
        tap(() => {
          this.toastService.success('Password changed successfully! ✓');
        }),
        catchError(error => {
          this.toastService.error('Failed to change password');
          return throwError(() => error);
        })
      );
  }

  // ==================== Two-Factor Authentication ====================
  
  enable2FA(): Observable<{ secret: string; qr_code: string }> {
    return this.http.post<{ secret: string; qr_code: string }>(
      `${environment.apiUrl}/auth/users/enable_2fa/`, 
      {}
    ).pipe(
      catchError(error => {
        this.toastService.error('Failed to enable 2FA');
        return throwError(() => error);
      })
    );
  }

  confirm2FA(code: string): Observable<{ message: string; backup_codes: string[] }> {
    return this.http.post<{ message: string; backup_codes: string[] }>(
      `${environment.apiUrl}/auth/users/confirm_2fa/`,
      { code }
    ).pipe(
      tap(response => {
        this.toastService.success('2FA enabled successfully! ✓');
        const currentUser = this.getCurrentUser();
        if (currentUser) {
          currentUser.two_factor_enabled = true;
          localStorage.setItem(this.USER_KEY, JSON.stringify(currentUser));
          this.currentUserSubject.next(currentUser);
        }
      }),
      catchError(error => {
        const message = error.error?.error || 'Invalid verification code';
        this.toastService.error(message);
        return throwError(() => error);
      })
    );
  }

  disable2FA(password: string): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/users/disable_2fa/`, { password })
      .pipe(
        tap(() => {
          this.toastService.success('2FA disabled successfully');
          const currentUser = this.getCurrentUser();
          if (currentUser) {
            currentUser.two_factor_enabled = false;
            localStorage.setItem(this.USER_KEY, JSON.stringify(currentUser));
            this.currentUserSubject.next(currentUser);
          }
        }),
        catchError(error => {
          this.toastService.error('Failed to disable 2FA');
          return throwError(() => error);
        })
      );
  }

  regenerateBackupCodes(): Observable<{ backup_codes: string[] }> {
    return this.http.get<{ backup_codes: string[] }>(`${environment.apiUrl}/auth/users/regenerate_backup_codes/`)
      .pipe(
        tap(() => {
          this.toastService.success('New backup codes generated');
        }),
        catchError(error => {
          this.toastService.error('Failed to regenerate backup codes');
          return throwError(() => error);
        })
      );
  }

  // ==================== Biometric Authentication ====================
  
  registerBiometric(data: {
    device_type: string;
    device_id: string;
    device_name: string;
    public_key: string;
  }): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/users/register_biometric/`, data)
      .pipe(
        tap(() => {
          this.toastService.success('Biometric device registered successfully! ✓');
          const currentUser = this.getCurrentUser();
          if (currentUser) {
            currentUser.biometric_enabled = true;
            localStorage.setItem(this.USER_KEY, JSON.stringify(currentUser));
            this.currentUserSubject.next(currentUser);
          }
        }),
        catchError(error => {
          this.toastService.error('Failed to register biometric device');
          return throwError(() => error);
        })
      );
  }

  getBiometricDevices(): Observable<any[]> {
    return this.http.get<any[]>(`${environment.apiUrl}/auth/users/biometric_devices/`)
      .pipe(
        catchError(error => {
          this.toastService.error('Failed to load biometric devices');
          return throwError(() => error);
        })
      );
  }

  removeBiometricDevice(deviceId: string): Observable<any> {
    const user = this.getCurrentUser();
    if (!user) {
      return throwError(() => new Error('No authenticated user'));
    }

    return this.http.delete(`${environment.apiUrl}/auth/users/${user.id}/biometric-devices/${deviceId}/`)
      .pipe(
        tap(() => {
          this.toastService.success('Biometric device removed');
        }),
        catchError(error => {
          this.toastService.error('Failed to remove device');
          return throwError(() => error);
        })
      );
  }

  // ==================== Account Management ====================
  
  deleteAccount(data: { password: string; confirmation: string }): Observable<any> {
    return this.http.delete(`${environment.apiUrl}/auth/users/delete_account/`, { body: data })
      .pipe(
        tap(() => {
          this.toastService.success('Account deleted successfully');
        }),
        catchError(error => {
          this.toastService.error('Failed to delete account');
          return throwError(() => error);
        })
      );
  }

  // ==================== Token Management ====================
  
  refreshToken(): Observable<any> {
    const refresh = this.getRefreshToken();
    if (!refresh) {
      return throwError(() => new Error('No refresh token'));
    }

    return this.http.post(`${environment.apiUrl}/token/refresh/`, { refresh })
      .pipe(
        tap((response: any) => {
          localStorage.setItem(this.TOKEN_KEY, response.access);
          if (response.refresh) {
            localStorage.setItem(this.REFRESH_KEY, response.refresh);
          }
        }),
        catchError(error => {
          this.logout();
          return throwError(() => error);
        })
      );
  }

  verifyToken(token?: string): Observable<any> {
    const tokenToVerify = token || this.getToken();
    return this.http.post(`${environment.apiUrl}/token/verify/`, { 
      token: tokenToVerify 
    });
  }

  // ==================== Helper Methods ====================
  
  private handleAuthResponse(response: AuthResponse): void {
    localStorage.setItem(this.TOKEN_KEY, response.tokens.access);
    localStorage.setItem(this.REFRESH_KEY, response.tokens.refresh);
    localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
    this.currentUserSubject.next(response.user);
  }

  logout(): void {
    this.clearStorage();
    this.toastService.info('Logged out successfully. See you soon! 👋');
    this.router.navigate(['/auth/login']);
  }

  private clearStorage(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem(this.USER_KEY);
    sessionStorage.removeItem('temp_token');
    sessionStorage.removeItem('temp_email');
    this.currentUserSubject.next(null);
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  isAdmin(): boolean {
    const user = this.getCurrentUser();
    return !!(user && (user.role === 'admin' || user.is_staff));
  }

  isEmailVerified(): boolean {
    return !!this.getCurrentUser()?.email_verified;
  }

  is2FAEnabled(): boolean {
    return !!this.getCurrentUser()?.two_factor_enabled;
  }

  isBiometricEnabled(): boolean {
    return !!this.getCurrentUser()?.biometric_enabled;
  }

  uploadProfilePhoto(file: File): Observable<User> {
  const formData = new FormData();
  formData.append('profile_photo', file);

  return this.http.post<any>(
    `${environment.apiUrl}/auth/users/upload_profile_photo/`,
    formData
  ).pipe(
    tap(response => {
      const user = response.user;
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      this.currentUserSubject.next(user);
      this.toastService.success('Profile photo updated successfully! ✓');
    }),
    catchError(error => {
      const message = error.error?.error || 'Failed to upload photo';
      this.toastService.error(message);
      return throwError(() => error);
    })
  );
}

deleteProfilePhoto(): Observable<any> {
  return this.http.delete(`${environment.apiUrl}/auth/users/delete_profile_photo/`)
    .pipe(
      tap(() => {
        const currentUser = this.getCurrentUser();
        if (currentUser) {
          currentUser.profile_photo = null;
          currentUser.profile_photo_url = null;
          localStorage.setItem(this.USER_KEY, JSON.stringify(currentUser));
          this.currentUserSubject.next(currentUser);
        }
        this.toastService.success('Profile photo deleted successfully');
      }),
      catchError(error => {
        this.toastService.error('Failed to delete photo');
        return throwError(() => error);
      })
    );
}
}