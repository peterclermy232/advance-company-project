import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AdminAnalyticsService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/admin/analytics`;

  getMemberAnalytics(): Observable<any> {
    return this.http.get(`${this.apiUrl}/members/`);
  }

  getSummary(): Observable<any> {
    return this.http.get(`${this.apiUrl}/summary/`);
  }

  getMonthlyTrends(months: number = 12): Observable<any> {
    return this.http.get(`${this.apiUrl}/trends/?months=${months}`);
  }

  exportAnalytics(format: 'excel' | 'pdf'): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/export/?format=${format}`, {
      responseType: 'blob'
    });
  }
}