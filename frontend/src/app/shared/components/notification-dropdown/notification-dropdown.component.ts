import { Component, inject, OnInit, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';
import { AppNotification, NotificationService } from '../../../core/services/notification.service';


@Component({
  selector: 'app-notification-dropdown',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './notification-dropdown.component.html',
  styleUrls: ['./notification-dropdown.component.scss']
})
export class NotificationDropdownComponent implements OnInit, OnDestroy {
  private notificationService = inject(NotificationService);
  private router = inject(Router);
  
  isOpen = false;
  notifications: AppNotification[] = [];
  unreadCount = 0;
  
  private subscriptions: Subscription[] = [];

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    // This will close dropdown when clicking outside
    // The stopPropagation() in template prevents closing when clicking inside
  }

  ngOnInit() {
    console.log('NotificationDropdownComponent: Initializing');
    
    // Subscribe to notifications
    this.subscriptions.push(
      this.notificationService.notifications$.subscribe(
        notifications => {
          console.log('NotificationDropdownComponent: Received notifications', notifications);
          this.notifications = notifications;
        }
      )
    );

    // Subscribe to unread count
    this.subscriptions.push(
      this.notificationService.unreadCount$.subscribe(
        count => {
          console.log('NotificationDropdownComponent: Unread count updated', count);
          this.unreadCount = count;
        }
      )
    );

    // Initial load
    console.log('NotificationDropdownComponent: Triggering initial refresh');
    this.notificationService.refresh();
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  trackByNotificationId(index: number, notification: AppNotification): number {
    return notification.id;
  }

  toggleDropdown() {
    console.log('NotificationDropdownComponent: Toggle dropdown', !this.isOpen);
    this.isOpen = !this.isOpen;
    if (this.isOpen) {
      console.log('NotificationDropdownComponent: Fetching notifications');
      this.notificationService.getRecentNotifications().subscribe({
        next: (response) => console.log('NotificationDropdownComponent: Notifications loaded', response),
        error: (error) => console.error('NotificationDropdownComponent: Error loading notifications', error)
      });
    }
  }

  closeDropdown() {
    this.isOpen = false;
  }

  handleNotificationClick(notification: AppNotification) {
    console.log('NotificationDropdownComponent: Notification clicked', notification);
    
    // Mark as read first
    if (!notification.is_read) {
      this.notificationService.markAsRead(notification.id).subscribe({
        next: () => {
          console.log('NotificationDropdownComponent: Marked as read', notification.id);
          notification.is_read = true;
        },
        error: (error) => {
          console.error('NotificationDropdownComponent: Error marking as read', error);
        }
      });
    }

    // Navigate to relevant page
    this.navigateToNotification(notification);
    
    // Close dropdown
    this.closeDropdown();
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
      'document_rejected': '/documents',
      'beneficiary_verified': '/beneficiary',
      'system': '/dashboard',
    };

    const route = routes[notification.notification_type];
    
    if (route) {
      console.log('NotificationDropdownComponent: Navigating to', route);
      this.router.navigate([route]);
    } else {
      console.log('NotificationDropdownComponent: No route found, going to dashboard');
      this.router.navigate(['/dashboard']);
    }
  }

  markAllAsRead() {
    console.log('NotificationDropdownComponent: Marking all as read');
    this.notificationService.markAllAsRead().subscribe({
      next: () => {
        console.log('NotificationDropdownComponent: All marked as read');
        this.notifications.forEach(n => n.is_read = true);
      },
      error: (error) => {
        console.error('NotificationDropdownComponent: Error marking all as read', error);
      }
    });
  }

  clearAllRead() {
    if (confirm('Clear all read notifications?')) {
      console.log('NotificationDropdownComponent: Clearing all read');
      this.notificationService.clearAll().subscribe({
        next: () => {
          console.log('NotificationDropdownComponent: All read notifications cleared');
          this.notificationService.refresh();
        },
        error: (error) => {
          console.error('NotificationDropdownComponent: Error clearing notifications', error);
        }
      });
    }
  }

  viewAll() {
    console.log('NotificationDropdownComponent: View all clicked');
    this.router.navigate(['/notifications']);
    this.closeDropdown();
  }

  getIconClass(type: string): string {
    const classes: { [key: string]: string } = {
      'deposit_created': 'w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center',
      'deposit_approved': 'w-8 h-8 bg-green-600 rounded-full flex items-center justify-center',
      'deposit_rejected': 'w-8 h-8 bg-red-600 rounded-full flex items-center justify-center',
      'application_submitted': 'w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center',
      'application_approved': 'w-8 h-8 bg-green-600 rounded-full flex items-center justify-center',
      'application_rejected': 'w-8 h-8 bg-red-600 rounded-full flex items-center justify-center',
      'document_verified': 'w-8 h-8 bg-green-600 rounded-full flex items-center justify-center',
      'document_rejected': 'w-8 h-8 bg-red-600 rounded-full flex items-center justify-center',
      'beneficiary_verified': 'w-8 h-8 bg-green-600 rounded-full flex items-center justify-center',
      'system': 'w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center',
    };
    return classes[type] || 'w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center';
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
      'document_rejected': 'M6 18L18 6M6 6l12 12',
      'beneficiary_verified': 'M5 13l4 4L19 7',
      'system': 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
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
      'document_rejected': 'bg-red-100 text-red-800',
      'beneficiary_verified': 'bg-green-100 text-green-800',
      'system': 'bg-gray-100 text-gray-800',
    };
    return classes[type] || 'bg-gray-100 text-gray-800';
  }

  getTypeLabel(type: string): string {
    const labels: { [key: string]: string } = {
      'deposit_created': 'Deposit',
      'deposit_approved': 'Approved',
      'deposit_rejected': 'Rejected',
      'application_submitted': 'Application',
      'application_approved': 'Approved',
      'application_rejected': 'Rejected',
      'document_verified': 'Verified',
      'document_rejected': 'Rejected',
      'beneficiary_verified': 'Verified',
      'system': 'System',
    };
    return labels[type] || 'Notification';
  }
}