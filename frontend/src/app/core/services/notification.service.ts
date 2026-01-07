import { Injectable, inject, OnDestroy } from '@angular/core';
import { Observable, BehaviorSubject, interval, of } from 'rxjs';
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
export class NotificationService implements OnDestroy {
  private apiService = inject(ApiService);
  private snackBar = inject(MatSnackBar);

  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();

  private notificationsSubject = new BehaviorSubject<AppNotification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();

  private pollingSubscription: any;

  constructor() {
    this.initialize();
  }

  // Initialize service and start polling
  initialize(): void {
    console.log('NotificationService: Initializing...');
    this.refresh();
    this.startPolling();
  }

  private startPolling(): void {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }

    this.pollingSubscription = interval(30000)
      .pipe(
        startWith(0),
        switchMap(() => this.getUnreadCount()),
        catchError(error => {
          console.error('NotificationService: Polling error', error);
          return of({ count: 0 }); // ✅ must return observable
        })
      )
      .subscribe();
  }

  getNotifications(): Observable<NotificationResponse> {
    return this.apiService.get<NotificationResponse>('notifications/').pipe(
      tap(response => {
        console.log('NotificationService: Received notifications', response);
        this.notificationsSubject.next(response.results ?? []);
      }),
      catchError(error => {
        console.error('NotificationService: Error fetching notifications', error);
        return of({ count: 0, next: null, previous: null, results: [] });
      })
    );
  }

  getUnreadNotifications(): Observable<NotificationResponse> {
    return this.apiService.get<NotificationResponse>('notifications/unread/').pipe(
      tap(response => {
        console.log('NotificationService: Unread notifications', response);
      }),
      catchError(error => {
        console.error('NotificationService: Error fetching unread notifications', error);
        return of({ count: 0, next: null, previous: null, results: [] });
      })
    );
  }

  getUnreadCount(): Observable<{ count: number }> {
    return this.apiService.get<{ count: number }>('notifications/unread_count/').pipe(
      tap(response => {
        this.unreadCountSubject.next(response.count ?? 0);
      }),
      catchError(error => {
        console.error('NotificationService: Error fetching unread count', error);
        return of({ count: 0 });
      })
    );
  }

  getRecentNotifications(): Observable<NotificationResponse> {
    return this.apiService.get<NotificationResponse>('notifications/recent/').pipe(
      tap(response => {
        this.notificationsSubject.next(response.results ?? []);
      }),
      catchError(error => {
        console.error('NotificationService: Error fetching recent notifications', error);
        return of({ count: 0, next: null, previous: null, results: [] });
      })
    );
  }

  markAsRead(id: number): Observable<AppNotification> {
    return this.apiService.post<AppNotification>(`notifications/${id}/mark_as_read/`, {}).pipe(
      tap(() => {
        const count = this.unreadCountSubject.value;
        this.unreadCountSubject.next(Math.max(0, count - 1));

        const notifications = this.notificationsSubject.value ?? [];
        const updatedNotifications = notifications.map(n => n.id === id ? { ...n, is_read: true } : n);
        this.notificationsSubject.next(updatedNotifications);
      }),
      catchError(error => {
        console.error('NotificationService: Error marking as read', error);
        return of(null as unknown as AppNotification); // fallback
      })
    );
  }

  markAllAsRead(): Observable<any> {
    return this.apiService.post<any>('notifications/mark_all_as_read/', {}).pipe(
      tap(() => {
        this.unreadCountSubject.next(0);

        const notifications = this.notificationsSubject.value ?? [];
        const updatedNotifications = notifications.map(n => ({ ...n, is_read: true }));
        this.notificationsSubject.next(updatedNotifications);
      }),
      catchError(error => {
        console.error('NotificationService: Error marking all as read', error);
        return of(null);
      })
    );
  }

  clearAll(): Observable<any> {
    return this.apiService.delete<any>('notifications/clear_all/').pipe(
      tap(() => {
        const notifications = this.notificationsSubject.value ?? [];
        const unreadNotifications = notifications.filter(n => !n.is_read);
        this.notificationsSubject.next(unreadNotifications);
      }),
      catchError(error => {
        console.error('NotificationService: Error clearing notifications', error);
        return of(null);
      })
    );
  }

  refresh(): void {
    this.getRecentNotifications().subscribe();
    this.getUnreadCount().subscribe();
  }

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
