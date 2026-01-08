import { Injectable, inject } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Document } from '../models/document.model';
import { ToastService } from './toast.service';

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private apiService = inject(ApiService);
  private toastService = inject(ToastService);

  getDocuments(params?: any): Observable<PaginatedResponse<Document>> {
    return this.apiService.get<PaginatedResponse<Document>>('documents/', params);
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