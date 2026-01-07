import { Injectable, inject } from '@angular/core';
import { Observable, BehaviorSubject, interval, timer } from 'rxjs';
import { switchMap, tap, catchError, startWith } from 'rxjs/operators';
import { ApiService } from './api.service';
import { MatSnackBar } from '@angular/material/snack-bar';


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

interface NotificationResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: AppNotification[];
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private apiService = inject(ApiService);
  private snackBar = inject(MatSnackBar);
  
  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();
  
  private notificationsSubject = new BehaviorSubject<AppNotification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();

  private pollingSubscription: any;

  constructor() {
    // Initial load
    this.initialize();
  }

  // Initialize service and start polling
  initialize(): void {
    console.log('NotificationService: Initializing...');
    
    // Load initial data
    this.refresh();
    
    // Start polling every 30 seconds
    this.startPolling();
  }

  private startPolling(): void {
    // Cancel existing polling if any
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }

    // Poll for new notifications every 30 seconds
    this.pollingSubscription = interval(30000)
      .pipe(
        startWith(0), // Start immediately
        switchMap(() => this.getUnreadCount()),
        catchError(error => {
          console.error('NotificationService: Polling error', error);
          return [];
        })
      )
      .subscribe();
  }

  getNotifications(): Observable<NotificationResponse> {
    console.log('NotificationService: Fetching all notifications');
    return this.apiService.get<NotificationResponse>('notifications/').pipe(
      tap(response => {
        console.log('NotificationService: Received notifications', response);
        this.notificationsSubject.next(response.results);
      }),
      catchError(error => {
        console.error('NotificationService: Error fetching notifications', error);
        throw error;
      })
    );
  }

  getUnreadNotifications(): Observable<NotificationResponse> {
    console.log('NotificationService: Fetching unread notifications');
    return this.apiService.get<NotificationResponse>('notifications/unread/').pipe(
      tap(response => console.log('NotificationService: Unread notifications', response)),
      catchError(error => {
        console.error('NotificationService: Error fetching unread notifications', error);
        throw error;
      })
    );
  }

  getUnreadCount(): Observable<{ count: number }> {
    console.log('NotificationService: Fetching unread count');
    return this.apiService.get<{ count: number }>('notifications/unread_count/').pipe(
      tap(response => {
        console.log('NotificationService: Unread count', response.count);
        this.unreadCountSubject.next(response.count);
      }),
      catchError(error => {
        console.error('NotificationService: Error fetching unread count', error);
        return [];
      })
    );
  }

  getRecentNotifications(): Observable<NotificationResponse> {
    console.log('NotificationService: Fetching recent notifications');
    return this.apiService.get<NotificationResponse>('notifications/recent/').pipe(
      tap(response => {
        console.log('NotificationService: Recent notifications', response);
        this.notificationsSubject.next(response.results);
      }),
      catchError(error => {
        console.error('NotificationService: Error fetching recent notifications', error);
        throw error;
      })
    );
  }

  markAsRead(id: number): Observable<AppNotification> {
    console.log('NotificationService: Marking notification as read', id);
    return this.apiService.post<AppNotification>(`notifications/${id}/mark_as_read/`, {}).pipe(
      tap(() => {
        // Update local state
        const count = this.unreadCountSubject.value;
        this.unreadCountSubject.next(Math.max(0, count - 1));
        
        // Update the notification in the list
        const notifications = this.notificationsSubject.value;
        const updatedNotifications = notifications.map(n => 
          n.id === id ? { ...n, is_read: true } : n
        );
        this.notificationsSubject.next(updatedNotifications);
      }),
      catchError(error => {
        console.error('NotificationService: Error marking as read', error);
        throw error;
      })
    );
  }

  markAllAsRead(): Observable<any> {
    console.log('NotificationService: Marking all as read');
    return this.apiService.post<any>('notifications/mark_all_as_read/', {}).pipe(
      tap(() => {
        this.unreadCountSubject.next(0);
        
        // Update all notifications to read
        const notifications = this.notificationsSubject.value;
        const updatedNotifications = notifications.map(n => ({ ...n, is_read: true }));
        this.notificationsSubject.next(updatedNotifications);
      }),
      catchError(error => {
        console.error('NotificationService: Error marking all as read', error);
        throw error;
      })
    );
  }

  clearAll(): Observable<any> {
    console.log('NotificationService: Clearing all read notifications');
    return this.apiService.delete<any>('notifications/clear_all/').pipe(
      tap(() => {
        // Remove read notifications from the list
        const notifications = this.notificationsSubject.value;
        const unreadNotifications = notifications.filter(n => !n.is_read);
        this.notificationsSubject.next(unreadNotifications);
      }),
      catchError(error => {
        console.error('NotificationService: Error clearing notifications', error);
        throw error;
      })
    );
  }

  // Refresh notifications manually
  refresh(): void {
    console.log('NotificationService: Refreshing notifications');
    this.getRecentNotifications().subscribe();
    this.getUnreadCount().subscribe();
  }

  // Stop polling when service is destroyed
  ngOnDestroy(): void {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }
  }
  success(message: string, action: string = 'OK', duration = 3000): void {
  this.snackBar.open(message, action, {
    duration,
    panelClass: ['snackbar-success'],
    horizontalPosition: 'right',
    verticalPosition: 'top'
  });
}

error(message: string, action: string = 'DISMISS', duration = 4000): void {
  this.snackBar.open(message, action, {
    duration,
    panelClass: ['snackbar-error'],
    horizontalPosition: 'right',
    verticalPosition: 'top'
  });
}

info(message: string, action: string = 'OK', duration = 3000): void {
  this.snackBar.open(message, action, {
    duration,
    panelClass: ['snackbar-info'],
    horizontalPosition: 'right',
    verticalPosition: 'top'
  });
}
}