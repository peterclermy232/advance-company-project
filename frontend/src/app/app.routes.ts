import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard]
  },
  {
    path: 'financial',
    loadComponent: () => import('./features/financial/financial.component').then(m => m.FinancialComponent),
    canActivate: [authGuard]
  },
  {
    path: 'deposit-form',
    loadComponent: () => import('./features/financial/components/deposit-form/deposit-form.component').then(m => m.DepositFormComponent),
    canActivate: [authGuard]
  },
  {
    path: 'beneficiary',
    loadChildren: () => import('./features/beneficiary/beneficiary.routes').then(m => m.BENEFICIARY_ROUTES),
    canActivate: [authGuard]
  },
  {
    path: 'documents',
    loadChildren: () => import('./features/documents/documents.routes').then(m => m.DOCUMENTS_ROUTES),
    canActivate: [authGuard]
  },
  {
    path: 'applications',
    loadChildren: () => import('./features/applications/applications.routes').then(m => m.APPLICATIONS_ROUTES),
    canActivate: [authGuard]
  },
  {
    path: 'reports',
    loadComponent: () => import('./features/reports/reports.component').then(m => m.ReportsComponent),
    canActivate: [authGuard]
  },
  {
    path: 'settings',
    loadComponent: () => import('./features/settings/settings.component').then(m => m.SettingsComponent),
    canActivate: [authGuard]
  },
  {
    path: 'support',
    loadComponent: () => import('./features/support/support.component').then(m => m.SupportComponent),
    canActivate: [authGuard]
  },
  {
  path: 'notifications',
  loadComponent: () => import('./features/notifications/notifications.component')
    .then(m => m.NotificationsComponent),
  canActivate: [authGuard]
},
{
  path: 'admin/analytics',
  loadComponent: () => import('./features/admin/admin-analytics/admin-analytics.component')
    .then(m => m.AdminAnalyticsComponent),
  canActivate: [authGuard, adminGuard]
},
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];