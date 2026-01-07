import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../shared/components/loading/loading.component';
import { AppNotification, NotificationService } from '../../core/services/notification.service';
import { NotificationIconPipe } from '../../shared/pipes/notification-icon.pipe';
import { NotificationTypeLabelPipe } from '../../shared/pipes/notification-type-label.pipe';
import { NotificationTypeClassPipe } from '../../shared/pipes/notification-type-class.pipe';


@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    SidebarComponent,
    LoadingComponent,
    NotificationIconPipe,
    NotificationTypeLabelPipe,
    NotificationTypeClassPipe
  ],
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.scss']
})
export class NotificationsComponent implements OnInit {
  private notificationService = inject(NotificationService);
  private router = inject(Router);

  sidebarOpen = true;
  isLoading = true;
  notifications: AppNotification[] = [];
  unreadCount = 0;

  ngOnInit() {
    this.loadNotifications();
  }

  loadNotifications() {
    this.notificationService.notifications$.subscribe(n => {
      this.notifications = n ?? [];
      this.isLoading = false;
    });

    this.notificationService.unreadCount$.subscribe(c => this.unreadCount = c ?? 0);

    this.notificationService.getRecentNotifications().subscribe();
  }

  toggleSidebar() { this.sidebarOpen = !this.sidebarOpen; }

  handleNotificationClick(notification: AppNotification) {
    if (!notification.is_read) {
      this.notificationService.markAsRead(notification.id).subscribe(() => notification.is_read = true);
    }
    this.navigateToNotification(notification);
  }

  navigateToNotification(notification: AppNotification) {
    const routes: { [key: string]: string } = {
      'deposit_created': '/financial',
      'deposit_approved': '/dashboard',
      'deposit_rejected': '/dashboard',
      'application_submitted': '/applications',
      'application_approved': '/applications',
      'application_rejected': '/applications',
      'document_verified': '/documents',
      'beneficiary_verified': '/beneficiary',
    };
    const route = routes[notification.notification_type] || '/dashboard';
    this.router.navigate([route]);
  }

  markAllAsRead() {
    this.notificationService.markAllAsRead().subscribe(() => {
      this.notifications.forEach(n => n.is_read = true);
    });
  }

  clearAllRead() {
    if (confirm('Are you sure you want to clear all read notifications?')) {
      this.notificationService.clearAll().subscribe(() => this.notificationService.refresh());
    }
  }

  getIconClass(type: string) {
    const classes: { [key: string]: string } = {
      'deposit_created': 'w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0',
      'deposit_approved': 'w-10 h-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0',
      'deposit_rejected': 'w-10 h-10 bg-red-600 rounded-full flex items-center justify-center flex-shrink-0',
      'application_submitted': 'w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0',
      'application_approved': 'w-10 h-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0',
      'application_rejected': 'w-10 h-10 bg-red-600 rounded-full flex items-center justify-center flex-shrink-0',
      'document_verified': 'w-10 h-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0',
      'beneficiary_verified': 'w-10 h-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0',
    };
    return classes[type] || 'w-10 h-10 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0';
  }
}
