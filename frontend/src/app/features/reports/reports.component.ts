import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../shared/components/loading/loading.component';
import { CurrencyFormatPipe } from '../../shared/pipes/currency-format.pipe';
import { ReportService } from '../../core/services/report.service';
import { NotificationService } from '../../core/services/notification.service';
import { Report } from '../../core/models/report.model';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    HeaderComponent,
    SidebarComponent,
    LoadingComponent,
    CurrencyFormatPipe
  ],
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.scss']
})
export class ReportsComponent implements OnInit {
  private fb = inject(FormBuilder);
  private reportService = inject(ReportService);
  private notificationService = inject(NotificationService);

  sidebarOpen = true;
  isLoading = false;
  isGenerating = false;
  activeTab = 'FINANCIAL';
  
  reports: Report[] = [];
  reportData: any = null;
  filterForm: FormGroup;

  constructor() {
    this.filterForm = this.fb.group({
      date_from: [''],
      date_to: ['']
    });
  }

  ngOnInit() {
    this.loadReports();
  }

  loadReports() {
    this.isLoading = true;
    
    this.reportService.getReports({ report_type: this.activeTab.toUpperCase() }).subscribe({
      next: (response) => {
        // Handle both paginated and non-paginated responses
        let allReports: Report[] = [];
        if (response && response.results) {
          allReports = response.results;
        } else if (Array.isArray(response)) {
          allReports = response;
        }
        
        // Filter reports by active tab (client-side filtering as backup)
        this.reports = allReports.filter(report => report.report_type === this.activeTab);
        
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading reports:', error);
        this.reports = [];
        this.isLoading = false;
        this.notificationService.error('Failed to load reports');
      }
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  setActiveTab(tab: string) {
    this.activeTab = tab.toLowerCase();
    this.reportData = null;
    this.loadReports();
  }

  generateReport() {
    this.isGenerating = true;
    const { date_from, date_to } = this.filterForm.value;

    const dateFrom = date_from || undefined;
    const dateTo = date_to || undefined;

    let reportObservable;
    
    switch (this.activeTab.toUpperCase()) {
      case 'FINANCIAL':
        reportObservable = this.reportService.generateFinancialReport(dateFrom, dateTo);
        break;
      case 'COMPENSATORY':
        reportObservable = this.reportService.generateCompensatoryReport(dateFrom, dateTo);
        break;
      case 'ACTIVITY':
        reportObservable = this.reportService.generateActivityReport(dateFrom, dateTo);
        break;
      default:
        reportObservable = this.reportService.generateFinancialReport(dateFrom, dateTo);
    }

    reportObservable.subscribe({
      next: (response) => {
        this.reportData = response;
        this.notificationService.success('Report generated successfully');
        
        // Reload reports after generation
        setTimeout(() => {
          this.loadReports();
        }, 1000);
        
        this.isGenerating = false;
      },
      error: (error) => {
        console.error('Error generating report:', error);
        this.notificationService.error('Failed to generate report');
        this.isGenerating = false;
      }
    });
  }

  downloadReport(report: Report) {
    if (report.file_url) {
      // Open the Cloudinary URL in a new tab
      window.open(report.file_url, '_blank');
    } else {
      this.notificationService.error('Download URL not available for this report');
    }
  }

  // Check if download is available
  canDownload(report: Report): boolean {
    return report.status === 'ready' && !!report.file_url;
  }

  getStatusClass(status: string): string {
    const classes: { [key: string]: string } = {
      'ready': 'bg-green-100 text-green-800',
      'generating': 'bg-blue-100 text-blue-800',
      'failed': 'bg-red-100 text-red-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  getTabDisplayName(): string {
    switch (this.activeTab.toUpperCase()) {
      case 'FINANCIAL':
        return 'FINANCIAL';
      case 'COMPENSATORY':
        return 'COMPENSATORY';
      case 'ACTIVITY':
        return 'ACTIVITY';
      default:
        return '';
    }
  }
}