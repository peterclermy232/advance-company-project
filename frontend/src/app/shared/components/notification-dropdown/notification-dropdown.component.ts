import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
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
  
  isOpen = false;
  notifications: AppNotification[] = [];
  unreadCount = 0;
  
  private subscriptions: Subscription[] = [];

  ngOnInit() {
    // Subscribe to notifications
    this.subscriptions.push(
      this.notificationService.notifications$.subscribe(
        notifications => this.notifications = notifications
      )
    );

    // Subscribe to unread count
    this.subscriptions.push(
      this.notificationService.unreadCount$.subscribe(
        count => this.unreadCount = count
      )
    );

    // Initial load
    this.notificationService.refresh();
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  toggleDropdown() {
    this.isOpen = !this.isOpen;
    if (this.isOpen) {
      this.notificationService.getRecentNotifications().subscribe();
    }
  }

  closeDropdown() {
    this.isOpen = false;
  }

  markAsRead(notification: AppNotification) {
    if (!notification.is_read) {
      this.notificationService.markAsRead(notification.id).subscribe(() => {
        notification.is_read = true;
      });
    }
  }

  markAllAsRead() {
    this.notificationService.markAllAsRead().subscribe(() => {
      this.notifications.forEach(n => n.is_read = true);
      this.closeDropdown();
    });
  }

  clearAll() {
    if (confirm('Are you sure you want to clear all read notifications?')) {
      this.notificationService.clearAll().subscribe(() => {
        this.notificationService.refresh();
        this.closeDropdown();
      });
    }
  }

  viewAll() {
    // Navigate to notifications page (you can create this later)
    this.closeDropdown();
  }

  getIconClass(type: string): string {
    const classes: { [key: string]: string } = {
      'deposit_created': 'w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0',
      'deposit_approved': 'w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0',
      'deposit_rejected': 'w-8 h-8 bg-red-600 rounded-full flex items-center justify-center flex-shrink-0',
      'application_submitted': 'w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0',
      'application_approved': 'w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0',
      'application_rejected': 'w-8 h-8 bg-red-600 rounded-full flex items-center justify-center flex-shrink-0',
      'document_verified': 'w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0',
      'beneficiary_verified': 'w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0',
    };
    return classes[type] || 'w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0';
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
}