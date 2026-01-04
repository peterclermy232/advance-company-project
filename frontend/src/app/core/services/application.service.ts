import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Application } from '../models/application.model';

@Injectable({
  providedIn: 'root'
})
export class ApplicationService {
  private apiService = inject(ApiService);

  getApplications(params?: any): Observable<PaginatedResponse<Application>> {
    return this.apiService.get<PaginatedResponse<Application>>('applications/', params);
  }

  getApplication(id: number): Observable<Application> {
    return this.apiService.get<Application>(`applications/${id}/`);
  }

  createApplication(data: FormData): Observable<Application> {
    return this.apiService.upload<Application>('applications/', data);
  }

  approveApplication(id: number, comments: string): Observable<any> {
    return this.apiService.post<any>(`applications/${id}/approve/`, { comments });
  }

  rejectApplication(id: number, comments: string): Observable<any> {
    return this.apiService.post<any>(`applications/${id}/reject/`, { comments });
  }

  reviewApplication(id: number): Observable<any> {
    return this.apiService.post<any>(`applications/${id}/review/`, {});
  }
}