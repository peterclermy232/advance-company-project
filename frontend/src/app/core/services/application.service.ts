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
  return this.apiService.get<Application[]>('applications/')
    .pipe(
      tap(() => {}),
      catchError(error => this.responseHandler.handleError(error, 'Failed to load applications'))
    );
}


  getApplication(uuid: string): Observable<Application> {
    return this.apiService.get<BackendResponse<Application>>(`applications/${uuid}/`)
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

  approveApplication(uuid: string, comments: string): Observable<any> {
    return this.apiService.post<BackendResponse>(`applications/${uuid}/approve/`, { comments })
      .pipe(
        tap(response => {
          // Show backend success message (e.g., "Application approved successfully")
          this.responseHandler.showToast(response);
        }),
        catchError(error => this.responseHandler.handleError(error, 'Failed to approve application'))
      );
  }

  rejectApplication(uuid: string, comments: string): Observable<any> {
    return this.apiService.post<BackendResponse>(`applications/${uuid}/reject/`, { comments })
      .pipe(
        tap(response => {
          // Show backend warning/error message (e.g., "Application rejected")
          this.responseHandler.showToast(response);
        }),
        catchError(error => this.responseHandler.handleError(error, 'Failed to reject application'))
      );
  }

  reviewApplication(uuid: string): Observable<any> {
    return this.apiService.post<BackendResponse>(`applications/${uuid}/review/`, {})
      .pipe(
        tap(response => {
          // Show backend info message
          this.responseHandler.showToast(response);
        }),
        catchError(error => this.responseHandler.handleError(error))
      );
  }
}