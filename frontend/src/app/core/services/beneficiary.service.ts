import { Injectable, inject } from '@angular/core';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
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
  return this.apiService.get<PaginatedResponse<Beneficiary>>('beneficiary/', params).pipe(
    map(response => {
      // Handle case where API returns array instead of paginated response
      if (Array.isArray(response)) {
        return {
          count: response.length,
          next: null,
          previous: null,
          results: response
        } as PaginatedResponse<Beneficiary>;
      }
      return response;
    })
  );
}

  getBeneficiary( uuid: string): Observable<Beneficiary> {
    return this.apiService.get<Beneficiary>(`beneficiary/${uuid}/`);
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

  updateBeneficiary( uuid: string, data: FormData): Observable<Beneficiary> {
    return this.apiService.update<Beneficiary>(`beneficiary/${uuid}/`, data)
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

  deleteBeneficiary(uuid: string): Observable<any> {
    return this.apiService.delete<any>(`beneficiary/${uuid}/`)
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

  verifyBeneficiary(uuid: string): Observable<any> {
    return this.apiService.post<any>(`beneficiary/${uuid}/verify/`, {})
      .pipe(
        tap(() => {
          this.toastService.success('Beneficiary verified! ✓');
        })
      );
  }

  markDeceased(uuid: string): Observable<any> {
    return this.apiService.post<any>(`beneficiary/${uuid}/mark_deceased/`, {})
      .pipe(
        tap(() => {
          this.toastService.info('Beneficiary marked as deceased');
        })
      );
  }
}