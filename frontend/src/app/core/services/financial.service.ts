import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import { CanDepositResponse, Deposit, DepositResponse } from '../models/financial.model';
import { ToastService } from './toast.service';



@Injectable({
  providedIn: 'root'
})
export class FinancialService {
  private http = inject(HttpClient);
  private toastService = inject(ToastService);
  private apiUrl = `${environment.apiUrl}/financial`;

  // Account endpoints
  getMyAccount(): Observable<any> {
    return this.http.get(`${this.apiUrl}/accounts/my_account/`)
      .pipe(
        catchError(error => {
          this.toastService.error('Failed to load account information');
          return throwError(() => error);
        })
      );
  }

  getAccounts(): Observable<any> {
    return this.http.get(`${this.apiUrl}/accounts/`);
  }

  // Deposit endpoints
  getDeposits(): Observable<any> {
    return this.http.get(`${this.apiUrl}/deposits/`);
  }

  createDeposit(data: any): Observable<DepositResponse> {
    return this.http.post<DepositResponse>(`${this.apiUrl}/deposits/`, data)
      .pipe(
        catchError(error => {
          console.error('Deposit creation error:', error);
          return throwError(() => error);
        })
      );
  }

  canDeposit(): Observable<CanDepositResponse> {
    return this.http.get<CanDepositResponse>(`${this.apiUrl}/deposits/can_deposit/`);
  }

  getMonthlySummary(): Observable<any> {
    return this.http.get(`${this.apiUrl}/deposits/monthly_summary/`);
  }

  // Admin endpoints
  getPendingApprovals(): Observable<any> {
    return this.http.get(`${this.apiUrl}/deposits/pending_approvals/`);
  }

  approveDeposit(depositId: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/deposits/${depositId}/approve_deposit/`, {})
      .pipe(
        tap(() => {
          this.toastService.success('Deposit approved successfully! ✓');
        }),
        catchError(error => {
          const message = error.error?.error || 'Failed to approve deposit';
          this.toastService.error(message);
          return throwError(() => error);
        })
      );
  }

  rejectDeposit(depositId: number, reason: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/deposits/${depositId}/reject_deposit/`, { reason })
      .pipe(
        tap(() => {
          this.toastService.warning('Deposit rejected');
        }),
        catchError(error => {
          const message = error.error?.error || 'Failed to reject deposit';
          this.toastService.error(message);
          return throwError(() => error);
        })
      );
  }

  // Interest calculations
  getInterestCalculations(): Observable<any> {
    return this.http.get(`${this.apiUrl}/interest/`);
  }
}