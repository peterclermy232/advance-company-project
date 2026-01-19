import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const token = authService.getToken();

  const publicEndpoints = [
    '/auth/login/',
    '/auth/register/',
    '/auth/verify-email/',
    '/auth/resend-verification/',
    '/auth/verify-2fa/',
    '/auth/forgot-password/',
    '/auth/reset-password-confirm/',
    '/auth/biometric-challenge/',
    '/auth/biometric-login/',
    '/auth/test/',
    '/token/refresh/',
    '/token/verify/'
  ];

  const isPublicEndpoint = publicEndpoints.some(endpoint =>
    req.url.includes(endpoint)
  );

  // Attach token ONLY for protected endpoints
  if (token && !isPublicEndpoint) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {

      // 🚫 DO NOT refresh token for public/auth endpoints
      if (error.status === 401 && !isPublicEndpoint && !req.url.includes('/token/refresh/')) {
        return authService.refreshToken().pipe(
          switchMap(() => {
            const newToken = authService.getToken();
            return next(
              req.clone({
                setHeaders: {
                  Authorization: `Bearer ${newToken}`
                }
              })
            );
          }),
          catchError(refreshError => {
            authService.logout();
            return throwError(() => refreshError);
          })
        );
      }

      // Optional handlers
      if (error.status === 403) {
        console.error('Access forbidden:', error);
      }

      if (error.status === 429) {
        console.error('Rate limit exceeded:', error);
      }

      // ✅ Let AuthService handle backend toast messages
      return throwError(() => error);
    })
  );
};
