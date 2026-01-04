import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, PaginatedResponse } from './api.service';
import { Beneficiary } from '../models/beneficiary.model';

@Injectable({
  providedIn: 'root'
})
export class BeneficiaryService {
  private apiService = inject(ApiService);

  getBeneficiaries(params?: any): Observable<PaginatedResponse<Beneficiary>> {
    return this.apiService.get<PaginatedResponse<Beneficiary>>('beneficiary/', params);
  }

  getBeneficiary(id: number): Observable<Beneficiary> {
    return this.apiService.get<Beneficiary>(`beneficiary/${id}/`);
  }

  createBeneficiary(data: FormData): Observable<Beneficiary> {
    return this.apiService.upload<Beneficiary>('beneficiary/', data);
  }

  updateBeneficiary(id: number, data: FormData): Observable<Beneficiary> {
    return this.apiService.upload<Beneficiary>(`beneficiary/${id}/`, data);
  }

  deleteBeneficiary(id: number): Observable<any> {
    return this.apiService.delete<any>(`beneficiary/${id}/`);
  }

  verifyBeneficiary(id: number): Observable<any> {
    return this.apiService.post<any>(`beneficiary/${id}/verify/`, {});
  }

  markDeceased(id: number): Observable<any> {
    return this.apiService.post<any>(`beneficiary/${id}/mark_deceased/`, {});
  }
}