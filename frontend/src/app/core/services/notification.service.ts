import { Injectable, inject, OnDestroy } from '@angular/core';
import { Observable, BehaviorSubject, interval, of } from 'rxjs';
import { switchMap, tap, catchError, startWith } from 'rxjs/operators';
import { ApiService } from './api.service';
import { MatSnackBar } from '@angular/material/snack-bar';

export interface AppNotification {
   uuid: string;
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
  private readonly apiService = inject(ApiService);
  private readonly snackBar = inject(MatSnackBar);

  private readonly unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();

  private readonly notificationsSubject = new BehaviorSubject<AppNotification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();

  private pollingSubscription: any;

  constructor() {}

  // Initialize service and start polling
  initialize(): void {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return; // Not logged in → do nothing
    }
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
          return of({ count: 0 }); 
        })
      )
      .subscribe();
  }

  stop(): void {
  if (this.pollingSubscription) {
    this.pollingSubscription.unsubscribe();
    this.pollingSubscription = null;
  }

  this.unreadCountSubject.next(0);
  this.notificationsSubject.next([]);
}

  getNotifications(): Observable<NotificationResponse> {
    return this.apiService.get<NotificationResponse>('notifications/').pipe(
      tap(response => {
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
      catchError(() => of({ count: 0, next: null, previous: null, results: [] }))
    );
  }

  getUnreadCount(): Observable<{ count: number }> {
    return this.apiService.get<{ count: number }>('notifications/unread_count/').pipe(
      tap(response => {
        this.unreadCountSubject.next(response.count ?? 0);
      }),
      catchError(() => of({ count: 0 }))
    );
  }

  getRecentNotifications(): Observable<NotificationResponse | AppNotification[]> {
    return this.apiService.get<NotificationResponse | AppNotification[]>('notifications/recent/').pipe(
      tap(response => {
        const notifications = Array.isArray(response) ? response : (response.results ?? []);
        this.notificationsSubject.next(notifications);
      }),
      catchError(() => of({ count: 0, next: null, previous: null, results: [] }))
    );
  }

  markAsRead( uuid: string): Observable<AppNotification> {
    return this.apiService.post<AppNotification>(`notifications/${uuid}/mark_as_read/`, {}).pipe(
      tap(() => {
        const count = this.unreadCountSubject.value;
        this.unreadCountSubject.next(Math.max(0, count - 1));

        const notifications = this.notificationsSubject.value ?? [];
        const updatedNotifications = notifications.map(n => n.uuid === uuid ? { ...n, is_read: true } : n);
        this.notificationsSubject.next(updatedNotifications);
      }),
      catchError(() => of(null as unknown as AppNotification))
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
      catchError(() => of(null))
    );
  }

  clearAll(): Observable<any> {
    return this.apiService.delete<any>('notifications/clear_all/').pipe(
      tap(() => {
        const notifications = this.notificationsSubject.value ?? [];
        const unreadNotifications = notifications.filter(n => !n.is_read);
        this.notificationsSubject.next(unreadNotifications);
      }),
      catchError(() => of(null))
    );
  }

  refresh(): void {
    this.getRecentNotifications().subscribe();
    this.getUnreadCount().subscribe();
  }
  
loading(message: string, action: string = '', duration: number = 0) {
    // duration = 0 means the snackbar stays open until manually dismissed
    const snackBarRef = this.snackBar.open(message, action, {
      duration,
      panelClass: ['snackbar-loading'],
      horizontalPosition: 'right',
      verticalPosition: 'top'
    });

    return snackBarRef; // return ref so it can be dismissed later
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

  warning(message: string, action: string = 'OK', duration = 3500): void {
  this.snackBar.open(message, action, {
    duration,
    panelClass: ['snackbar-warning'],
    horizontalPosition: 'right',
    verticalPosition: 'top'
  });
}
}
