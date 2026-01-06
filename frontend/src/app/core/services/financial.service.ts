import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Deposit } from '../models/financial.model';


@Injectable({
  providedIn: 'root'
})
export class FinancialService {
  private apiUrl = `${environment.apiUrl}/financial`;

  constructor(private http: HttpClient) {}

  // Account endpoints
  getMyAccount(): Observable<any> {
    return this.http.get(`${this.apiUrl}/accounts/my_account/`);
  }

  getAccounts(): Observable<any> {
    return this.http.get(`${this.apiUrl}/accounts/`);
  }

  // Deposit endpoints
  getDeposits(): Observable<any> {
    return this.http.get(`${this.apiUrl}/deposits/`);
  }

  createDeposit(data: any): Observable<Deposit> {
    return this.http.post<Deposit>(`${this.apiUrl}/deposits/`, data);
  }

  canDeposit(): Observable<any> {
    return this.http.get(`${this.apiUrl}/deposits/can_deposit/`);
  }

  getMonthlySummary(): Observable<any> {
    return this.http.get(`${this.apiUrl}/deposits/monthly_summary/`);
  }

  // Admin endpoints
  getPendingApprovals(): Observable<any> {
    return this.http.get(`${this.apiUrl}/deposits/pending_approvals/`);
  }

  approveDeposit(depositId: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/deposits/${depositId}/approve_deposit/`, {});
  }

  rejectDeposit(depositId: number, reason: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/deposits/${depositId}/reject_deposit/`, { reason });
  }

  // Interest calculations
  getInterestCalculations(): Observable<any> {
    return this.http.get(`${this.apiUrl}/interest-calculations/`);
  }
}