import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Beneficiary } from '../models/beneficiary.model';
import { ToastService } from './toast.service';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class BeneficiaryService {
  private readonly apiService = inject(ApiService);
  private readonly toastService = inject(ToastService);
  private readonly http = inject(HttpClient);

  getBeneficiaries(params?: any): Observable<PaginatedResponse<Beneficiary>> {
    return this.apiService.get<PaginatedResponse<Beneficiary>>('beneficiary/', params).pipe(
      map(response => {
        if (Array.isArray(response)) {
          return { count: (response as any[]).length, next: null, previous: null, results: response as Beneficiary[] };
        }
        return response;
      })
    );
  }

  getBeneficiary(uuid: string): Observable<Beneficiary> {
    return this.apiService.get<Beneficiary>(`beneficiary/${uuid}/`);
  }

  createBeneficiary(data: FormData): Observable<Beneficiary> {
    return this.apiService.upload<Beneficiary>('beneficiary/', data).pipe(
      tap(() => this.toastService.success('Beneficiary added successfully')),
      catchError(error => {
        this.toastService.error('Failed to add beneficiary');
        return throwError(() => error);
      })
    );
  }

  updateBeneficiary(uuid: string, data: FormData): Observable<Beneficiary> {
    return this.apiService.update<Beneficiary>(`beneficiary/${uuid}/`, data).pipe(
      tap(() => this.toastService.success('Beneficiary updated successfully')),
      catchError(error => {
        this.toastService.error('Failed to update beneficiary');
        return throwError(() => error);
      })
    );
  }

  deleteBeneficiary(uuid: string): Observable<any> {
    return this.apiService.delete<any>(`beneficiary/${uuid}/`).pipe(
      tap(() => this.toastService.success('Beneficiary removed')),
      catchError(error => {
        this.toastService.error('Failed to remove beneficiary');
        return throwError(() => error);
      })
    );
  }

  verifyBeneficiary(uuid: string, notes?: string): Observable<any> {
    return this.apiService.post<any>(`beneficiary/${uuid}/verify/`, { notes }).pipe(
      tap(() => this.toastService.success('Beneficiary verified'))
    );
  }

  rejectBeneficiary(uuid: string, reason: string): Observable<any> {
    return this.apiService.post<any>(`beneficiary/${uuid}/reject/`, { reason }).pipe(
      tap(() => this.toastService.info('Beneficiary rejected')),
      catchError(error => {
        this.toastService.error('Failed to reject beneficiary');
        return throwError(() => error);
      })
    );
  }

  markDeceased(uuid: string, formData: FormData): Observable<any> {
    return this.http.post<any>(`${environment.apiUrl}/beneficiary/${uuid}/mark_deceased/`, formData).pipe(
      tap(() => this.toastService.info('Beneficiary marked as deceased')),
      catchError(error => {
        this.toastService.error('Failed to update beneficiary status');
        return throwError(() => error);
      })
    );
  }

  getStatistics(): Observable<any> {
    return this.apiService.get<any>('beneficiary/statistics/');
  }

  getPendingVerification(): Observable<any> {
    return this.apiService.get<any>('beneficiary/pending_verification/');
  }
}
