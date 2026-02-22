import { Injectable, inject } from '@angular/core';
import { Observable, tap, catchError, map } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Application } from '../models/application.model';
import { BackendResponse, BackendResponseHandler } from './backend-response-handler.service';

export interface ApplicationTypeChoice {
  value: string;
  label: string;
  description: string;
}

export interface StatusChoice {
  value: string;
  label: string;
}

export interface ApplicationChoices {
  application_types: ApplicationTypeChoice[];
  status_choices: StatusChoice[];
}

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

  getChoices(): Observable<ApplicationChoices> {
    return this.apiService.get<ApplicationChoices>('applications/choices/')
      .pipe(
        catchError(error => this.responseHandler.handleError(error, 'Failed to load application types'))
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
          this.responseHandler.showToast(response);
        }),
        map(response => response.data as Application),
        catchError(error => this.responseHandler.handleError(error, 'Failed to submit application'))
      );
  }

  approveApplication(id: string, comments: string): Observable<any> {
    return this.apiService.post<BackendResponse>(`applications/${id}/approve/`, { comments })
      .pipe(
        tap(response => {
          this.responseHandler.showToast(response);
        }),
        catchError(error => this.responseHandler.handleError(error, 'Failed to approve application'))
      );
  }

  rejectApplication(uuid: string, comments: string): Observable<any> {
    return this.apiService.post<BackendResponse>(`applications/${uuid}/reject/`, { comments })
      .pipe(
        tap(response => {
          this.responseHandler.showToast(response);
        }),
        catchError(error => this.responseHandler.handleError(error, 'Failed to reject application'))
      );
  }

  reviewApplication(uuid: string): Observable<any> {
    return this.apiService.post<BackendResponse>(`applications/${uuid}/review/`, {})
      .pipe(
        tap(response => {
          this.responseHandler.showToast(response);
        }),
        catchError(error => this.responseHandler.handleError(error))
      );
  }
}