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
    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/users/login/`, credentials)
      .pipe(
        tap(response => {
          this.handleAuthResponse(response);
          this.toastService.success(`Welcome back, ${response.user.full_name}! 👋`);
        }),
        catchError(error => {
          const message = error.error?.detail || 
                         error.error?.non_field_errors?.[0] || 
                         'Invalid email or password';
          this.toastService.error(message);
          return throwError(() => error);
        })
      );
  }

  register(data: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/users/register/`, data)
      .pipe(
        tap(response => {
          this.handleAuthResponse(response);
          this.toastService.success(`Account created successfully! Welcome, ${response.user.full_name}! 🎉`);
        }),
        catchError(error => {
          const errorMessage = error.error?.email?.[0] || 
                             error.error?.phone_number?.[0] || 
                             error.error?.detail ||
                             'Registration failed. Please check your information.';
          this.toastService.error(errorMessage);
          return throwError(() => error);
        })
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
    this.toastService.info('Logged out successfully. See you soon! 👋');
    this.router.navigate(['/auth/login']);
  }

  private clearStorage(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem(this.USER_KEY);
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
    return user?.role === 'admin';
  }

  refreshToken(): Observable<any> {
    const refresh = this.getRefreshToken();
    return this.http.post(`${environment.apiUrl}/token/refresh/`, { refresh })
      .pipe(
        tap((response: any) => {
          localStorage.setItem(this.TOKEN_KEY, response.access);
        })
      );
  }

  getMe(): Observable<User> {
    return this.http.get<User>(`${environment.apiUrl}/auth/users/me/`)
      .pipe(
        tap(user => {
          localStorage.setItem(this.USER_KEY, JSON.stringify(user));
          this.currentUserSubject.next(user);
        })
      );
  }

  updateProfile(data: Partial<User>): Observable<User> {
    return this.http.put<User>(`${environment.apiUrl}/auth/users/update_profile/`, data)
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
}