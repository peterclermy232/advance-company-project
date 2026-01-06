import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { FinancialAccount, Deposit, DepositRequest, MonthlySummary } from '../models/financial.model';

@Injectable({
  providedIn: 'root'
})
export class FinancialService {
  private apiService = inject(ApiService);

  getMyAccount(): Observable<FinancialAccount> {
    return this.apiService.get<FinancialAccount>('financial/accounts/my_account/');
  }

  getDeposits(params?: any): Observable<PaginatedResponse<Deposit>> {
    return this.apiService.get<PaginatedResponse<Deposit>>('financial/deposits/', params);
  }

  createDeposit(data: DepositRequest): Observable<Deposit> {
    return this.apiService.post<Deposit>('financial/deposits/', data);
  }

  confirmPayment(id: number): Observable<any> {
    return this.apiService.post<any>(`financial/deposits/${id}/confirm_payment/`, {});
  }

  getMonthlySummary(): Observable<MonthlySummary> {
    return this.apiService.get<MonthlySummary>('financial/deposits/monthly_summary/');
  }

  canDeposit(): Observable<any> {
    return this.apiService.get<any>('financial/deposits/can_deposit/');
  }
}