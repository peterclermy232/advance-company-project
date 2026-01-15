import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const token = authService.getToken();

  // List of public endpoints that don't need authentication
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

  // Check if the request is to a public endpoint
  const isPublicEndpoint = publicEndpoints.some(endpoint => 
    req.url.includes(endpoint)
  );

  // Add token to request if authenticated and not a public endpoint
  if (token && !isPublicEndpoint) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  // Handle the request and catch errors
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle 401 Unauthorized errors (token expired)
      if (error.status === 401 && !req.url.includes('/token/refresh/')) {
        // Try to refresh the token
        return authService.refreshToken().pipe(
          switchMap(() => {
            // Retry the original request with new token
            const newToken = authService.getToken();
            const retryReq = req.clone({
              setHeaders: {
                Authorization: `Bearer ${newToken}`
              }
            });
            return next(retryReq);
          }),
          catchError(refreshError => {
            // If refresh fails, logout user
            authService.logout();
            router.navigate(['/auth/login']);
            return throwError(() => refreshError);
          })
        );
      }

      // Handle 403 Forbidden errors
      if (error.status === 403) {
        console.error('Access forbidden:', error);
        // Optionally redirect to a forbidden page or show a message
      }

      // Handle 429 Too Many Requests (rate limiting)
      if (error.status === 429) {
        console.error('Rate limit exceeded:', error);
        // You can show a toast message here
      }

      // Pass through other errors
      return throwError(() => error);
    })
  );
};