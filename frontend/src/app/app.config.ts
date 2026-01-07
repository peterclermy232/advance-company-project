// app.config.ts
import { ApplicationConfig, provideZoneChangeDetection, APP_INITIALIZER } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
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
    // Initialize notification service on app startup
    {
      provide: APP_INITIALIZER,
      useFactory: initializeNotificationService,
      deps: [NotificationService, AuthService],
      multi: true
    }
  ]
};