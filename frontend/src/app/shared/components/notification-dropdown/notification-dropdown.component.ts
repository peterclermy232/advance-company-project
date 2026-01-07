import { Component, inject, OnInit, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';
import { AppNotification, NotificationService } from '../../../core/services/notification.service';
import { NotificationIconPipe } from '../../pipes/notification-icon.pipe';
import { NotificationTypeLabelPipe } from '../../pipes/notification-type-label.pipe';
import { NotificationTypeClassPipe } from '../../pipes/notification-type-class.pipe';


@Component({
  selector: 'app-notification-dropdown',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    NotificationIconPipe,
    NotificationTypeLabelPipe,
    NotificationTypeClassPipe
  ],
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
  onDocumentClick(event: MouseEvent) { this.isOpen = false; }

  ngOnInit() {
    this.subscriptions.push(
      this.notificationService.notifications$.subscribe(n => this.notifications = n ?? [])
    );
    this.subscriptions.push(
      this.notificationService.unreadCount$.subscribe(c => this.unreadCount = c ?? 0)
    );
    this.notificationService.refresh();
  }

  ngOnDestroy() { this.subscriptions.forEach(sub => sub.unsubscribe()); }

  trackByNotificationId(index: number, notification: AppNotification) { return notification.id; }

  toggleDropdown() { 
    this.isOpen = !this.isOpen; 
    if (this.isOpen) this.notificationService.getRecentNotifications().subscribe();
  }

  closeDropdown() { this.isOpen = false; }

  handleNotificationClick(notification: AppNotification) {
    if (!notification.is_read) this.notificationService.markAsRead(notification.id).subscribe(() => notification.is_read = true);
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
    this.router.navigate([routes[notification.notification_type] || '/dashboard']);
    this.closeDropdown();
  }

  markAllAsRead() { this.notificationService.markAllAsRead().subscribe(() => this.notifications.forEach(n => n.is_read = true)); }

  clearAllRead() { if (confirm('Clear all read notifications?')) this.notificationService.clearAll().subscribe(() => this.notificationService.refresh()); }

  viewAll() { this.router.navigate(['/notifications']); this.closeDropdown(); }

  getIconClass(type: string) {
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
}
