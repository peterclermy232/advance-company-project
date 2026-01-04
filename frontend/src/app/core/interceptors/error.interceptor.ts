import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';
import { NotificationService } from '../services/notification.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const notificationService = inject(NotificationService);

  return next(req).pipe(
    catchError((error) => {
      if (error.status === 401) {
        // Unauthorized - redirect to login
        localStorage.clear();
        router.navigate(['/auth/login']);
        notificationService.error('Session expired. Please login again.');
      } else if (error.status === 403) {
        notificationService.error('You do not have permission to perform this action.');
      } else if (error.status === 404) {
        notificationService.error('Resource not found.');
      } else if (error.status === 500) {
        notificationService.error('Server error. Please try again later.');
      } else if (error.error?.message) {
        notificationService.error(error.error.message);
      }

      return throwError(() => error);
    })
  );
};
