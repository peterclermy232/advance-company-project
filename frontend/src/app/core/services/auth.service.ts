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

  // ✅ Login - Matches /api/auth/login/
  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/login/`, credentials)
      .pipe(
        tap(response => {
          // Check if 2FA is required
          if ((response as any).requires_2fa) {
            this.toastService.info('Please enter your 2FA code');
            // Store temp token for 2FA verification
            sessionStorage.setItem('temp_token', (response as any).temp_token);
            sessionStorage.setItem('temp_email', (response as any).email);
            return;
          }
          
          this.handleAuthResponse(response);
          this.toastService.success(`Welcome back, ${response.user.first_name}! 👋`);
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

  // ✅ Register - Matches /api/auth/register/
  register(data: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/register/`, data)
      .pipe(
        tap(response => {
          this.handleAuthResponse(response);
          this.toastService.success(`Account created successfully! Welcome, ${response.user.first_name}! 🎉`);
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

  // ✅ Verify Email - Matches /api/auth/verify-email/
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

  // ✅ Resend Verification - Matches /api/auth/resend-verification/
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

  // ✅ Verify 2FA - Matches /api/auth/verify-2fa/
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

  // ✅ Forgot Password - Matches /api/auth/forgot-password/
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

  // ✅ Reset Password Confirm - Matches /api/auth/reset-password-confirm/
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

  // ✅ Enable 2FA - Matches /api/auth/users/enable_2fa/
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

  // ✅ Confirm 2FA Setup - Matches /api/auth/users/confirm_2fa/
  confirm2FA(code: string): Observable<{ message: string; backup_codes: string[] }> {
    return this.http.post<{ message: string; backup_codes: string[] }>(
      `${environment.apiUrl}/auth/users/confirm_2fa/`,
      { code }
    ).pipe(
      tap(response => {
        this.toastService.success('2FA enabled successfully! ✓');
        // Update current user
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

  // ✅ Register Biometric Device - Matches /api/auth/users/register_biometric/
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
          // Update current user
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

  // ✅ Get User Profile - Matches /api/auth/users/<id>/
  getUserProfile(userId: number): Observable<User> {
    return this.http.get<User>(`${environment.apiUrl}/auth/users/${userId}/`)
      .pipe(
        tap(user => {
          // Update current user if it's the same user
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

  // ✅ Update User Profile - Matches /api/auth/users/<id>/
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

  // Update profile with photo (FormData)
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
    })
  );
}


  // ✅ Refresh Token - Matches /api/token/refresh/
  refreshToken(): Observable<any> {
    const refresh = this.getRefreshToken();
    if (!refresh) {
      return throwError(() => new Error('No refresh token'));
    }

    return this.http.post(`${environment.apiUrl}/token/refresh/`, { refresh })
      .pipe(
        tap((response: any) => {
          localStorage.setItem(this.TOKEN_KEY, response.access);
          // Update refresh token if rotation is enabled
          if (response.refresh) {
            localStorage.setItem(this.REFRESH_KEY, response.refresh);
          }
        }),
        catchError(error => {
          // If refresh fails, logout user
          this.logout();
          return throwError(() => error);
        })
      );
  }

  // ✅ Verify Token - Matches /api/token/verify/
  verifyToken(token?: string): Observable<any> {
    const tokenToVerify = token || this.getToken();
    return this.http.post(`${environment.apiUrl}/token/verify/`, { 
      token: tokenToVerify 
    });
  }

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
  // Helper method to check if email is verified
  isEmailVerified(): boolean {
  return !!this.getCurrentUser()?.email_verified;
}

  // Helper method to check if 2FA is enabled
  is2FAEnabled(): boolean {
  return !!this.getCurrentUser()?.two_factor_enabled;
}

  // Helper method to check if biometric is enabled
  isBiometricEnabled(): boolean {
  return !!this.getCurrentUser()?.biometric_enabled;
}
}