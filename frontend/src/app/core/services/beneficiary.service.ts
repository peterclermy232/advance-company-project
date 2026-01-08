import { Injectable, inject } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Beneficiary } from '../models/beneficiary.model';
import { ToastService } from './toast.service';

@Injectable({
  providedIn: 'root'
})
export class BeneficiaryService {
  private apiService = inject(ApiService);
  private toastService = inject(ToastService);

  getBeneficiaries(params?: any): Observable<PaginatedResponse<Beneficiary>> {
    return this.apiService.get<PaginatedResponse<Beneficiary>>('beneficiary/', params);
  }

  getBeneficiary(id: number): Observable<Beneficiary> {
    return this.apiService.get<Beneficiary>(`beneficiary/${id}/`);
  }

  createBeneficiary(data: FormData): Observable<Beneficiary> {
    return this.apiService.upload<Beneficiary>('beneficiary/', data)
      .pipe(
        tap(() => {
          this.toastService.success('Beneficiary added successfully! 👥');
        }),
        catchError(error => {
          this.toastService.error('Failed to add beneficiary. Please try again.');
          return throwError(() => error);
        })
      );
  }

  updateBeneficiary(id: number, data: FormData): Observable<Beneficiary> {
    return this.apiService.upload<Beneficiary>(`beneficiary/${id}/`, data)
      .pipe(
        tap(() => {
          this.toastService.success('Beneficiary updated successfully! ✓');
        }),
        catchError(error => {
          this.toastService.error('Failed to update beneficiary');
          return throwError(() => error);
        })
      );
  }

  deleteBeneficiary(id: number): Observable<any> {
    return this.apiService.delete<any>(`beneficiary/${id}/`)
      .pipe(
        tap(() => {
          this.toastService.success('Beneficiary removed successfully');
        }),
        catchError(error => {
          this.toastService.error('Failed to remove beneficiary');
          return throwError(() => error);
        })
      );
  }

  verifyBeneficiary(id: number): Observable<any> {
    return this.apiService.post<any>(`beneficiary/${id}/verify/`, {})
      .pipe(
        tap(() => {
          this.toastService.success('Beneficiary verified! ✓');
        })
      );
  }

  markDeceased(id: number): Observable<any> {
    return this.apiService.post<any>(`beneficiary/${id}/mark_deceased/`, {})
      .pipe(
        tap(() => {
          this.toastService.info('Beneficiary marked as deceased');
        })
      );
  }
}