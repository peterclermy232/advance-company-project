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
import { FinancialService } from '../../core/services/financial.service';
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

interface MonthlyEntry {
  month: number;
  year: number;
  total_deposits: number;
  count: number;
}

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

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
  private readonly apiService = inject(ApiService);
  private readonly authService = inject(AuthService);
  private readonly financialService = inject(FinancialService);

  currentUser: User | null = null;
  summary: DashboardSummary | null = null;
  isLoading = true;
  isLoadingChart = true;
  sidebarOpen = true;
  selectedRange = 6;

  recentActivities: RecentActivity[] = [];
  allChartData: MonthlyEntry[] = [];

  // ── computed chart slices ──────────────────────────────────────────
  get visibleData(): MonthlyEntry[] {
    return this.allChartData.slice(-this.selectedRange);
  }

  get totalVisibleContributions(): number {
    return this.visibleData.reduce((sum, r) => sum + r.total_deposits, 0);
  }

  get chartHasData(): boolean {
    return this.visibleData.length > 0;
  }

  /** Period-over-period growth — only shown when we have 2× selectedRange months of history. */
  get periodGrowth(): { pct: number; direction: 'up' | 'down' | 'same' } | null {
    if (this.allChartData.length < this.selectedRange * 2) return null;
    const prevData = this.allChartData.slice(
      this.allChartData.length - this.selectedRange * 2,
      this.allChartData.length - this.selectedRange
    );
    const prevTotal = prevData.reduce((s, r) => s + r.total_deposits, 0);
    if (prevTotal === 0) return null;
    const pct = Math.round(((this.totalVisibleContributions - prevTotal) / prevTotal) * 100);
    return { pct, direction: pct > 0 ? 'up' : pct < 0 ? 'down' : 'same' };
  }

  /** Consecutive months (newest-first) that had at least one completed deposit. */
  get contributionStreak(): number {
    let streak = 0;
    for (const entry of [...this.allChartData].reverse()) {
      if (entry.total_deposits > 0) streak++;
      else break;
    }
    return streak;
  }

  get avgMonthlyContribution(): number {
    const active = this.visibleData.filter(r => r.total_deposits > 0);
    if (active.length === 0) return 0;
    return this.totalVisibleContributions / active.length;
  }

  get bestMonth(): MonthlyEntry | null {
    if (this.visibleData.length === 0) return null;
    return this.visibleData.reduce((best, r) =>
      r.total_deposits > best.total_deposits ? r : best
    );
  }

  /** Month-over-month growth for bar at position i within visibleData. */
  getMonthGrowth(index: number): { pct: number; direction: 'up' | 'down' | 'same' } | null {
    if (index === 0) return null;
    const curr = this.visibleData[index].total_deposits;
    const prev = this.visibleData[index - 1].total_deposits;
    if (prev === 0) return null;
    const pct = Math.round(((curr - prev) / prev) * 100);
    return { pct, direction: pct > 0 ? 'up' : pct < 0 ? 'down' : 'same' };
  }

  ngOnInit() {
    this.loadDashboardData();
    this.loadRecentNotifications();
    this.loadMonthlySummary();
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
        error: () => {
          this.isLoading = false;
        }
      });
  }

  loadRecentNotifications() {
    this.apiService.get<Notification[] | { results: Notification[] }>('notifications/?limit=5')
      .subscribe({
        next: (response) => {
          const notifications: Notification[] = Array.isArray(response)
            ? response
            : (response?.results ?? []);
          this.recentActivities = this.mapNotificationsToActivities(notifications);
        },
        error: () => {
          this.recentActivities = [];
        }
      });
  }

  loadMonthlySummary() {
    this.isLoadingChart = true;
    this.financialService.getMonthlySummary().subscribe({
      next: (data) => {
        const raw: MonthlyEntry[] = data?.results ?? (Array.isArray(data) ? data : []);
        // API returns newest-first; reverse so chart reads oldest → newest
        this.allChartData = [...raw].reverse();
        this.isLoadingChart = false;
      },
      error: () => {
        this.isLoadingChart = false;
      }
    });
  }

  onRangeChange(event: Event) {
    this.selectedRange = Number((event.target as HTMLSelectElement).value);
  }

  // ── chart helpers ──────────────────────────────────────────────────
  getMaxContribution(): number {
    const max = Math.max(...this.visibleData.map(r => r.total_deposits), 0);
    return max > 0 ? max : 1;
  }

  getBarHeightPct(value: number): number {
    const pct = (value / this.getMaxContribution()) * 100;
    // Guarantee at least 2% height so a bar is always visible
    return Math.max(pct, 2);
  }

  getMonthLabel(item: MonthlyEntry): string {
    const label = MONTH_NAMES[item.month - 1];
    const years = new Set(this.visibleData.map(d => d.year));
    return years.size > 1
      ? `${label} '${String(item.year).slice(2)}`
      : label;
  }

  // ── activity helpers ───────────────────────────────────────────────
  mapNotificationsToActivities(notifications: Notification[]): RecentActivity[] {
    return notifications.map(notification => ({
      action: notification.title,
      amount: this.extractAmountOrDetail(notification.message),
      date: notification.time_ago,
      status: this.getStatusFromNotificationType(notification.notification_type),
      icon: this.getIconFromNotificationType(notification.notification_type)
    }));
  }

  extractAmountOrDetail(message: string): string {
    const amountMatch = /KES\s*([\d,]+\.?\d*)/.exec(message);
    if (amountMatch) return `KES ${amountMatch[1]}`;
    if (message.includes('Birth Certificate')) return 'Birth Certificate';
    if (message.includes('ID Document') || message.includes('Identity')) return 'ID Document';
    if (message.includes('application')) return 'Application';
    if (message.includes('beneficiary')) return 'Beneficiary';
    if (message.includes('document')) return 'Document';
    return message.length > 30 ? message.substring(0, 30) + '...' : message;
  }

  getStatusFromNotificationType(type: string): 'success' | 'pending' | 'rejected' {
    if (type.includes('approved') || type.includes('verified') || type.includes('completed')) return 'success';
    if (type.includes('rejected') || type.includes('failed') || type.includes('deceased')) return 'rejected';
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
    for (const [key, icon] of Object.entries(iconMap)) {
      if (type.toLowerCase().includes(key)) return icon;
    }
    return iconMap['system'];
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  markNotificationAsRead(notificationId: number) {
    this.apiService.post(`notifications/${notificationId}/mark_as_read/`, {}).subscribe();
  }
}
