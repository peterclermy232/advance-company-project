import {
  ApplicationConfig,
  provideZoneChangeDetection,
  APP_INITIALIZER,
  importProvidersFrom
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';

import { MAT_SNACK_BAR_DEFAULT_OPTIONS, MatSnackBarModule } from '@angular/material/snack-bar';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { NotificationService } from './core/services/notification.service';
import { AuthService } from './core/services/auth.service';

// Factory function to initialize notification service
export function initializeNotificationService(
  notificationService: NotificationService,
  authService: AuthService
) {
  return () => {
    // Only initialize if user is authenticated
    const currentUser = authService.currentUser$;
    if (currentUser) {
      console.log('App Initializer: Starting notification service');
      notificationService.initialize();
    } else {
      console.log('App Initializer: User not authenticated, skipping notification service');
    }
    return Promise.resolve();
  };
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([authInterceptor])
    ),

    // REQUIRED for Angular Material SnackBar
    provideAnimations(),
    importProvidersFrom(MatSnackBarModule),

    // Configure default toast position and duration
    {
      provide: MAT_SNACK_BAR_DEFAULT_OPTIONS,
      useValue: {
        horizontalPosition: 'right',
        verticalPosition: 'top',
        duration: 4000
      }
    },

    // Initialize notification service on app startup
    {
      provide: APP_INITIALIZER,
      useFactory: initializeNotificationService,
      deps: [NotificationService, AuthService],
      multi: true
    }
  ]
};
