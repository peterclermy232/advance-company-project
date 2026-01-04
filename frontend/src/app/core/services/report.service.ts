import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Report, DashboardSummary } from '../models/report.model';

@Injectable({
  providedIn: 'root'
})
export class ReportService {
  private apiService = inject(ApiService);

  getReports(params?: any): Observable<PaginatedResponse<Report>> {
    return this.apiService.get<PaginatedResponse<Report>>('reports/', params);
  }

  generateFinancialReport(dateFrom?: string, dateTo?: string): Observable<any> {
    return this.apiService.post<any>('reports/generate_financial_report/', {
      date_from: dateFrom,
      date_to: dateTo
    });
  }

  getDashboardSummary(): Observable<DashboardSummary> {
    return this.apiService.get<DashboardSummary>('reports/dashboard_summary/');
  }
}