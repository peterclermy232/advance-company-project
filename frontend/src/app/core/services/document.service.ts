import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Document } from '../models/document.model';

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private apiService = inject(ApiService);

  getDocuments(params?: any): Observable<PaginatedResponse<Document>> {
    return this.apiService.get<PaginatedResponse<Document>>('documents/', params);
  }

  uploadDocument(data: FormData): Observable<Document> {
    return this.apiService.upload<Document>('documents/', data);
  }

  deleteDocument(id: number): Observable<any> {
    return this.apiService.delete<any>(`documents/${id}/`);
  }

  verifyDocument(id: number): Observable<any> {
    return this.apiService.post<any>(`documents/${id}/verify/`, {});
  }

  rejectDocument(id: number, reason: string): Observable<any> {
    return this.apiService.post<any>(`documents/${id}/reject/`, { reason });
  }
}
