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

  recentActivities = [
    { action: 'Deposit Made', amount: 'KES 5,000', date: 'Today, 10:30 AM', status: 'success' },
    { action: 'Document Uploaded', amount: 'Birth Certificate', date: 'Yesterday, 3:45 PM', status: 'pending' },
    { action: 'Report Generated', amount: 'Monthly Report', date: '2 days ago', status: 'success' }
  ];

  monthlyContributions = [4200, 4800, 5100, 4500, 5300, 5000];
  months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];

  ngOnInit() {
    this.loadDashboardData();
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

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  getMaxContribution(): number {
    return Math.max(...this.monthlyContributions);
  }
}