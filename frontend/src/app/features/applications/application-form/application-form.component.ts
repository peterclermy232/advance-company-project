import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HeaderComponent } from '../../../shared/components/header/header.component';
import { SidebarComponent } from '../../../shared/components/sidebar/sidebar.component';
import { ApplicationService } from '../../../core/services/application.service';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-application-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule, HeaderComponent, SidebarComponent],
  templateUrl: './application-form.component.html',
  styleUrls: ['./application-form.component.scss']
})
export class ApplicationFormComponent {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private applicationService = inject(ApplicationService);
  private authService = inject(AuthService);
  private notificationService = inject(NotificationService);

  sidebarOpen = true;
  isSubmitting = false;
  applicationForm: FormGroup;
  selectedFile: File | null = null;
  currentUser = this.authService.getCurrentUser();

  constructor() {
    this.applicationForm = this.fb.group({
      application_type: ['', Validators.required],
      reason: ['', [Validators.required, Validators.minLength(20)]]
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile = file;
    }
  }

  onSubmit() {
    if (this.applicationForm.valid) {
      this.isSubmitting = true;
      const formData = new FormData();
      
      formData.append('application_type', this.applicationForm.value.application_type);
      formData.append('reason', this.applicationForm.value.reason);
      
      if (this.selectedFile) {
        formData.append('supporting_document', this.selectedFile);
      }

      this.applicationService.createApplication(formData).subscribe({
        next: () => {
          this.notificationService.success('Application submitted successfully');
          this.router.navigate(['/applications']);
        },
        error: (error) => {
          this.notificationService.error('Failed to submit application');
          this.isSubmitting = false;
        }
      });
    }
  }
}
