import { Injectable, inject } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { ToastService } from './toast.service';

// Backend response interface matching Django response_utils.py
export interface BackendResponse<T = any> {
  success: boolean;
  message: string;
  toast_type: 'success' | 'error' | 'warning' | 'info';
  data?: T;
  errors?: any;
}

@Injectable({
  providedIn: 'root'
})
export class BackendResponseHandler {
  private toastService = inject(ToastService);
  showToast(response: BackendResponse, silent: boolean = false): void {
    if (silent || !response.message) return;
    
    switch (response.toast_type) {
      case 'success':
        this.toastService.success(response.message);
        break;
      case 'error':
        this.toastService.error(response.message);
        break;
      case 'warning':
        this.toastService.warning(response.message);
        break;
      case 'info':
        this.toastService.info(response.message);
        break;
      default:
        this.toastService.info(response.message);
    }
  }
  handleError(error: any, fallbackMessage?: string): Observable<never> {
    console.error('Backend error:', error);

    // Priority 1: Check for standardized backend response format
    if (error.error?.message && error.error?.toast_type) {
      const backendError = error.error as BackendResponse;
      this.showToast(backendError);
      
      // Log detailed errors if available
      if (backendError.errors) {
        console.error('Validation errors:', backendError.errors);
      }
    }
    // Priority 2: Check for Django Rest Framework error format
    else if (error.error?.detail) {
      this.toastService.error(error.error.detail);
    }
    // Priority 3: Check for validation errors (field-specific)
    else if (error.error?.errors) {
      const errors = error.error.errors;
      const firstError = Object.values(errors)[0];
      const errorMessage = Array.isArray(firstError) ? firstError[0] : firstError;
      this.toastService.error(errorMessage as string);
    }
    // Priority 4: Generic error message
    else if (error.message) {
      this.toastService.error(error.message);
    }
    // Priority 5: Fallback message
    else {
      this.toastService.error(fallbackMessage || 'An unexpected error occurred');
    }
    
    return throwError(() => error);
  }

  extractData<T>(response: BackendResponse<T>): T | undefined {
    return response.data;
  }

  isSuccess(response: BackendResponse): boolean {
    return response.success === true;
  }

  getErrors(response: BackendResponse): any {
    return response.errors;
  }
}