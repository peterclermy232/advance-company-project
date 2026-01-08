import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { StatCardComponent } from '../../shared/components/stat-card/stat-card.component';
import { LoadingComponent } from '../../shared/components/loading/loading.component';
import { CurrencyFormatPipe } from '../../shared/pipes/currency-format.pipe';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { DashboardSummary } from '../../core/models/report.model';
import { User } from '../../core/models/user.model';

interface Notification {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  time_ago: string;
  related_deposit_id?: number;
  related_application_id?: number;
}

interface RecentActivity {
  action: string;
  amount: string;
  date: string;
  status: 'success' | 'pending' | 'rejected';
  icon: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule, 
    RouterModule, 
    HeaderComponent, 
    SidebarComponent, 
    StatCardComponent, 
    LoadingComponent,
    CurrencyFormatPipe
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  private apiService = inject(ApiService);
  private authService = inject(AuthService);

  currentUser: User | null = null;
  summary: DashboardSummary | null = null;
  isLoading = true;
  sidebarOpen = true;

  recentActivities: RecentActivity[] = [];
  monthlyContributions = [4200, 4800, 5100, 4500, 5300, 5000];
  months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];

  ngOnInit() {
    this.loadDashboardData();
    this.loadRecentNotifications();
  }

  loadDashboardData() {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });

    this.apiService.get<DashboardSummary>('reports/dashboard_summary/')
      .subscribe({
        next: (data) => {
          this.summary = data;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading dashboard data:', error);
          this.isLoading = false;
        }
      });
  }

  loadRecentNotifications() {
    // Fetch recent notifications (limit to 5 for dashboard)
    this.apiService.get<{ results: Notification[] }>('notifications/?limit=5')
      .subscribe({
        next: (response) => {
          this.recentActivities = this.mapNotificationsToActivities(response.results || []);
        },
        error: (error) => {
          console.error('Error loading notifications:', error);
          // Keep empty array if error
          this.recentActivities = [];
        }
      });
  }

  mapNotificationsToActivities(notifications: Notification[]): RecentActivity[] {
    return notifications.map(notification => {
      const activity: RecentActivity = {
        action: notification.title,
        amount: this.extractAmountOrDetail(notification.message),
        date: notification.time_ago,
        status: this.getStatusFromNotificationType(notification.notification_type),
        icon: this.getIconFromNotificationType(notification.notification_type)
      };
      return activity;
    });
  }

  extractAmountOrDetail(message: string): string {
    // Try to extract KES amount from message
    const amountMatch = message.match(/KES\s*([\d,]+\.?\d*)/);
    if (amountMatch) {
      return `KES ${amountMatch[1]}`;
    }

    // Extract key details for non-financial notifications
    if (message.includes('Birth Certificate')) return 'Birth Certificate';
    if (message.includes('ID Document')) return 'ID Document';
    if (message.includes('application')) return 'Application';
    if (message.includes('beneficiary')) return 'Beneficiary';
    if (message.includes('document')) return 'Document';
    
    // Return first 30 characters as fallback
    return message.length > 30 ? message.substring(0, 30) + '...' : message;
  }

  getStatusFromNotificationType(type: string): 'success' | 'pending' | 'rejected' {
    if (type.includes('approved') || type.includes('verified') || type.includes('completed')) {
      return 'success';
    }
    if (type.includes('rejected') || type.includes('failed') || type.includes('deceased')) {
      return 'rejected';
    }
    return 'pending';
  }

  getIconFromNotificationType(type: string): string {
    const iconMap: { [key: string]: string } = {
      'deposit': 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      'application': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      'document': 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
      'beneficiary': 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
      'system': 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    };

    // Find matching icon based on notification type
    for (const [key, icon] of Object.entries(iconMap)) {
      if (type.includes(key)) {
        return icon;
      }
    }

    // Default icon
    return iconMap['system'];
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  getMaxContribution(): number {
    return Math.max(...this.monthlyContributions);
  }

  markNotificationAsRead(notificationId: number) {
    this.apiService.post(`notifications/${notificationId}/mark_as_read/`, {})
      .subscribe({
        next: () => {
          console.log('Notification marked as read');
        },
        error: (error) => {
          console.error('Error marking notification as read:', error);
        }
      });
  }
}