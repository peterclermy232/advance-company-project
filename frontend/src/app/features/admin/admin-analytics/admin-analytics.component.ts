import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HeaderComponent } from '../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../../shared/components/loading/loading.component';
import { CurrencyFormatPipe } from '../../../shared/pipes/currency-format.pipe';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { AdminAnalyticsService } from '../../../core/services/admin-analytics.service';
import { AnalyticsSummary, MemberAnalytics, MonthlyTrend } from '../../../core/models/analytics.model';


@Component({
  selector: 'app-admin-analytics',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HeaderComponent,
    SidebarComponent,
    LoadingComponent,
    CurrencyFormatPipe
  ],
  templateUrl: './admin-analytics.component.html',
  styleUrls: ['./admin-analytics.component.scss']
})
export class AdminAnalyticsComponent implements OnInit {
  private analyticsService = inject(AdminAnalyticsService);
  private authService = inject(AuthService);
  private toastService = inject(ToastService);

  // State
  sidebarOpen = true;
  isLoading = true;
  selectedView: 'overview' | 'members' | 'trends' = 'overview';
  
  // Data
  memberAnalytics: MemberAnalytics[] = [];
  summary: AnalyticsSummary | null = null;
  monthlyTrends: MonthlyTrend[] = [];
  
  // Filtering & Sorting
  searchTerm = '';
  sortBy: 'full_name' | 'total_contributions' | 'total_deposits' = 'total_contributions';
  sortOrder: 'asc' | 'desc' = 'desc';

  ngOnInit() {
    if (!this.authService.isAdmin()) {
      this.toastService.error('Access denied. Admin only.');
      return;
    }
    this.loadAnalytics();
  }

  loadAnalytics() {
    this.isLoading = true;
    
    this.analyticsService.getMemberAnalytics().subscribe({
      next: (data) => {
        this.memberAnalytics = data.members;
        this.summary = data.summary;
        this.monthlyTrends = data.monthly_trends || [];
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading analytics:', error);
        this.toastService.error('Failed to load analytics data');
        this.isLoading = false;
      }
    });
  }

  get filteredMembers(): MemberAnalytics[] {
    let filtered = this.memberAnalytics.filter(member =>
      member.full_name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
      member.email.toLowerCase().includes(this.searchTerm.toLowerCase())
    );

    return filtered.sort((a, b) => {
      const aVal = a[this.sortBy];
      const bVal = b[this.sortBy];
      
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return this.sortOrder === 'asc' 
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      
      return this.sortOrder === 'asc' 
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    });
  }

  get topContributors(): MemberAnalytics[] {
    return [...this.memberAnalytics]
      .sort((a, b) => b.total_contributions - a.total_contributions)
      .slice(0, 5);
  }

  get contributionDistribution() {
    const ranges = [
      { name: '0-100K', min: 0, max: 100000 },
      { name: '100-200K', min: 100000, max: 200000 },
      { name: '200K+', min: 200000, max: Infinity }
    ];

    return ranges.map(range => ({
      name: range.name,
      count: this.memberAnalytics.filter(m => 
        m.total_contributions >= range.min && m.total_contributions < range.max
      ).length
    }));
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  toggleSortOrder() {
    this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
  }

  exportToExcel() {
    this.analyticsService.exportAnalytics('excel').subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `member-analytics-${new Date().toISOString().split('T')[0]}.xlsx`;
        link.click();
        this.toastService.success('Excel report downloaded successfully');
      },
      error: () => {
        this.toastService.error('Failed to export to Excel');
      }
    });
  }

  exportToPDF() {
    this.analyticsService.exportAnalytics('pdf').subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `member-analytics-${new Date().toISOString().split('T')[0]}.pdf`;
        link.click();
        this.toastService.success('PDF report downloaded successfully');
      },
      error: () => {
        this.toastService.error('Failed to export to PDF');
      }
    });
  }

  getStatusClass(status: string): string {
    return status === 'Active' 
      ? 'bg-green-100 text-green-800' 
      : 'bg-gray-100 text-gray-800';
  }

  getInitials(name: string): string {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  }
}
