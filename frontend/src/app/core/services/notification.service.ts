import { Injectable, inject } from '@angular/core';
import { Observable, BehaviorSubject, interval } from 'rxjs';
import { switchMap, tap } from 'rxjs/operators';
import { ApiService } from './api.service';

export interface AppNotification {
  id: number;
  user: number;
  user_name: string;
  notification_type: string;
  title: string;
  message: string;
  related_deposit_id?: number;
  related_application_id?: number;
  related_user_name?: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
  time_ago: string;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private apiService = inject(ApiService);
  
  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();
  
  private notificationsSubject = new BehaviorSubject<AppNotification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();

  constructor() {
    // Poll for new notifications every 30 seconds
    interval(30000)
      .pipe(switchMap(() => this.getUnreadCount()))
      .subscribe();
  }

  getNotifications(): Observable<AppNotification[]> {
    return this.apiService.get<AppNotification[]>('notifications/').pipe(
      tap(notifications => this.notificationsSubject.next(notifications))
    );
  }

  getUnreadNotifications(): Observable<AppNotification[]> {
    return this.apiService.get<AppNotification[]>('notifications/unread/');
  }

  getUnreadCount(): Observable<{ count: number }> {
    return this.apiService.get<{ count: number }>('notifications/unread_count/').pipe(
      tap(response => this.unreadCountSubject.next(response.count))
    );
  }

  getRecentNotifications(): Observable<AppNotification[]> {
    return this.apiService.get<AppNotification[]>('notifications/recent/').pipe(
      tap(notifications => this.notificationsSubject.next(notifications))
    );
  }

  markAsRead(id: number): Observable<AppNotification> {
    return this.apiService.post<AppNotification>(`notifications/${id}/mark_as_read/`, {}).pipe(
      tap(() => {
        // Update local state
        const count = this.unreadCountSubject.value;
        this.unreadCountSubject.next(Math.max(0, count - 1));
      })
    );
  }

  markAllAsRead(): Observable<any> {
    return this.apiService.post<any>('notifications/mark_all_as_read/', {}).pipe(
      tap(() => this.unreadCountSubject.next(0))
    );
  }

  clearAll(): Observable<any> {
    return this.apiService.delete<any>('notifications/clear_all/');
  }

  // Refresh notifications manually
  refresh(): void {
    this.getRecentNotifications().subscribe();
    this.getUnreadCount().subscribe();
  }
}