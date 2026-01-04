import { Routes } from '@angular/router';

export const BENEFICIARY_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./beneficiary-list/beneficiary-list.component').then(m => m.BeneficiaryListComponent)
  },
  {
    path: 'add',
    loadComponent: () => import('./beneficiary-form/beneficiary-form.component').then(m => m.BeneficiaryFormComponent)
  },
  {
    path: 'edit/:id',
    loadComponent: () => import('./beneficiary-form/beneficiary-form.component').then(m => m.BeneficiaryFormComponent)
  }
];
