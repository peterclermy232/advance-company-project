import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { CanDepositResponse, Deposit, DepositResponse } from '../models/financial.model';
import { ToastService } from './toast.service';

// Backend response interface
interface BackendResponse<T = any> {
  success: boolean;
  message: string;
  toast_type: 'success' | 'error' | 'warning' | 'info';
  data?: T;
  errors?: any;
}

@Injectable({
  providedIn: 'root'
})
export class FinancialService {
  private http = inject(HttpClient);
  private toastService = inject(ToastService);
  private apiUrl = `${environment.apiUrl}/financial`;

  private showBackendToast(response: BackendResponse) {
    if (!response.message) return;
    
    switch (response.toast_type) {
      case 'success':
        this.toastService.success(response.message);
        break;
      case 'error':
        this.toastService.error(response.message);
        break;
      case 'warning':
        this.toastService.warning(response.message);
        break;
      case 'info':
        this.toastService.info(response.message);
        break;
      default:
        this.toastService.info(response.message);
    }
  }

  private handleBackendError(error: any): Observable<never> {
    // Check if error has backend response format
    if (error.error?.message) {
      const backendError = error.error as BackendResponse;
      this.showBackendToast(backendError);
    } else if (error.error?.detail) {
      this.toastService.error(error.error.detail);
    } else if (error.message) {
      this.toastService.error(error.message);
    } else {
      this.toastService.error('An unexpected error occurred');
    }
    
    return throwError(() => error);
  }

  // Account endpoints
  getMyAccount(): Observable<any> {
    return this.http.get<BackendResponse>(`${this.apiUrl}/accounts/my_account/`)
      .pipe(
        tap(response => {
          // Optionally show message for account fetch
          if (response.message) {
            this.showBackendToast(response);
          }
        }),
        map(response => response.data || response),
        catchError(error => this.handleBackendError(error))
      );
  }

  getAccounts(): Observable<any> {
    return this.http.get<BackendResponse>(`${this.apiUrl}/accounts/`)
      .pipe(
        map(response => response.data || response),
        catchError(error => this.handleBackendError(error))
      );
  }

  // Deposit endpoints
  getDeposits(): Observable<any> {
    return this.http.get<BackendResponse>(`${this.apiUrl}/deposits/`)
      .pipe(
        map(response => response.data || response),
        catchError(error => this.handleBackendError(error))
      );
  }

  createDeposit(data: any): Observable<DepositResponse> {
    return this.http.post<BackendResponse<DepositResponse>>(`${this.apiUrl}/deposits/`, data)
      .pipe(
        tap(response => {
          this.showBackendToast(response);
        }),
        map(response => response.data as DepositResponse),
        catchError(error => this.handleBackendError(error))
      );
  }

  canDeposit(): Observable<CanDepositResponse> {
    return this.http.get<BackendResponse<CanDepositResponse>>(`${this.apiUrl}/deposits/can_deposit/`)
      .pipe(
        tap(response => {
          // Only show toast if deposit is not allowed
          if (response.data && !response.data.can_deposit && response.message) {
            this.showBackendToast(response);
          }
        }),
        map(response => response.data as CanDepositResponse),
        catchError(error => this.handleBackendError(error))
      );
  }

  getMonthlySummary(): Observable<any> {
    return this.http.get<BackendResponse>(`${this.apiUrl}/deposits/monthly_summary/`)
      .pipe(
        map(response => response.data || response),
        catchError(error => this.handleBackendError(error))
      );
  }

  // Admin endpoints
  getPendingApprovals(): Observable<any> {
    return this.http.get<BackendResponse>(`${this.apiUrl}/deposits/pending_approvals/`)
      .pipe(
        map(response => response.data || response),
        catchError(error => this.handleBackendError(error))
      );
  }

  approveDeposit(depositId: string): Observable<any> {
    return this.http.post<BackendResponse>(`${this.apiUrl}/deposits/${depositId}/approve_deposit/`, {})
      .pipe(
        tap(response => {
          this.showBackendToast(response);
        }),
        map(response => response.data || response),
        catchError(error => this.handleBackendError(error))
      );
  }

  rejectDeposit(depositId: string, reason: string): Observable<any> {
    return this.http.post<BackendResponse>(`${this.apiUrl}/deposits/${depositId}/reject_deposit/`, { reason })
      .pipe(
        tap(response => {
          this.showBackendToast(response);
        }),
        map(response => response.data || response),
        catchError(error => this.handleBackendError(error))
      );
  }

  // Interest calculations
  getInterestCalculations(): Observable<any> {
    return this.http.get<BackendResponse>(`${this.apiUrl}/interest/`)
      .pipe(
        map(response => response.data || response),
        catchError(error => this.handleBackendError(error))
      );
  }
}