import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap, catchError, throwError, map } from 'rxjs';
import { User, AuthResponse, LoginRequest, RegisterRequest } from '../models/user.model';
import { environment } from '../../environments/environment';
import { ToastService } from './toast.service';

// Backend response interface
interface BackendResponse<T = any> {
  success: boolean;
  message: string;
  toast_type: 'success' | 'error' | 'warning' | 'info';
  data?: T;
  errors?: any;
}

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

  /**
   * Helper method to show backend toast message
   */
  private showBackendToast(response: BackendResponse) {
    
    if (!response.message) {
      console.warn(' No message in response - skipping toast');
      return;
    }
    
    try {
      switch (response.toast_type) {
        case 'success':
          this.toastService.success(response.message);
          break;
        case 'error':
          this.toastService.error(response.message);
          break;
        case 'warning':
          this.toastService.warning(response.message);
          break;
        case 'info':
          this.toastService.info(response.message);
          break;
        default:
          this.toastService.info(response.message);
      }
    } catch (error) {
      console.error('ERROR showing toast:', error);
    }
  }

  /**
   * Helper method to handle backend error responses
   */
  private handleBackendError(error: any): Observable<never> {
    
    // Check if error.error exists and is an object
    if (error.error && typeof error.error === 'object') {
      // Check for backend response format with message and toast_type
      if (error.error.message && error.error.toast_type) {
        const backendError = error.error as BackendResponse;
        this.showBackendToast(backendError);
      }
      // Check for Django Rest Framework detail format
      else if (error.error.detail) {
        this.toastService.error(error.error.detail);
      }
      // Check for generic error field
      else if (error.error.error) {
        this.toastService.error(error.error.error);
      }
      else {
        this.toastService.error('An error occurred. Please try again.');
      }
    }
    // If error.error is a string
    else if (typeof error.error === 'string') {
      this.toastService.error(error.error);
    }
    // Fallback to error.message
    else if (error.message) {
      this.toastService.error(error.message);
    }
    // Final fallback
    else {
      this.toastService.error('An unexpected error occurred');
    }
    
    console.log('🔴 ====================================');
    return throwError(() => error);
  }

  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http
      .post<BackendResponse<AuthResponse>>(
        `${environment.apiUrl}/auth/login/`,
        credentials
      )
      .pipe(
        tap(response => {
          this.showBackendToast(response);

          if ((response.data as any)?.requires_2fa) {
            sessionStorage.setItem('temp_token', (response.data as any).temp_token);
            sessionStorage.setItem('temp_email', (response.data as any).email);
          }

          if (response.data) {
            this.handleAuthResponse(response.data);
          }
          console.log('🟢 ====================================');
        }),
        map(response => response.data as AuthResponse),
        catchError(error => {
          return this.handleBackendError(error);
        })
      );
  }

  register(data: RegisterRequest | FormData): Observable<AuthResponse> {
  return this.http
    .post<BackendResponse<AuthResponse>>(
      `${environment.apiUrl}/auth/register/`,
      data
    )
    .pipe(
      tap(response => {
        this.showBackendToast(response);

        if (response.success && response.data) {
          this.handleAuthResponse(response.data);
        }
      }),
      map(response => response.data as AuthResponse),
      catchError((error: HttpErrorResponse) => {
        // PASS BACKEND ERROR CLEANLY
        return throwError(() => error.error);
      })
    );
}


  verifyEmail(email: string, token: string): Observable<any> {
    return this.http.post<BackendResponse>(`${environment.apiUrl}/auth/verify-email/`, { email, token })
      .pipe(
        tap(response => this.showBackendToast(response)),
        catchError(error => this.handleBackendError(error))
      );
  }

  resendVerification(email: string): Observable<any> {
    return this.http.post<BackendResponse>(`${environment.apiUrl}/auth/resend-verification/`, { email })
      .pipe(
        tap(response => this.showBackendToast(response)),
        catchError(error => this.handleBackendError(error))
      );
  }

  verify2FA(code: string, isBackupCode = false): Observable<AuthResponse> {
    const temp_token = sessionStorage.getItem('temp_token');
    const email = sessionStorage.getItem('temp_email');

    if (!temp_token || !email) {
      return throwError(() => new Error('No temp token'));
    }

    return this.http
      .post<BackendResponse<AuthResponse>>(
        `${environment.apiUrl}/auth/verify-2fa/`,
        { temp_token, email, code, is_backup_code: isBackupCode }
      )
      .pipe(
        tap(response => {
          this.showBackendToast(response);
          if (response.data) {
            this.handleAuthResponse(response.data);
            sessionStorage.removeItem('temp_token');
            sessionStorage.removeItem('temp_email');
          }
        }),
        map(response => response.data as AuthResponse),
        catchError(error => this.handleBackendError(error))
      );
  }

  forgotPassword(email: string): Observable<any> {
    return this.http.post<BackendResponse>(`${environment.apiUrl}/auth/forgot-password/`, { email })
      .pipe(
        tap(response => this.showBackendToast(response)),
        catchError(error => this.handleBackendError(error))
      );
  }

  resetPasswordConfirm(uid: string, token: string, newPassword: string): Observable<any> {
    return this.http.post<BackendResponse>(`${environment.apiUrl}/auth/reset-password-confirm/`, {
      uid,
      token,
      new_password: newPassword
    }).pipe(
      tap(response => {
        this.showBackendToast(response);
        this.router.navigate(['/auth/login']);
      }),
      catchError(error => this.handleBackendError(error))
    );
  }

  getUserProfile(userId: number): Observable<User> {
    return this.http.get<BackendResponse<User>>(`${environment.apiUrl}/auth/users/${userId}/`)
      .pipe(
        tap(response => {
          if (response.data && this.getCurrentUser()?.id === userId) {
            localStorage.setItem(this.USER_KEY, JSON.stringify(response.data));
            this.currentUserSubject.next(response.data);
          }
        }),
        map(response => response.data as User),
        catchError(error => this.handleBackendError(error))
      );
  }

  updateProfile(userId: number, data: Partial<User>): Observable<User> {
    return this.http.patch<BackendResponse<User>>(`${environment.apiUrl}/auth/users/${userId}/`, data)
      .pipe(
        tap(response => {
          this.showBackendToast(response);
          if (response.data) {
            localStorage.setItem(this.USER_KEY, JSON.stringify(response.data));
            this.currentUserSubject.next(response.data);
          }
        }),
        map(response => response.data as User),
        catchError(error => this.handleBackendError(error))
      );
  }

  updateProfileWithPhoto(formData: FormData): Observable<User> {
    const user = this.getCurrentUser();
    if (!user) {
      return throwError(() => new Error('No authenticated user'));
    }

    return this.http.patch<BackendResponse<User>>(
      `${environment.apiUrl}/auth/users/${user.id}/`,
      formData
    ).pipe(
      tap(response => {
        this.showBackendToast(response);
        if (response.data) {
          localStorage.setItem(this.USER_KEY, JSON.stringify(response.data));
          this.currentUserSubject.next(response.data);
        }
      }),
      map(response => response.data as User),
      catchError(error => this.handleBackendError(error))
    );
  }

  changePassword(data: { current_password: string; new_password: string; confirm_password: string }): Observable<any> {
    return this.http.post<BackendResponse>(`${environment.apiUrl}/auth/users/change_password/`, data)
      .pipe(
        tap(response => this.showBackendToast(response)),
        catchError(error => this.handleBackendError(error))
      );
  }

  enable2FA(): Observable<{ secret: string; qr_code: string }> {
    return this.http.post<BackendResponse<{ secret: string; qr_code: string }>>(
      `${environment.apiUrl}/auth/users/enable_2fa/`, 
      {}
    ).pipe(
      tap(response => {
        if (response.message) {
          this.showBackendToast(response);
        }
      }),
      map(response => response.data as { secret: string; qr_code: string }),
      catchError(error => this.handleBackendError(error))
    );
  }

  confirm2FA(code: string): Observable<{ message: string; backup_codes: string[] }> {
    return this.http.post<BackendResponse<{ backup_codes: string[] }>>(
      `${environment.apiUrl}/auth/users/confirm_2fa/`,
      { code }
    ).pipe(
      tap(response => {
        this.showBackendToast(response);
        const currentUser = this.getCurrentUser();
        if (currentUser) {
          currentUser.two_factor_enabled = true;
          localStorage.setItem(this.USER_KEY, JSON.stringify(currentUser));
          this.currentUserSubject.next(currentUser);
        }
      }),
      map(response => ({
        message: response.message,
        backup_codes: response.data?.backup_codes || []
      })),
      catchError(error => this.handleBackendError(error))
    );
  }

  disable2FA(password: string): Observable<any> {
    return this.http.post<BackendResponse>(`${environment.apiUrl}/auth/users/disable_2fa/`, { password })
      .pipe(
        tap(response => {
          this.showBackendToast(response);
          const currentUser = this.getCurrentUser();
          if (currentUser) {
            currentUser.two_factor_enabled = false;
            localStorage.setItem(this.USER_KEY, JSON.stringify(currentUser));
            this.currentUserSubject.next(currentUser);
          }
        }),
        catchError(error => this.handleBackendError(error))
      );
  }

  regenerateBackupCodes(): Observable<{ backup_codes: string[] }> {
    return this.http.get<BackendResponse<{ backup_codes: string[] }>>(`${environment.apiUrl}/auth/users/regenerate_backup_codes/`)
      .pipe(
        tap(response => this.showBackendToast(response)),
        map(response => response.data as { backup_codes: string[] }),
        catchError(error => this.handleBackendError(error))
      );
  }

  registerBiometric(data: {
    device_type: string;
    device_id: string;
    device_name: string;
    public_key: string;
  }): Observable<any> {
    return this.http.post<BackendResponse>(`${environment.apiUrl}/auth/users/register_biometric/`, data)
      .pipe(
        tap(response => {
          this.showBackendToast(response);
          const currentUser = this.getCurrentUser();
          if (currentUser) {
            currentUser.biometric_enabled = true;
            localStorage.setItem(this.USER_KEY, JSON.stringify(currentUser));
            this.currentUserSubject.next(currentUser);
          }
        }),
        catchError(error => this.handleBackendError(error))
      );
  }

  getBiometricDevices(): Observable<any[]> {
    return this.http.get<BackendResponse<any[]>>(`${environment.apiUrl}/auth/users/biometric_devices/`)
      .pipe(
        map(response => response.data || []),
        catchError(error => this.handleBackendError(error))
      );
  }

  removeBiometricDevice(deviceId: string): Observable<any> {
    const user = this.getCurrentUser();
    if (!user) {
      return throwError(() => new Error('No authenticated user'));
    }

    return this.http.delete<BackendResponse>(`${environment.apiUrl}/auth/users/${user.id}/biometric-devices/${deviceId}/`)
      .pipe(
        tap(response => this.showBackendToast(response)),
        catchError(error => this.handleBackendError(error))
      );
  }

  deleteAccount(data: { password: string; confirmation: string }): Observable<any> {
    return this.http.delete<BackendResponse>(`${environment.apiUrl}/auth/users/delete_account/`, { body: data })
      .pipe(
        tap(response => this.showBackendToast(response)),
        catchError(error => this.handleBackendError(error))
      );
  }

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

  uploadProfilePhoto(file: File): Observable<User> {
    const formData = new FormData();
    formData.append('profile_photo', file);

    return this.http
      .post<BackendResponse<{ user: User }>>(
        `${environment.apiUrl}/auth/users/upload_profile_photo/`,
        formData
      )
      .pipe(
        tap(response => {
          this.showBackendToast(response);

          if (response.data?.user) {
            localStorage.setItem(
              this.USER_KEY,
              JSON.stringify(response.data.user)
            );
            this.currentUserSubject.next(response.data.user);
          }
        }),
        map(response => response.data!.user),
        catchError(error => this.handleBackendError(error))
      );
  }

  deleteProfilePhoto(): Observable<any> {
    return this.http.delete<BackendResponse>(`${environment.apiUrl}/auth/users/delete_profile_photo/`)
      .pipe(
        tap(response => {
          this.showBackendToast(response);
          const currentUser = this.getCurrentUser();
          if (currentUser) {
            currentUser.profile_photo = null;
            currentUser.profile_photo_url = null;
            localStorage.setItem(this.USER_KEY, JSON.stringify(currentUser));
            this.currentUserSubject.next(currentUser);
          }
        }),
        catchError(error => this.handleBackendError(error))
      );
  }

  private handleAuthResponse(response: AuthResponse): void {
    localStorage.setItem(this.TOKEN_KEY, response.tokens.access);
    localStorage.setItem(this.REFRESH_KEY, response.tokens.refresh);
    localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
    this.currentUserSubject.next(response.user);
  }

  logout(): void {
    this.clearStorage();
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
}