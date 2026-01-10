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

// Import Chart.js
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

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

  // Charts
  private monthlyTrendsChart: Chart | null = null;
  private contributionDistributionChart: Chart | null = null;
  private interestComparisonChart: Chart | null = null;
  private growthTimelineChart: Chart | null = null;

  // State
  sidebarOpen = true;
  isLoading = true;
  selectedView: 'overview' | 'members' | 'trends' = 'overview';
  
  // Data
  memberAnalytics: any[] = [];
  summary: any = null;
  monthlyTrends: any[] = [];
  
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
        
        // Initialize charts after data is loaded
        setTimeout(() => this.initializeCharts(), 100);
      },
      error: (error) => {
        console.error('Error loading analytics:', error);
        this.toastService.error('Failed to load analytics data');
        this.isLoading = false;
      }
    });
  }

  initializeCharts() {
    this.createMonthlyTrendsChart();
    this.createContributionDistributionChart();
    this.createInterestComparisonChart();
    this.createGrowthTimelineChart();
  }

  createMonthlyTrendsChart() {
    const canvas = document.getElementById('monthlyTrendsChart') as HTMLCanvasElement;
    if (!canvas) return;

    if (this.monthlyTrendsChart) {
      this.monthlyTrendsChart.destroy();
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    this.monthlyTrendsChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: this.monthlyTrends.map(t => `${t.month} ${t.year}`),
        datasets: [
          {
            label: 'Total Contributions',
            data: this.monthlyTrends.map(t => t.total_amount),
            borderColor: '#3B82F6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4,
            fill: true
          },
          {
            label: 'Number of Deposits',
            data: this.monthlyTrends.map(t => t.deposit_count),
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.4,
            fill: true,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            position: 'top',
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                const value = context.parsed.y;
                if (value === null) return label;
                
                if (context.datasetIndex === 0) {
                  label += 'KES ' + value.toLocaleString();
                } else {
                  label += value + ' deposits';
                }
                return label;
              }
            }
          }
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: 'Amount (KES)'
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              display: true,
              text: 'Number of Deposits'
            },
            grid: {
              drawOnChartArea: false,
            },
          },
        }
      }
    });
  }

  createContributionDistributionChart() {
    const canvas = document.getElementById('contributionDistributionChart') as HTMLCanvasElement;
    if (!canvas) return;

    if (this.contributionDistributionChart) {
      this.contributionDistributionChart.destroy();
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const distribution = this.contributionDistribution;

    this.contributionDistributionChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: distribution.map(d => d.name),
        datasets: [{
          data: distribution.map(d => d.count),
          backgroundColor: [
            '#3B82F6',
            '#10B981',
            '#F59E0B',
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || '';
                const value = context.parsed;
                if (value === null) return label;
                
                const total = distribution.reduce((sum, d) => sum + d.count, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${label}: ${value} members (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  }

  createInterestComparisonChart() {
    const canvas = document.getElementById('interestComparisonChart') as HTMLCanvasElement;
    if (!canvas) return;

    if (this.interestComparisonChart) {
      this.interestComparisonChart.destroy();
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const topMembers = this.topContributors;

    this.interestComparisonChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: topMembers.map(m => m.full_name.split(' ')[0]),
        datasets: [
          {
            label: 'Contributions',
            data: topMembers.map(m => m.total_contributions),
            backgroundColor: '#3B82F6',
          },
          {
            label: 'Interest Earned',
            data: topMembers.map(m => m.interest_earned),
            backgroundColor: '#10B981',
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.parsed.y;
                if (value === null) return '';
                return context.dataset.label + ': KES ' + value.toLocaleString();
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Amount (KES)'
            }
          }
        }
      }
    });
  }

  createGrowthTimelineChart() {
    const canvas = document.getElementById('growthTimelineChart') as HTMLCanvasElement;
    if (!canvas) return;

    if (this.growthTimelineChart) {
      this.growthTimelineChart.destroy();
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Calculate cumulative data
    let cumulative = 0;
    const cumulativeData = this.monthlyTrends.map(t => {
      cumulative += t.total_amount;
      return cumulative;
    });

    this.growthTimelineChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: this.monthlyTrends.map(t => `${t.month} ${t.year}`),
        datasets: [{
          label: 'Cumulative Contributions',
          data: cumulativeData,
          borderColor: '#8B5CF6',
          backgroundColor: 'rgba(139, 92, 246, 0.2)',
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.parsed.y;
                if (value === null) return '';
                return 'Total: KES ' + value.toLocaleString();
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Cumulative Amount (KES)'
            }
          }
        }
      }
    });
  }

  get filteredMembers(): any[] {
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

  get topContributors(): any[] {
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
    this.toastService.info('Preparing Excel export...');
    
    this.analyticsService.exportAnalytics('excel').subscribe({
      next: (blob) => {
        if (blob.size === 0) {
          this.toastService.error('Export failed: Empty file received');
          return;
        }
        
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `member-analytics-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        this.toastService.success('Excel report downloaded successfully');
      },
      error: (error) => {
        console.error('Excel export error:', error);
        this.toastService.error('Failed to export to Excel: ' + (error.message || 'Unknown error'));
      }
    });
  }

  exportToPDF() {
    this.toastService.info('Preparing PDF export...');
    
    this.analyticsService.exportAnalytics('pdf').subscribe({
      next: (blob) => {
        if (blob.size === 0) {
          this.toastService.error('Export failed: Empty file received');
          return;
        }
        
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `member-analytics-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        this.toastService.success('PDF report downloaded successfully');
      },
      error: (error) => {
        console.error('PDF export error:', error);
        this.toastService.error('Failed to export to PDF: ' + (error.message || 'Unknown error'));
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

  ngOnDestroy() {
    // Cleanup charts
    if (this.monthlyTrendsChart) this.monthlyTrendsChart.destroy();
    if (this.contributionDistributionChart) this.contributionDistributionChart.destroy();
    if (this.interestComparisonChart) this.interestComparisonChart.destroy();
    if (this.growthTimelineChart) this.growthTimelineChart.destroy();
  }
}