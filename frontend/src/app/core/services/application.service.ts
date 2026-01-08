import { Injectable, inject } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Application } from '../models/application.model';
import { ToastService } from './toast.service';

@Injectable({
  providedIn: 'root'
})
export class ApplicationService {
  private apiService = inject(ApiService);
  private toastService = inject(ToastService);

  getApplications(params?: any): Observable<PaginatedResponse<Application>> {
    return this.apiService.get<PaginatedResponse<Application>>('applications/', params);
  }

  getApplication(id: number): Observable<Application> {
    return this.apiService.get<Application>(`applications/${id}/`);
  }

  createApplication(data: FormData): Observable<Application> {
    return this.apiService.upload<Application>('applications/', data)
      .pipe(
        tap(() => {
          this.toastService.success('Application submitted successfully! 📝');
        }),
        catchError(error => {
          this.toastService.error('Failed to submit application. Please try again.');
          return throwError(() => error);
        })
      );
  }

  approveApplication(id: number, comments: string): Observable<any> {
    return this.apiService.post<any>(`applications/${id}/approve/`, { comments })
      .pipe(
        tap(() => {
          this.toastService.success('Application approved! ✓');
        }),
        catchError(error => {
          this.toastService.error('Failed to approve application');
          return throwError(() => error);
        })
      );
  }

  rejectApplication(id: number, comments: string): Observable<any> {
    return this.apiService.post<any>(`applications/${id}/reject/`, { comments })
      .pipe(
        tap(() => {
          this.toastService.warning('Application rejected');
        }),
        catchError(error => {
          this.toastService.error('Failed to reject application');
          return throwError(() => error);
        })
      );
  }

  reviewApplication(id: number): Observable<any> {
    return this.apiService.post<any>(`applications/${id}/review/`, {})
      .pipe(
        tap(() => {
          this.toastService.info('Application marked as under review');
        })
      );
  }
}
