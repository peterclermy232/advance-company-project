import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../shared/components/loading/loading.component';
import { AppNotification, NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule, HeaderComponent, SidebarComponent, LoadingComponent],
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
    this.notificationService.notifications$.subscribe(
      notifications => {
        this.notifications = notifications;
        this.isLoading = false;
      }
    );

    this.notificationService.unreadCount$.subscribe(
      count => this.unreadCount = count
    );

    // Load all notifications (not just recent)
    this.notificationService.getRecentNotifications().subscribe();
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  handleNotificationClick(notification: AppNotification) {
    // Mark as read
    if (!notification.is_read) {
      this.notificationService.markAsRead(notification.id).subscribe(() => {
        notification.is_read = true;
      });
    }

    // Navigate to relevant page
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

    const route = routes[notification.notification_type];
    if (route) {
      this.router.navigate([route]);
    }
  }

  markAllAsRead() {
    this.notificationService.markAllAsRead().subscribe(() => {
      this.notifications.forEach(n => n.is_read = true);
    });
  }

  clearAllRead() {
    if (confirm('Are you sure you want to clear all read notifications?')) {
      this.notificationService.clearAll().subscribe(() => {
        this.notificationService.refresh();
      });
    }
  }

  getIconClass(type: string): string {
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

  getIcon(type: string): string {
    const icons: { [key: string]: string } = {
      'deposit_created': 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      'deposit_approved': 'M5 13l4 4L19 7',
      'deposit_rejected': 'M6 18L18 6M6 6l12 12',
      'application_submitted': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      'application_approved': 'M5 13l4 4L19 7',
      'application_rejected': 'M6 18L18 6M6 6l12 12',
      'document_verified': 'M5 13l4 4L19 7',
      'beneficiary_verified': 'M5 13l4 4L19 7',
    };
    return icons[type] || 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9';
  }

  getTypeClass(type: string): string {
    const classes: { [key: string]: string } = {
      'deposit_created': 'bg-blue-100 text-blue-800',
      'deposit_approved': 'bg-green-100 text-green-800',
      'deposit_rejected': 'bg-red-100 text-red-800',
      'application_submitted': 'bg-purple-100 text-purple-800',
      'application_approved': 'bg-green-100 text-green-800',
      'application_rejected': 'bg-red-100 text-red-800',
      'document_verified': 'bg-green-100 text-green-800',
      'beneficiary_verified': 'bg-green-100 text-green-800',
    };
    return classes[type] || 'bg-gray-100 text-gray-800';
  }

  getTypeLabel(type: string): string {
    const labels: { [key: string]: string } = {
      'deposit_created': 'Deposit',
      'deposit_approved': 'Deposit',
      'deposit_rejected': 'Deposit',
      'application_submitted': 'Application',
      'application_approved': 'Application',
      'application_rejected': 'Application',
      'document_verified': 'Document',
      'beneficiary_verified': 'Beneficiary',
    };
    return labels[type] || 'System';
  }
}