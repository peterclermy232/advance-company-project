import { Injectable, inject } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Report, DashboardSummary } from '../models/report.model';
import { ToastService } from './toast.service';

@Injectable({
  providedIn: 'root'
})
export class ReportService {
  private apiService = inject(ApiService);
  private toastService = inject(ToastService);

  getReports(params?: any): Observable<PaginatedResponse<Report>> {
    return this.apiService.get<PaginatedResponse<Report>>('reports/', params);
  }

  generateFinancialReport(dateFrom?: string, dateTo?: string): Observable<any> {
    return this.apiService.post<any>('reports/generate_financial_report/', {
      date_from: dateFrom,
      date_to: dateTo
    }).pipe(
      tap(() => {
        this.toastService.success('Report generated successfully! 📊');
      }),
      catchError(error => {
        this.toastService.error('Failed to generate report. Please try again.');
        return throwError(() => error);
      })
    );
  }

  getDashboardSummary(): Observable<DashboardSummary> {
    return this.apiService.get<DashboardSummary>('reports/dashboard_summary/');
  }
}