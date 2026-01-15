import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl;

  /**
   * GET request
   * @param endpoint - API endpoint (e.g., 'auth/users/1/')
   * @param params - Query parameters
   */
  get<T>(endpoint: string, params?: any): Observable<T> {
    let httpParams = new HttpParams();
    
    if (params) {
      Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
          httpParams = httpParams.set(key, params[key].toString());
        }
      });
    }
    
    return this.http.get<T>(`${this.baseUrl}/${endpoint}`, { params: httpParams });
  }

  /**
   * POST request
   * @param endpoint - API endpoint
   * @param data - Request body data
   */
  post<T>(endpoint: string, data: any): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}/${endpoint}`, data);
  }

  /**
   * PUT request (full update)
   * @param endpoint - API endpoint
   * @param data - Request body data
   */
  put<T>(endpoint: string, data: any): Observable<T> {
    return this.http.put<T>(`${this.baseUrl}/${endpoint}`, data);
  }

  /**
   * PATCH request (partial update)
   * @param endpoint - API endpoint
   * @param data - Request body data
   */
  patch<T>(endpoint: string, data: any): Observable<T> {
    return this.http.patch<T>(`${this.baseUrl}/${endpoint}`, data);
  }

  /**
   * DELETE request
   * @param endpoint - API endpoint
   */
  delete<T>(endpoint: string): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}/${endpoint}`);
  }

  /**
   * Upload files using FormData
   * @param endpoint - API endpoint
   * @param formData - FormData with files
   */
  upload<T>(endpoint: string, formData: FormData): Observable<T> {
    // Don't set Content-Type - Angular will set it automatically with boundary
    return this.http.post<T>(`${this.baseUrl}/${endpoint}`, formData);
  }

  /**
   * Download file
   * @param endpoint - API endpoint
   */
  download(endpoint: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/${endpoint}`, {
      responseType: 'blob'
    });
  }

  /**
   * Helper method for paginated endpoints
   * @param endpoint - API endpoint
   * @param page - Page number
   * @param pageSize - Items per page
   * @param filters - Additional filters
   */
  getPaginated<T>(
    endpoint: string, 
    page: number = 1, 
    pageSize: number = 10,
    filters?: any
  ): Observable<PaginatedResponse<T>> {
    const params = {
      page: page.toString(),
      page_size: pageSize.toString(),
      ...filters
    };
    
    return this.get<PaginatedResponse<T>>(endpoint, params);
  }
}

// Example usage service for specific endpoints
@Injectable({
  providedIn: 'root'
})
export class UserApiService {
  private api = inject(ApiService);

  // Get all users (admin only)
  getUsers(page: number = 1, pageSize: number = 10) {
    return this.api.getPaginated<any>('auth/users/', page, pageSize);
  }

  // Get specific user
  getUser(userId: number) {
    return this.api.get<any>(`auth/users/${userId}/`);
  }

  // Update user
  updateUser(userId: number, data: any) {
    return this.api.patch<any>(`auth/users/${userId}/`, data);
  }

  // Delete user (admin only)
  deleteUser(userId: number) {
    return this.api.delete(`auth/users/${userId}/`);
  }
}

// Notification service example
@Injectable({
  providedIn: 'root'
})
export class NotificationApiService {
  private api = inject(ApiService);

  getNotifications(page: number = 1) {
    return this.api.getPaginated<any>('notifications/', page, 20);
  }

  getUnreadCount() {
    return this.api.get<{ count: number }>('notifications/unread_count/');
  }

  markAsRead(notificationId: number) {
    return this.api.post(`notifications/${notificationId}/mark_read/`, {});
  }

  markAllAsRead() {
    return this.api.post('notifications/mark_all_read/', {});
  }
}