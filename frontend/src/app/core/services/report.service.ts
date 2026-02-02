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

  getReports(params?: any): Observable<any> {
    // Return observable that can handle both array and paginated response
    return this.apiService.get<any>('reports/', params).pipe(
      tap(response => {
        console.log('Raw API response:', response);
      }),
      catchError(error => {
        console.error('API error:', error);
        return throwError(() => error);
      })
    );
  }

  generateFinancialReport(dateFrom?: string, dateTo?: string): Observable<any> {
    const payload: any = {};
    if (dateFrom) payload.date_from = dateFrom;
    if (dateTo) payload.date_to = dateTo;
    
    return this.apiService.post<any>('reports/generate_financial_report/', payload).pipe(
      tap(() => {
        this.toastService.success('Financial report generated successfully!');
      }),
      catchError(error => {
        this.toastService.error('Failed to generate financial report. Please try again.');
        return throwError(() => error);
      })
    );
  }

  generateCompensatoryReport(dateFrom?: string, dateTo?: string): Observable<any> {
    const payload: any = {};
    if (dateFrom) payload.date_from = dateFrom;
    if (dateTo) payload.date_to = dateTo;
    
    return this.apiService.post<any>('reports/generate_compensatory_report/', payload).pipe(
      tap(() => {
        this.toastService.success('Compensatory report generated successfully!');
      }),
      catchError(error => {
        this.toastService.error('Failed to generate compensatory report. Please try again.');
        return throwError(() => error);
      })
    );
  }

  generateActivityReport(dateFrom?: string, dateTo?: string): Observable<any> {
    const payload: any = {};
    if (dateFrom) payload.date_from = dateFrom;
    if (dateTo) payload.date_to = dateTo;
    
    return this.apiService.post<any>('reports/generate_activity_report/', payload).pipe(
      tap(() => {
        this.toastService.success('Activity report generated successfully!');
      }),
      catchError(error => {
        this.toastService.error('Failed to generate activity report. Please try again.');
        return throwError(() => error);
      })
    );
  }

  getDashboardSummary(): Observable<DashboardSummary> {
    return this.apiService.get<DashboardSummary>('reports/dashboard_summary/');
  }
}