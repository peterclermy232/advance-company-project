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
  isLoading = true;
  isGenerating = false;
  activeTab = 'financial';
  
  reports: Report[] = [];
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
    this.reportService.getReports({ report_type: this.activeTab }).subscribe({
      next: (response) => {
        this.reports = response.results;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading reports:', error);
        this.isLoading = false;
      }
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  setActiveTab(tab: string) {
    this.activeTab = tab;
    this.isLoading = true;
    this.loadReports();
  }

  generateReport() {
    this.isGenerating = true;
    const { date_from, date_to } = this.filterForm.value;

    this.reportService.generateFinancialReport(date_from, date_to).subscribe({
      next: (response) => {
        this.notificationService.success('Report generated successfully');
        this.loadReports();
        this.isGenerating = false;
      },
      error: (error) => {
        this.notificationService.error('Failed to generate report');
        this.isGenerating = false;
      }
    });
  }

  downloadReport(report: Report) {
    if (report.file_url) {
      window.open(report.file_url, '_blank');
    }
  }

  getStatusClass(status: string): string {
    const classes: { [key: string]: string } = {
      'ready': 'bg-green-100 text-green-800',
      'generating': 'bg-blue-100 text-blue-800',
      'failed': 'bg-red-100 text-red-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }
}