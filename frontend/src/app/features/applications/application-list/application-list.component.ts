import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HeaderComponent } from '../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../shared/components/sidebar/sidebar.component';
import { LoadingComponent } from '../../../shared/components/loading/loading.component';
import { ApplicationService } from '../../../core/services/application.service';
import { NotificationService } from '../../../core/services/notification.service';
import { AuthService } from '../../../core/services/auth.service';
import { Application } from '../../../core/models/application.model';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-application-list',
  standalone: true,
  imports: [CommonModule, RouterModule, HeaderComponent, SidebarComponent, LoadingComponent, FormsModule],
  templateUrl: './application-list.component.html',
  styleUrls: ['./application-list.component.scss']
})
export class ApplicationListComponent implements OnInit {
  private applicationService = inject(ApplicationService);
  private notificationService = inject(NotificationService);
  private authService = inject(AuthService);

  sidebarOpen = true;
  isLoading = true;
  applications: Application[] = [];
  selectedApplication: Application | null = null;
  showActionModal = false;
  actionType: 'approve' | 'reject' | null = null;
  actionComments = '';

  ngOnInit() {
    this.loadApplications();
  }

  loadApplications() {
    this.applicationService.getApplications().subscribe({
      next: (response) => {
        this.applications = response.results;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading applications:', error);
        this.isLoading = false;
      }
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  openActionModal(application: Application, action: 'approve' | 'reject') {
    this.selectedApplication = application;
    this.actionType = action;
    this.showActionModal = true;
    this.actionComments = '';
  }

  closeActionModal() {
    this.showActionModal = false;
    this.selectedApplication = null;
    this.actionType = null;
    this.actionComments = '';
  }

  performAction() {
    if (!this.selectedApplication || !this.actionType) return;

    const action = this.actionType === 'approve'
      ? this.applicationService.approveApplication(this.selectedApplication.id, this.actionComments)
      : this.applicationService.rejectApplication(this.selectedApplication.id, this.actionComments);

    action.subscribe({
      next: () => {
        this.notificationService.success(`Application ${this.actionType}d successfully`);
        this.loadApplications();
        this.closeActionModal();
      },
      error: (error) => {
        this.notificationService.error(`Failed to ${this.actionType} application`);
      }
    });
  }

  getStatusClass(status: string): string {
    const classes: { [key: string]: string } = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'under_review': 'bg-blue-100 text-blue-800',
      'approved': 'bg-green-100 text-green-800',
      'rejected': 'bg-red-100 text-red-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  isAdmin(): boolean {
    return this.authService.isAdmin();
  }
}
