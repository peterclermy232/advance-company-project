import { Injectable, inject } from '@angular/core';
import { Observable, tap, catchError, map } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Application } from '../models/application.model';
import { BackendResponse, BackendResponseHandler } from './backend-response-handler.service';

@Injectable({
  providedIn: 'root'
})
export class ApplicationService {
  private apiService = inject(ApiService);
  private responseHandler = inject(BackendResponseHandler);

  getApplications(): Observable<Application[]> {
    return this.apiService.get<BackendResponse<Application[]>>('applications/')
      .pipe(
        tap(response => {
          // Don't show toast for list operations
          this.responseHandler.showToast(response, true);
        }),
        map(response => response.data || []),
        catchError(error => this.responseHandler.handleError(error, 'Failed to load applications'))
      );
  }

  getApplication(id: number): Observable<Application> {
    return this.apiService.get<BackendResponse<Application>>(`applications/${id}/`)
      .pipe(
        tap(response => this.responseHandler.showToast(response, true)),
        map(response => response.data as Application),
        catchError(error => this.responseHandler.handleError(error, 'Failed to load application'))
      );
  }

  createApplication(data: FormData): Observable<Application> {
    return this.apiService.upload<BackendResponse<Application>>('applications/', data)
      .pipe(
        tap(response => {
          // Show backend success message
          this.responseHandler.showToast(response);
        }),
        map(response => response.data as Application),
        catchError(error => this.responseHandler.handleError(error, 'Failed to submit application'))
      );
  }

  approveApplication(id: number, comments: string): Observable<any> {
    return this.apiService.post<BackendResponse>(`applications/${id}/approve/`, { comments })
      .pipe(
        tap(response => {
          // Show backend success message (e.g., "Application approved successfully")
          this.responseHandler.showToast(response);
        }),
        catchError(error => this.responseHandler.handleError(error, 'Failed to approve application'))
      );
  }

  rejectApplication(id: number, comments: string): Observable<any> {
    return this.apiService.post<BackendResponse>(`applications/${id}/reject/`, { comments })
      .pipe(
        tap(response => {
          // Show backend warning/error message (e.g., "Application rejected")
          this.responseHandler.showToast(response);
        }),
        catchError(error => this.responseHandler.handleError(error, 'Failed to reject application'))
      );
  }

  reviewApplication(id: number): Observable<any> {
    return this.apiService.post<BackendResponse>(`applications/${id}/review/`, {})
      .pipe(
        tap(response => {
          // Show backend info message
          this.responseHandler.showToast(response);
        }),
        catchError(error => this.responseHandler.handleError(error))
      );
  }
}