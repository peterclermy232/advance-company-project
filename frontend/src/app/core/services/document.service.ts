import { Injectable, inject } from '@angular/core';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Document } from '../models/document.model';
import { ToastService } from './toast.service';

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private apiService = inject(ApiService);
  private toastService = inject(ToastService);

  getDocuments(params?: any): Observable<Document[]> {
  return this.apiService
    .get<PaginatedResponse<Document> | Document[]>('documents/', params)
    .pipe(
      tap(response => {
        console.log('Documents API response:', response);
      }),
      catchError(error => {
        this.toastService.error('Failed to load documents');
        return throwError(() => error);
      }),
      //  normalize response
      map(response =>
        Array.isArray(response) ? response : response?.results ?? []
      )
    );
}


  uploadDocument(data: FormData): Observable<Document> {
    return this.apiService.upload<Document>('documents/', data)
      .pipe(
        tap(() => {
          this.toastService.success('Document uploaded successfully! 📄');
        }),
        catchError(error => {
          this.toastService.error('Failed to upload document. Please try again.');
          return throwError(() => error);
        })
      );
  }

  deleteDocument(id: number): Observable<any> {
    return this.apiService.delete<any>(`documents/${id}/`)
      .pipe(
        tap(() => {
          this.toastService.success('Document deleted successfully');
        }),
        catchError(error => {
          this.toastService.error('Failed to delete document');
          return throwError(() => error);
        })
      );
  }

  verifyDocument(id: number): Observable<any> {
    return this.apiService.post<any>(`documents/${id}/verify/`, {})
      .pipe(
        tap(() => {
          this.toastService.success('Document verified! ✓');
        })
      );
  }

  rejectDocument(id: number, reason: string): Observable<any> {
    return this.apiService.post<any>(`documents/${id}/reject/`, { reason })
      .pipe(
        tap(() => {
          this.toastService.warning('Document rejected');
        })
      );
  }
}