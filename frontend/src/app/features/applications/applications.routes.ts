import { Routes } from '@angular/router';

export const APPLICATIONS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./application-list/application-list.component').then(m => m.ApplicationListComponent)
  },
  {
    path: 'new',
    loadComponent: () => import('./application-form/application-form.component').then(m => m.ApplicationFormComponent)
  }
];